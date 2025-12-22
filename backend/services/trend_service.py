"""
健康趋势分析服务
整合趋势预测、异常检测和健康评分功能
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from database import (
    SessionLocal, User, HealthMetric, 
    DeviceReading, DailyHealthSummary, UserHealthProfile
)
from sqlalchemy import func, desc
from services.ml_models import (
    analyze_health_trend,
    detect_anomalies,
    calculate_health_score,
    TrendAnalyzer,
    AnomalyDetector
)


class TrendService:
    """健康趋势分析服务"""
    
    @classmethod
    def get_metric_trend(cls, user_id: int, metric_type: str, 
                         days: int = 30) -> Dict:
        """
        获取指定指标的趋势分析
        
        Args:
            user_id: 用户ID
            metric_type: 指标类型
            days: 分析天数
            
        Returns:
            {
                'data': list,           # 历史数据
                'dates': list,          # 日期列表
                'trend': dict,          # 趋势分析结果
                'anomalies': dict,      # 异常检测结果
                'prediction': list,     # 预测数据
                'statistics': dict      # 统计信息
            }
        """
        db = SessionLocal()
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            # 从 HealthMetric 获取数据
            metrics = db.query(HealthMetric).filter(
                HealthMetric.user_id == user_id,
                HealthMetric.metric_type == metric_type,
                HealthMetric.recorded_at >= start_date
            ).order_by(HealthMetric.recorded_at).all()
            
            if not metrics:
                return cls._empty_result()
            
            # 提取数据
            data = [m.value for m in metrics]
            dates = [m.recorded_at.strftime("%Y-%m-%d") for m in metrics]
            
            # 趋势分析
            trend = analyze_health_trend(data, metric_type)
            
            # 异常检测
            anomalies = detect_anomalies(data, metric_type, dates)
            
            # 统计信息
            statistics = cls._calculate_statistics(data)
            
            # 构建预测数据（包含历史+预测）
            prediction_dates = []
            last_date = metrics[-1].recorded_at
            for i in range(1, 8):
                pred_date = last_date + timedelta(days=i)
                prediction_dates.append(pred_date.strftime("%Y-%m-%d"))
            
            return {
                'data': data,
                'dates': dates,
                'trend': trend,
                'anomalies': anomalies,
                'prediction': {
                    'values': trend['prediction'],
                    'dates': prediction_dates
                },
                'statistics': statistics
            }
        finally:
            db.close()
    
    @classmethod
    def get_device_data_trend(cls, user_id: int, metric_type: str,
                               days: int = 7) -> Dict:
        """
        获取穿戴设备数据趋势（高频数据）
        
        Args:
            user_id: 用户ID
            metric_type: heart_rate, spo2, steps 等
            days: 分析天数
        """
        db = SessionLocal()
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            # 按日聚合设备数据
            daily_data = db.query(
                func.date(DeviceReading.recorded_at).label('date'),
                func.avg(DeviceReading.value).label('avg_value'),
                func.min(DeviceReading.value).label('min_value'),
                func.max(DeviceReading.value).label('max_value'),
                func.count(DeviceReading.id).label('count')
            ).filter(
                DeviceReading.user_id == user_id,
                DeviceReading.metric_type == metric_type,
                DeviceReading.recorded_at >= start_date
            ).group_by(
                func.date(DeviceReading.recorded_at)
            ).order_by('date').all()
            
            if not daily_data:
                return cls._empty_result()
            
            # 提取数据
            data = [round(d.avg_value, 1) for d in daily_data]
            dates = [str(d.date) for d in daily_data]
            
            # 趋势分析
            trend = analyze_health_trend(data, metric_type)
            
            # 异常检测
            anomalies = detect_anomalies(data, metric_type, dates)
            
            # 详细统计
            statistics = {
                'avg': round(sum(data) / len(data), 1),
                'min': min(data),
                'max': max(data),
                'daily_details': [{
                    'date': str(d.date),
                    'avg': round(d.avg_value, 1),
                    'min': round(d.min_value, 1),
                    'max': round(d.max_value, 1),
                    'readings': d.count
                } for d in daily_data]
            }
            
            return {
                'data': data,
                'dates': dates,
                'trend': trend,
                'anomalies': anomalies,
                'prediction': {
                    'values': trend['prediction'],
                    'dates': cls._get_future_dates(dates[-1] if dates else None, 7)
                },
                'statistics': statistics
            }
        finally:
            db.close()
    
    @classmethod
    def get_sleep_trend(cls, user_id: int, days: int = 14) -> Dict:
        """获取睡眠趋势分析"""
        db = SessionLocal()
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            
            summaries = db.query(DailyHealthSummary).filter(
                DailyHealthSummary.user_id == user_id,
                DailyHealthSummary.date >= start_date
            ).order_by(DailyHealthSummary.date).all()
            
            if not summaries:
                return cls._empty_result()
            
            # 提取睡眠数据
            dates = [s.date for s in summaries]
            duration_data = [s.sleep_duration or 0 for s in summaries]
            quality_data = [s.sleep_quality_score or 0 for s in summaries]
            deep_sleep_data = [s.deep_sleep_duration or 0 for s in summaries]
            
            # 分析各维度趋势
            duration_trend = analyze_health_trend(duration_data, 'sleep_duration')
            quality_trend = analyze_health_trend(quality_data, 'sleep_quality')
            
            # 睡眠异常检测
            anomalies = []
            for i, s in enumerate(summaries):
                if s.sleep_duration and s.sleep_duration < 5:
                    anomalies.append({
                        'date': s.date,
                        'type': 'short_sleep',
                        'value': s.sleep_duration,
                        'message': f'睡眠时间过短 ({s.sleep_duration:.1f}小时)'
                    })
                if s.awake_count and s.awake_count > 5:
                    anomalies.append({
                        'date': s.date,
                        'type': 'frequent_wake',
                        'value': s.awake_count,
                        'message': f'夜间觉醒次数过多 ({s.awake_count}次)'
                    })
            
            # 统计
            avg_duration = sum(duration_data) / len(duration_data) if duration_data else 0
            avg_quality = sum(quality_data) / len(quality_data) if quality_data else 0
            avg_deep = sum(deep_sleep_data) / len(deep_sleep_data) if deep_sleep_data else 0
            
            return {
                'dates': dates,
                'duration': {
                    'data': duration_data,
                    'trend': duration_trend,
                    'avg': round(avg_duration, 1)
                },
                'quality': {
                    'data': quality_data,
                    'trend': quality_trend,
                    'avg': round(avg_quality)
                },
                'deep_sleep': {
                    'data': deep_sleep_data,
                    'avg': round(avg_deep, 1),
                    'ratio': round(avg_deep / avg_duration * 100, 1) if avg_duration > 0 else 0
                },
                'anomalies': anomalies,
                'summary': cls._generate_sleep_summary(avg_duration, avg_quality, anomalies)
            }
        finally:
            db.close()
    
    @classmethod
    def get_activity_trend(cls, user_id: int, days: int = 14) -> Dict:
        """获取活动量趋势分析"""
        db = SessionLocal()
        try:
            start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            
            summaries = db.query(DailyHealthSummary).filter(
                DailyHealthSummary.user_id == user_id,
                DailyHealthSummary.date >= start_date
            ).order_by(DailyHealthSummary.date).all()
            
            if not summaries:
                return cls._empty_result()
            
            dates = [s.date for s in summaries]
            steps_data = [s.total_steps or 0 for s in summaries]
            calories_data = [s.calories_burned or 0 for s in summaries]
            active_minutes_data = [s.active_minutes or 0 for s in summaries]
            
            # 趋势分析
            steps_trend = analyze_health_trend(steps_data, 'steps')
            
            # 目标达成分析 (假设目标8000步)
            goal = 8000
            days_reached = sum(1 for s in steps_data if s >= goal)
            reach_rate = days_reached / len(steps_data) * 100 if steps_data else 0
            
            # 统计
            avg_steps = sum(steps_data) / len(steps_data) if steps_data else 0
            avg_calories = sum(calories_data) / len(calories_data) if calories_data else 0
            avg_active = sum(active_minutes_data) / len(active_minutes_data) if active_minutes_data else 0
            
            return {
                'dates': dates,
                'steps': {
                    'data': steps_data,
                    'trend': steps_trend,
                    'avg': round(avg_steps),
                    'max': max(steps_data) if steps_data else 0,
                    'goal': goal,
                    'reach_rate': round(reach_rate, 1)
                },
                'calories': {
                    'data': calories_data,
                    'avg': round(avg_calories)
                },
                'active_minutes': {
                    'data': active_minutes_data,
                    'avg': round(avg_active)
                },
                'summary': cls._generate_activity_summary(avg_steps, reach_rate, steps_trend)
            }
        finally:
            db.close()
    
    @classmethod
    def get_health_score(cls, user_id: int) -> Dict:
        """
        计算用户综合健康评分
        
        整合最新的各项健康指标计算综合评分
        """
        db = SessionLocal()
        try:
            # 获取最新的每日汇总
            latest_summary = db.query(DailyHealthSummary).filter(
                DailyHealthSummary.user_id == user_id
            ).order_by(desc(DailyHealthSummary.date)).first()
            
            # 获取最新的健康指标
            metrics = {}
            
            for metric_type in ['heart_rate', 'blood_pressure_sys', 'blood_pressure_dia', 'blood_sugar']:
                latest = db.query(HealthMetric).filter(
                    HealthMetric.user_id == user_id,
                    HealthMetric.metric_type == metric_type
                ).order_by(desc(HealthMetric.recorded_at)).first()
                
                if latest:
                    metrics[metric_type] = latest.value
            
            # 从每日汇总补充数据
            if latest_summary:
                if latest_summary.avg_heart_rate and 'heart_rate' not in metrics:
                    metrics['heart_rate'] = latest_summary.avg_heart_rate
                if latest_summary.total_steps:
                    metrics['steps'] = latest_summary.total_steps
                if latest_summary.sleep_duration:
                    metrics['sleep_duration'] = latest_summary.sleep_duration
                if latest_summary.avg_spo2:
                    metrics['spo2'] = latest_summary.avg_spo2
            
            # 获取BMI
            profile = db.query(UserHealthProfile).filter(
                UserHealthProfile.user_id == user_id
            ).first()
            
            if profile and profile.bmi:
                metrics['bmi'] = profile.bmi
            
            # 计算健康评分
            if not metrics:
                return {
                    'overall_score': 70,
                    'category_scores': {},
                    'level': 'unknown',
                    'summary': '数据不足，无法计算准确评分',
                    'metrics_used': []
                }
            
            result = calculate_health_score(metrics)
            result['metrics_used'] = list(metrics.keys())
            
            return result
        finally:
            db.close()
    
    @classmethod
    def get_comprehensive_analysis(cls, user_id: int) -> Dict:
        """
        获取综合健康分析报告
        
        整合所有趋势分析、异常检测和健康评分
        """
        db = SessionLocal()
        try:
            # 健康评分
            health_score = cls.get_health_score(user_id)
            
            # 各项趋势
            heart_rate_trend = cls.get_device_data_trend(user_id, 'heart_rate', 7)
            
            # 睡眠趋势
            sleep_trend = cls.get_sleep_trend(user_id, 7)
            
            # 活动趋势
            activity_trend = cls.get_activity_trend(user_id, 7)
            
            # 收集所有异常
            all_anomalies = []
            
            if heart_rate_trend.get('anomalies', {}).get('anomalies'):
                for a in heart_rate_trend['anomalies']['anomalies']:
                    a['metric'] = '心率'
                    all_anomalies.append(a)
            
            if sleep_trend.get('anomalies'):
                for a in sleep_trend['anomalies']:
                    a['metric'] = '睡眠'
                    all_anomalies.append(a)
            
            # 生成综合建议
            recommendations = cls._generate_comprehensive_recommendations(
                health_score, heart_rate_trend, sleep_trend, activity_trend
            )
            
            return {
                'health_score': health_score,
                'trends': {
                    'heart_rate': {
                        'direction': heart_rate_trend.get('trend', {}).get('direction', 'unknown'),
                        'analysis': heart_rate_trend.get('trend', {}).get('analysis', '')
                    },
                    'sleep': {
                        'avg_duration': sleep_trend.get('duration', {}).get('avg', 0),
                        'avg_quality': sleep_trend.get('quality', {}).get('avg', 0),
                        'summary': sleep_trend.get('summary', '')
                    },
                    'activity': {
                        'avg_steps': activity_trend.get('steps', {}).get('avg', 0),
                        'reach_rate': activity_trend.get('steps', {}).get('reach_rate', 0),
                        'summary': activity_trend.get('summary', '')
                    }
                },
                'anomalies': all_anomalies[:10],  # 最多显示10条
                'anomaly_count': len(all_anomalies),
                'recommendations': recommendations,
                'generated_at': datetime.now().isoformat()
            }
        finally:
            db.close()
    
    @classmethod
    def _empty_result(cls) -> Dict:
        """返回空结果"""
        return {
            'data': [],
            'dates': [],
            'trend': {'direction': 'unknown', 'analysis': '暂无数据'},
            'anomalies': {'has_anomaly': False, 'anomalies': []},
            'prediction': {'values': [], 'dates': []},
            'statistics': {}
        }
    
    @classmethod
    def _calculate_statistics(cls, data: List[float]) -> Dict:
        """计算统计信息"""
        if not data:
            return {}
        
        sorted_data = sorted(data)
        n = len(data)
        
        return {
            'count': n,
            'avg': round(sum(data) / n, 1),
            'min': round(min(data), 1),
            'max': round(max(data), 1),
            'median': round(sorted_data[n // 2], 1),
            'std': round(cls._calculate_std(data), 2)
        }
    
    @classmethod
    def _calculate_std(cls, data: List[float]) -> float:
        """计算标准差"""
        if len(data) < 2:
            return 0
        mean = sum(data) / len(data)
        variance = sum((x - mean) ** 2 for x in data) / len(data)
        return variance ** 0.5
    
    @classmethod
    def _get_future_dates(cls, last_date: str, days: int) -> List[str]:
        """获取未来日期列表"""
        if not last_date:
            base = datetime.now()
        else:
            base = datetime.strptime(last_date, "%Y-%m-%d")
        
        return [(base + timedelta(days=i+1)).strftime("%Y-%m-%d") for i in range(days)]
    
    @classmethod
    def _generate_sleep_summary(cls, avg_duration: float, avg_quality: float,
                                 anomalies: List) -> str:
        """生成睡眠摘要"""
        parts = []
        
        if avg_duration >= 7:
            parts.append(f'平均睡眠{avg_duration:.1f}小时，时长充足')
        elif avg_duration >= 6:
            parts.append(f'平均睡眠{avg_duration:.1f}小时，时长略短')
        else:
            parts.append(f'平均睡眠{avg_duration:.1f}小时，时长不足')
        
        if avg_quality >= 80:
            parts.append('睡眠质量良好')
        elif avg_quality >= 60:
            parts.append('睡眠质量一般')
        else:
            parts.append('睡眠质量较差')
        
        if anomalies:
            parts.append(f'近期有{len(anomalies)}次睡眠异常')
        
        return '，'.join(parts)
    
    @classmethod
    def _generate_activity_summary(cls, avg_steps: float, reach_rate: float,
                                    trend: Dict) -> str:
        """生成活动量摘要"""
        parts = []
        
        if avg_steps >= 10000:
            parts.append(f'日均{int(avg_steps)}步，运动量充足')
        elif avg_steps >= 6000:
            parts.append(f'日均{int(avg_steps)}步，运动量适中')
        else:
            parts.append(f'日均{int(avg_steps)}步，建议增加运动')
        
        parts.append(f'目标达成率{reach_rate:.0f}%')
        
        direction = trend.get('direction', 'stable')
        if direction == 'rising':
            parts.append('运动量呈上升趋势')
        elif direction == 'falling':
            parts.append('运动量有所下降')
        
        return '，'.join(parts)
    
    @classmethod
    def _generate_comprehensive_recommendations(cls, health_score: Dict,
                                                  heart_rate: Dict,
                                                  sleep: Dict,
                                                  activity: Dict) -> List[str]:
        """生成综合健康建议"""
        recommendations = []
        
        # 基于健康评分
        score = health_score.get('overall_score', 70)
        if score < 60:
            recommendations.append('您的健康评分偏低，建议进行全面体检')
        
        # 基于睡眠
        sleep_duration = sleep.get('duration', {}).get('avg', 7)
        if sleep_duration < 6:
            recommendations.append('睡眠时间不足，建议保证每晚7-8小时睡眠')
        
        sleep_quality = sleep.get('quality', {}).get('avg', 70)
        if sleep_quality < 60:
            recommendations.append('睡眠质量较差，建议改善睡眠环境，避免睡前使用电子设备')
        
        # 基于活动量
        avg_steps = activity.get('steps', {}).get('avg', 0)
        if avg_steps < 5000:
            recommendations.append('日常活动量偏少，建议每天步行至少6000步')
        
        reach_rate = activity.get('steps', {}).get('reach_rate', 0)
        if reach_rate < 50:
            recommendations.append('运动目标达成率较低，可以设置更合理的目标并坚持')
        
        # 基于心率
        hr_anomalies = heart_rate.get('anomalies', {}).get('anomaly_count', 0)
        if hr_anomalies > 3:
            recommendations.append('近期心率波动较大，建议关注并记录异常情况')
        
        # 通用建议
        if not recommendations:
            recommendations.append('继续保持良好的生活习惯')
        
        recommendations.append('定期进行健康检查，及时了解身体状况')
        
        return recommendations[:6]
