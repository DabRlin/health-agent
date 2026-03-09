"""
健康数据服务
"""
from datetime import datetime, timedelta
from typing import Optional, List
from database import SessionLocal, User, HealthRecord, HealthMetric, UserHealthProfile
from sqlalchemy import desc, func, and_
from config import config


class HealthService:
    """健康数据服务类"""
    
    @classmethod
    def get_metrics(cls, user_id: Optional[int] = None) -> List[dict]:
        """获取最新健康指标"""
        db = SessionLocal()
        try:
            user = cls._get_user(db, user_id)
            if not user:
                return []

            # 子查询：每种 metric_type 的最新 recorded_at
            latest_sub = db.query(
                HealthMetric.metric_type,
                func.max(HealthMetric.recorded_at).label('max_time')
            ).filter(
                HealthMetric.user_id == user.id
            ).group_by(HealthMetric.metric_type).subquery()

            # 主查询：一次获取所有最新指标
            latest_metrics = db.query(HealthMetric).join(
                latest_sub, and_(
                    HealthMetric.metric_type == latest_sub.c.metric_type,
                    HealthMetric.recorded_at == latest_sub.c.max_time
                )
            ).filter(HealthMetric.user_id == user.id).all()

            latest_map = {m.metric_type: m for m in latest_metrics}

            # 批量获取趋势：每种类型取最新 2 条
            trends = cls._calculate_trends_batch(db, user.id, list(latest_map.keys()))

            metrics = []
            for metric_type, cfg in config.METRIC_CONFIG.items():
                m = latest_map.get(metric_type)
                if m:
                    metrics.append({
                        "id": m.id,
                        "name": cfg['name'],
                        "value": m.value,
                        "unit": cfg['unit'],
                        "icon": cfg['icon'],
                        "color": cfg['color'],
                        "status": m.status,
                        "normal_range": cfg['normal_range'],
                        "trend": trends.get(metric_type, 'stable'),
                        "updated_at": m.recorded_at.isoformat()
                    })

            return metrics
        finally:
            db.close()
    
    _KEY_MAP = {
        'blood_pressure_sys': 'systolic',
        'blood_pressure_dia': 'diastolic',
    }

    @classmethod
    def get_metrics_trend(cls, user_id: Optional[int] = None, days: int = 30) -> List[dict]:
        """获取健康指标趋势"""
        db = SessionLocal()
        try:
            user = cls._get_user(db, user_id)
            if not user:
                return []

            start_date = datetime.now() - timedelta(days=days)
            trend_types = ['heart_rate', 'blood_pressure_sys', 'blood_pressure_dia', 'blood_sugar']

            # 一次查询所有数据
            rows = db.query(HealthMetric).filter(
                HealthMetric.user_id == user.id,
                HealthMetric.metric_type.in_(trend_types),
                HealthMetric.recorded_at >= start_date
            ).order_by(HealthMetric.recorded_at).all()

            # 按日期分组
            day_map: dict = {}
            for m in rows:
                date_str = m.recorded_at.strftime("%Y-%m-%d")
                if date_str not in day_map:
                    day_map[date_str] = {"date": date_str}
                key = cls._KEY_MAP.get(m.metric_type, m.metric_type)
                day_map[date_str][key] = m.value

            return [v for v in day_map.values() if len(v) > 1]
        finally:
            db.close()
    
    @classmethod
    def add_metric(cls, user_id: Optional[int], metric_type: str, value: float) -> Optional[dict]:
        """添加健康指标（每日唯一制：当日已有记录则更新，否则新增）"""
        cfg = config.METRIC_CONFIG.get(metric_type)
        if not cfg:
            return None
        
        db = SessionLocal()
        try:
            user = cls._get_user(db, user_id)
            if not user:
                return None
            
            # 判断状态
            status = 'normal' if cfg['min'] <= value <= cfg['max'] else 'warning'

            # 查找当日是否已有同类型记录
            today = datetime.now().date()
            existing = db.query(HealthMetric).filter(
                HealthMetric.user_id == user.id,
                HealthMetric.metric_type == metric_type,
                func.date(HealthMetric.recorded_at) == today
            ).first()

            if existing:
                existing.value = value
                existing.unit = cfg['unit']
                existing.status = status
                existing.recorded_at = datetime.now()
                metric = existing
            else:
                metric = HealthMetric(
                    user_id=user.id,
                    metric_type=metric_type,
                    value=value,
                    unit=cfg['unit'],
                    status=status
                )
                db.add(metric)

            db.commit()

            # 同步更新 UserHealthProfile 基线字段
            cls._sync_health_profile(db, user.id, metric_type, value)

            return {
                "id": metric.id,
                "name": cfg['name'],
                "value": metric.value,
                "unit": metric.unit,
                "status": metric.status,
                "recorded_at": metric.recorded_at.isoformat()
            }
        finally:
            db.close()

    # HealthMetric → UserHealthProfile 字段映射
    _PROFILE_SYNC_MAP = {
        'blood_pressure_sys': 'systolic_bp',
        'blood_pressure_dia': 'diastolic_bp',
        'blood_sugar':        'fasting_glucose',
        'bmi':                'bmi',
    }

    @classmethod
    def _sync_health_profile(cls, db, user_id: int, metric_type: str, value: float) -> None:
        """将新录入的指标同步到 UserHealthProfile 基线字段"""
        profile_field = cls._PROFILE_SYNC_MAP.get(metric_type)
        if not profile_field:
            return

        profile = db.query(UserHealthProfile).filter(
            UserHealthProfile.user_id == user_id
        ).first()
        if not profile:
            profile = UserHealthProfile(user_id=user_id)
            db.add(profile)

        setattr(profile, profile_field, value)

        # BMI 录入时同步 weight（若身高已知则反算体重，否则仅更新 bmi）
        if metric_type == 'bmi' and profile.height and profile.height > 0:
            profile.weight = round(value * ((profile.height / 100) ** 2), 1)

        db.commit()
    
    @classmethod
    def get_records(cls, user_id: Optional[int] = None, limit: int = 20) -> List[dict]:
        """获取健康记录"""
        db = SessionLocal()
        try:
            user = cls._get_user(db, user_id)
            if not user:
                return []
            
            records = db.query(HealthRecord).filter(
                HealthRecord.user_id == user.id
            ).order_by(desc(HealthRecord.record_date)).limit(limit).all()
            
            return [{
                "id": r.id,
                "date": r.record_date.strftime("%Y-%m-%d"),
                "type": r.record_type,
                "source": r.source,
                "status": r.status,
                "risk": r.risk_level
            } for r in records]
        finally:
            db.close()
    
    @classmethod
    def add_record(cls, user_id: Optional[int], record_type: str, source: str = "手动录入") -> Optional[dict]:
        """添加健康记录"""
        db = SessionLocal()
        try:
            user = cls._get_user(db, user_id)
            if not user:
                return None
            
            record = HealthRecord(
                user_id=user.id,
                record_type=record_type,
                source=source,
                status="已记录",
                risk_level="low"
            )
            db.add(record)
            db.commit()
            
            return {
                "id": record.id,
                "date": record.record_date.strftime("%Y-%m-%d"),
                "type": record.record_type,
                "source": record.source,
                "status": record.status,
                "risk": record.risk_level
            }
        finally:
            db.close()
    
    @classmethod
    def _get_user(cls, db, user_id: Optional[int] = None) -> Optional[User]:
        """获取用户"""
        if user_id:
            return db.query(User).filter(User.id == user_id).first()
        return db.query(User).first()
    
    @classmethod
    def _calculate_trends_batch(cls, db, user_id: int, metric_types: List[str]) -> dict:
        """批量计算多种指标的趋势（单次查询）"""
        if not metric_types:
            return {}

        # 每种类型取最新 2 条，使用窗口函数思路但 SQLite 兼容写法
        all_records = db.query(HealthMetric).filter(
            HealthMetric.user_id == user_id,
            HealthMetric.metric_type.in_(metric_types)
        ).order_by(HealthMetric.metric_type, desc(HealthMetric.recorded_at)).all()

        # 按类型分组，取前 2
        grouped: dict = {}
        for m in all_records:
            lst = grouped.setdefault(m.metric_type, [])
            if len(lst) < 2:
                lst.append(m.value)

        trends = {}
        for mt, vals in grouped.items():
            if len(vals) < 2:
                trends[mt] = 'stable'
            else:
                diff = vals[0] - vals[1]
                trends[mt] = 'stable' if abs(diff) < 0.5 else ('up' if diff > 0 else 'down')
        return trends
