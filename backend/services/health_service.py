"""
健康数据服务
"""
from datetime import datetime, timedelta
from typing import Optional, List
import random
from database import SessionLocal, User, HealthRecord, HealthMetric
from sqlalchemy import desc, func
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
            
            metrics = []
            for metric_type, cfg in config.METRIC_CONFIG.items():
                latest = db.query(HealthMetric).filter(
                    HealthMetric.user_id == user.id,
                    HealthMetric.metric_type == metric_type
                ).order_by(desc(HealthMetric.recorded_at)).first()
                
                if latest:
                    metrics.append({
                        "id": latest.id,
                        "name": cfg['name'],
                        "value": latest.value,
                        "unit": cfg['unit'],
                        "icon": cfg['icon'],
                        "color": cfg['color'],
                        "status": latest.status,
                        "normal_range": cfg['normal_range'],
                        "trend": cls._calculate_trend(db, user.id, metric_type),
                        "updated_at": latest.recorded_at.isoformat()
                    })
            
            return metrics
        finally:
            db.close()
    
    @classmethod
    def get_metrics_trend(cls, user_id: Optional[int] = None, days: int = 30) -> List[dict]:
        """获取健康指标趋势"""
        db = SessionLocal()
        try:
            user = cls._get_user(db, user_id)
            if not user:
                return []
            
            data = []
            for i in range(days, 0, -1):
                date = datetime.now() - timedelta(days=i)
                date_str = date.strftime("%Y-%m-%d")
                
                day_data = {"date": date_str}
                
                for metric_type in ['heart_rate', 'blood_pressure_sys', 'blood_pressure_dia', 'blood_sugar']:
                    metric = db.query(HealthMetric).filter(
                        HealthMetric.user_id == user.id,
                        HealthMetric.metric_type == metric_type,
                        func.date(HealthMetric.recorded_at) == date.date()
                    ).first()
                    
                    if metric:
                        key = metric_type.replace('blood_pressure_sys', 'systolic').replace('blood_pressure_dia', 'diastolic')
                        day_data[key] = metric.value
                
                if len(day_data) > 1:
                    data.append(day_data)
            
            return data
        finally:
            db.close()
    
    @classmethod
    def add_metric(cls, user_id: Optional[int], metric_type: str, value: float) -> Optional[dict]:
        """添加健康指标"""
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
            
            metric = HealthMetric(
                user_id=user.id,
                metric_type=metric_type,
                value=value,
                unit=cfg['unit'],
                status=status
            )
            db.add(metric)
            db.commit()
            
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
    def _calculate_trend(cls, db, user_id: int, metric_type: str) -> str:
        """计算指标趋势"""
        # 获取最近两条记录
        records = db.query(HealthMetric).filter(
            HealthMetric.user_id == user_id,
            HealthMetric.metric_type == metric_type
        ).order_by(desc(HealthMetric.recorded_at)).limit(2).all()
        
        if len(records) < 2:
            return "stable"
        
        diff = records[0].value - records[1].value
        if abs(diff) < 0.5:
            return "stable"
        return "up" if diff > 0 else "down"
