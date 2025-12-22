"""
健康趋势分析模块
包含时序预测和异常检测功能

算法说明:
1. 趋势预测: 使用移动平均和线性回归进行短期预测
2. 异常检测: 使用统计方法 (Z-Score, IQR) 和规则引擎
3. 健康评分: 综合多维度指标计算健康评分
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import math


@dataclass
class TimeSeriesPoint:
    """时序数据点"""
    timestamp: datetime
    value: float


class TrendAnalyzer:
    """
    趋势分析器
    
    功能:
    - 计算移动平均
    - 线性回归预测
    - 趋势方向判断
    - 变化率分析
    """
    
    @classmethod
    def calculate_moving_average(cls, data: List[float], window: int = 7) -> List[float]:
        """
        计算移动平均
        
        Args:
            data: 数值列表
            window: 窗口大小
            
        Returns:
            移动平均值列表
        """
        if len(data) < window:
            return data
        
        result = []
        for i in range(len(data)):
            if i < window - 1:
                result.append(sum(data[:i+1]) / (i + 1))
            else:
                result.append(sum(data[i-window+1:i+1]) / window)
        
        return result
    
    @classmethod
    def linear_regression(cls, data: List[float]) -> Tuple[float, float]:
        """
        简单线性回归
        
        Args:
            data: 数值列表 (y值，x为索引)
            
        Returns:
            (斜率, 截距)
        """
        n = len(data)
        if n < 2:
            return 0.0, data[0] if data else 0.0
        
        x_mean = (n - 1) / 2
        y_mean = sum(data) / n
        
        numerator = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(data))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0, y_mean
        
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        
        return slope, intercept
    
    @classmethod
    def predict_next_values(cls, data: List[float], steps: int = 7) -> List[float]:
        """
        预测未来值
        
        Args:
            data: 历史数据
            steps: 预测步数
            
        Returns:
            预测值列表
        """
        if len(data) < 3:
            return [data[-1]] * steps if data else [0] * steps
        
        # 使用最近14天数据进行预测
        recent_data = data[-14:] if len(data) > 14 else data
        slope, intercept = cls.linear_regression(recent_data)
        
        n = len(recent_data)
        predictions = []
        for i in range(steps):
            pred = slope * (n + i) + intercept
            predictions.append(pred)
        
        return predictions
    
    @classmethod
    def analyze_trend(cls, data: List[float], metric_type: str = None) -> Dict:
        """
        分析数据趋势
        
        Args:
            data: 历史数据列表
            metric_type: 指标类型
            
        Returns:
            {
                'direction': str,      # 趋势方向: rising/falling/stable
                'strength': str,       # 趋势强度: strong/moderate/weak
                'change_rate': float,  # 变化率 (%)
                'prediction': list,    # 未来7天预测
                'moving_avg': list,    # 移动平均
                'analysis': str        # 文字分析
            }
        """
        if len(data) < 3:
            return {
                'direction': 'unknown',
                'strength': 'unknown',
                'change_rate': 0,
                'prediction': [],
                'moving_avg': data,
                'analysis': '数据不足，无法分析趋势'
            }
        
        # 计算移动平均
        moving_avg = cls.calculate_moving_average(data, window=7)
        
        # 线性回归
        slope, _ = cls.linear_regression(data[-14:] if len(data) > 14 else data)
        
        # 计算变化率
        if data[0] != 0:
            change_rate = ((data[-1] - data[0]) / data[0]) * 100
        else:
            change_rate = 0
        
        # 判断趋势方向
        if abs(slope) < 0.1:
            direction = 'stable'
        elif slope > 0:
            direction = 'rising'
        else:
            direction = 'falling'
        
        # 判断趋势强度
        abs_slope = abs(slope)
        if abs_slope < 0.5:
            strength = 'weak'
        elif abs_slope < 2:
            strength = 'moderate'
        else:
            strength = 'strong'
        
        # 预测未来值
        predictions = cls.predict_next_values(data, steps=7)
        
        # 生成分析文字
        analysis = cls._generate_trend_analysis(
            direction, strength, change_rate, metric_type
        )
        
        return {
            'direction': direction,
            'strength': strength,
            'change_rate': round(change_rate, 2),
            'prediction': [round(p, 1) for p in predictions],
            'moving_avg': [round(m, 1) for m in moving_avg],
            'analysis': analysis
        }
    
    @classmethod
    def _generate_trend_analysis(cls, direction: str, strength: str, 
                                  change_rate: float, metric_type: str = None) -> str:
        """生成趋势分析文字"""
        metric_names = {
            'heart_rate': '心率',
            'blood_pressure_sys': '收缩压',
            'blood_pressure_dia': '舒张压',
            'blood_sugar': '血糖',
            'weight': '体重',
            'spo2': '血氧',
            'steps': '步数',
            'sleep_duration': '睡眠时长'
        }
        
        metric_name = metric_names.get(metric_type, '该指标')
        
        direction_text = {
            'rising': '呈上升趋势',
            'falling': '呈下降趋势',
            'stable': '保持稳定'
        }
        
        strength_text = {
            'strong': '明显',
            'moderate': '轻微',
            'weak': '基本'
        }
        
        if direction == 'stable':
            return f"{metric_name}{strength_text.get(strength, '')}稳定，变化幅度{abs(change_rate):.1f}%"
        else:
            return f"{metric_name}{direction_text.get(direction, '')}，{strength_text.get(strength, '')}变化，幅度{abs(change_rate):.1f}%"


class AnomalyDetector:
    """
    异常检测器
    
    方法:
    1. Z-Score: 基于标准差的异常检测
    2. IQR: 基于四分位距的异常检测
    3. 规则引擎: 基于医学阈值的异常检测
    """
    
    # 医学阈值定义
    MEDICAL_THRESHOLDS = {
        'heart_rate': {
            'critical_low': 40,
            'low': 50,
            'high': 100,
            'critical_high': 120,
            'unit': 'bpm'
        },
        'blood_pressure_sys': {
            'critical_low': 80,
            'low': 90,
            'high': 140,
            'critical_high': 180,
            'unit': 'mmHg'
        },
        'blood_pressure_dia': {
            'critical_low': 50,
            'low': 60,
            'high': 90,
            'critical_high': 120,
            'unit': 'mmHg'
        },
        'blood_sugar': {
            'critical_low': 3.0,
            'low': 3.9,
            'high': 6.1,
            'critical_high': 11.1,
            'unit': 'mmol/L'
        },
        'spo2': {
            'critical_low': 90,
            'low': 94,
            'high': 100,
            'critical_high': 100,
            'unit': '%'
        },
        'weight': {
            'change_threshold': 2,  # kg/周
            'unit': 'kg'
        }
    }
    
    @classmethod
    def detect_zscore(cls, data: List[float], threshold: float = 2.5) -> List[Dict]:
        """
        Z-Score 异常检测
        
        Args:
            data: 数值列表
            threshold: Z-Score 阈值 (默认2.5)
            
        Returns:
            异常点列表 [{'index': int, 'value': float, 'zscore': float}]
        """
        if len(data) < 3:
            return []
        
        mean = sum(data) / len(data)
        variance = sum((x - mean) ** 2 for x in data) / len(data)
        std = math.sqrt(variance) if variance > 0 else 1
        
        anomalies = []
        for i, value in enumerate(data):
            zscore = (value - mean) / std
            if abs(zscore) > threshold:
                anomalies.append({
                    'index': i,
                    'value': value,
                    'zscore': round(zscore, 2),
                    'type': 'high' if zscore > 0 else 'low'
                })
        
        return anomalies
    
    @classmethod
    def detect_iqr(cls, data: List[float], multiplier: float = 1.5) -> List[Dict]:
        """
        IQR (四分位距) 异常检测
        
        Args:
            data: 数值列表
            multiplier: IQR 乘数 (默认1.5)
            
        Returns:
            异常点列表
        """
        if len(data) < 4:
            return []
        
        sorted_data = sorted(data)
        n = len(sorted_data)
        
        q1 = sorted_data[n // 4]
        q3 = sorted_data[3 * n // 4]
        iqr = q3 - q1
        
        lower_bound = q1 - multiplier * iqr
        upper_bound = q3 + multiplier * iqr
        
        anomalies = []
        for i, value in enumerate(data):
            if value < lower_bound or value > upper_bound:
                anomalies.append({
                    'index': i,
                    'value': value,
                    'lower_bound': round(lower_bound, 1),
                    'upper_bound': round(upper_bound, 1),
                    'type': 'high' if value > upper_bound else 'low'
                })
        
        return anomalies
    
    @classmethod
    def detect_medical_anomaly(cls, value: float, metric_type: str) -> Optional[Dict]:
        """
        基于医学阈值的异常检测
        
        Args:
            value: 测量值
            metric_type: 指标类型
            
        Returns:
            异常信息或 None
        """
        thresholds = cls.MEDICAL_THRESHOLDS.get(metric_type)
        if not thresholds:
            return None
        
        result = {
            'value': value,
            'metric_type': metric_type,
            'unit': thresholds.get('unit', ''),
            'severity': 'normal',
            'message': ''
        }
        
        if 'critical_low' in thresholds:
            if value <= thresholds['critical_low']:
                result['severity'] = 'critical'
                result['type'] = 'low'
                result['message'] = f'严重偏低 (≤{thresholds["critical_low"]})'
            elif value <= thresholds['low']:
                result['severity'] = 'warning'
                result['type'] = 'low'
                result['message'] = f'偏低 (≤{thresholds["low"]})'
            elif value >= thresholds['critical_high']:
                result['severity'] = 'critical'
                result['type'] = 'high'
                result['message'] = f'严重偏高 (≥{thresholds["critical_high"]})'
            elif value >= thresholds['high']:
                result['severity'] = 'warning'
                result['type'] = 'high'
                result['message'] = f'偏高 (≥{thresholds["high"]})'
        
        if result['severity'] == 'normal':
            return None
        
        return result
    
    @classmethod
    def analyze_data(cls, data: List[float], metric_type: str, 
                     dates: List[str] = None) -> Dict:
        """
        综合异常分析
        
        Args:
            data: 数值列表
            metric_type: 指标类型
            dates: 日期列表 (可选)
            
        Returns:
            {
                'has_anomaly': bool,
                'anomaly_count': int,
                'anomalies': list,
                'latest_status': dict,
                'summary': str
            }
        """
        if not data:
            return {
                'has_anomaly': False,
                'anomaly_count': 0,
                'anomalies': [],
                'latest_status': None,
                'summary': '暂无数据'
            }
        
        # 统计异常
        zscore_anomalies = cls.detect_zscore(data)
        iqr_anomalies = cls.detect_iqr(data)
        
        # 合并异常索引
        anomaly_indices = set()
        for a in zscore_anomalies + iqr_anomalies:
            anomaly_indices.add(a['index'])
        
        # 构建异常列表
        anomalies = []
        for idx in sorted(anomaly_indices):
            anomaly = {
                'index': idx,
                'value': data[idx],
                'date': dates[idx] if dates and idx < len(dates) else None
            }
            
            # 检查医学阈值
            medical = cls.detect_medical_anomaly(data[idx], metric_type)
            if medical:
                anomaly['severity'] = medical['severity']
                anomaly['message'] = medical['message']
            else:
                anomaly['severity'] = 'warning'
                anomaly['message'] = '统计异常值'
            
            anomalies.append(anomaly)
        
        # 检查最新值状态
        latest_status = cls.detect_medical_anomaly(data[-1], metric_type)
        
        # 生成摘要
        summary = cls._generate_summary(anomalies, latest_status, metric_type)
        
        return {
            'has_anomaly': len(anomalies) > 0,
            'anomaly_count': len(anomalies),
            'anomalies': anomalies,
            'latest_status': latest_status,
            'summary': summary
        }
    
    @classmethod
    def _generate_summary(cls, anomalies: List[Dict], latest_status: Optional[Dict],
                          metric_type: str) -> str:
        """生成异常摘要"""
        metric_names = {
            'heart_rate': '心率',
            'blood_pressure_sys': '收缩压',
            'blood_pressure_dia': '舒张压',
            'blood_sugar': '血糖',
            'spo2': '血氧'
        }
        name = metric_names.get(metric_type, '该指标')
        
        if not anomalies and not latest_status:
            return f'{name}数据正常，未发现异常'
        
        parts = []
        
        if latest_status:
            if latest_status['severity'] == 'critical':
                parts.append(f'⚠️ 当前{name}{latest_status["message"]}，建议立即就医')
            else:
                parts.append(f'⚡ 当前{name}{latest_status["message"]}，请注意监测')
        
        critical_count = sum(1 for a in anomalies if a.get('severity') == 'critical')
        warning_count = len(anomalies) - critical_count
        
        if critical_count > 0:
            parts.append(f'近期有{critical_count}次严重异常')
        if warning_count > 0:
            parts.append(f'{warning_count}次轻度异常')
        
        return '，'.join(parts) if parts else f'{name}数据正常'


class HealthScoreCalculator:
    """
    健康评分计算器
    
    综合多维度指标计算健康评分 (0-100)
    """
    
    # 各指标权重
    WEIGHTS = {
        'heart_rate': 0.15,
        'blood_pressure': 0.20,
        'blood_sugar': 0.15,
        'sleep': 0.15,
        'activity': 0.15,
        'weight': 0.10,
        'spo2': 0.10
    }
    
    @classmethod
    def calculate_metric_score(cls, value: float, metric_type: str) -> float:
        """
        计算单项指标得分 (0-100)
        
        基于与正常范围的偏离程度计算
        """
        ranges = {
            'heart_rate': {'optimal': (60, 80), 'normal': (50, 100)},
            'blood_pressure_sys': {'optimal': (100, 120), 'normal': (90, 140)},
            'blood_pressure_dia': {'optimal': (60, 80), 'normal': (60, 90)},
            'blood_sugar': {'optimal': (4.0, 5.5), 'normal': (3.9, 6.1)},
            'spo2': {'optimal': (97, 100), 'normal': (94, 100)},
            'sleep_duration': {'optimal': (7, 8), 'normal': (6, 9)},
            'steps': {'optimal': (8000, 12000), 'normal': (5000, 15000)},
            'bmi': {'optimal': (18.5, 24), 'normal': (18.5, 28)}
        }
        
        if metric_type not in ranges:
            return 70  # 默认分数
        
        optimal = ranges[metric_type]['optimal']
        normal = ranges[metric_type]['normal']
        
        # 在最优范围内: 90-100分
        if optimal[0] <= value <= optimal[1]:
            return 95
        
        # 在正常范围内: 70-90分
        if normal[0] <= value <= normal[1]:
            if value < optimal[0]:
                ratio = (value - normal[0]) / (optimal[0] - normal[0])
            else:
                ratio = (normal[1] - value) / (normal[1] - optimal[1])
            return 70 + ratio * 20
        
        # 超出正常范围: 0-70分
        if value < normal[0]:
            ratio = max(0, value / normal[0])
        else:
            ratio = max(0, 1 - (value - normal[1]) / normal[1])
        
        return ratio * 70
    
    @classmethod
    def calculate_overall_score(cls, metrics: Dict[str, float]) -> Dict:
        """
        计算综合健康评分
        
        Args:
            metrics: {metric_type: value}
            
        Returns:
            {
                'overall_score': int,
                'category_scores': dict,
                'level': str,
                'summary': str
            }
        """
        category_scores = {}
        weighted_sum = 0
        total_weight = 0
        
        # 心率
        if 'heart_rate' in metrics:
            score = cls.calculate_metric_score(metrics['heart_rate'], 'heart_rate')
            category_scores['heart_rate'] = round(score)
            weighted_sum += score * cls.WEIGHTS['heart_rate']
            total_weight += cls.WEIGHTS['heart_rate']
        
        # 血压
        if 'blood_pressure_sys' in metrics and 'blood_pressure_dia' in metrics:
            sys_score = cls.calculate_metric_score(metrics['blood_pressure_sys'], 'blood_pressure_sys')
            dia_score = cls.calculate_metric_score(metrics['blood_pressure_dia'], 'blood_pressure_dia')
            bp_score = (sys_score + dia_score) / 2
            category_scores['blood_pressure'] = round(bp_score)
            weighted_sum += bp_score * cls.WEIGHTS['blood_pressure']
            total_weight += cls.WEIGHTS['blood_pressure']
        
        # 血糖
        if 'blood_sugar' in metrics:
            score = cls.calculate_metric_score(metrics['blood_sugar'], 'blood_sugar')
            category_scores['blood_sugar'] = round(score)
            weighted_sum += score * cls.WEIGHTS['blood_sugar']
            total_weight += cls.WEIGHTS['blood_sugar']
        
        # 睡眠
        if 'sleep_duration' in metrics:
            score = cls.calculate_metric_score(metrics['sleep_duration'], 'sleep_duration')
            category_scores['sleep'] = round(score)
            weighted_sum += score * cls.WEIGHTS['sleep']
            total_weight += cls.WEIGHTS['sleep']
        
        # 活动量
        if 'steps' in metrics:
            score = cls.calculate_metric_score(metrics['steps'], 'steps')
            category_scores['activity'] = round(score)
            weighted_sum += score * cls.WEIGHTS['activity']
            total_weight += cls.WEIGHTS['activity']
        
        # 血氧
        if 'spo2' in metrics:
            score = cls.calculate_metric_score(metrics['spo2'], 'spo2')
            category_scores['spo2'] = round(score)
            weighted_sum += score * cls.WEIGHTS['spo2']
            total_weight += cls.WEIGHTS['spo2']
        
        # BMI/体重
        if 'bmi' in metrics:
            score = cls.calculate_metric_score(metrics['bmi'], 'bmi')
            category_scores['weight'] = round(score)
            weighted_sum += score * cls.WEIGHTS['weight']
            total_weight += cls.WEIGHTS['weight']
        
        # 计算总分
        if total_weight > 0:
            overall_score = int(weighted_sum / total_weight)
        else:
            overall_score = 70  # 默认分数
        
        # 确定等级
        if overall_score >= 90:
            level = 'excellent'
            summary = '健康状况优秀，请继续保持！'
        elif overall_score >= 75:
            level = 'good'
            summary = '健康状况良好，注意保持健康习惯'
        elif overall_score >= 60:
            level = 'fair'
            summary = '健康状况一般，建议改善生活方式'
        else:
            level = 'poor'
            summary = '健康状况需要关注，建议就医检查'
        
        return {
            'overall_score': overall_score,
            'category_scores': category_scores,
            'level': level,
            'summary': summary
        }


# 便捷函数
def analyze_health_trend(data: List[float], metric_type: str = None) -> Dict:
    """分析健康数据趋势"""
    return TrendAnalyzer.analyze_trend(data, metric_type)


def detect_anomalies(data: List[float], metric_type: str, 
                     dates: List[str] = None) -> Dict:
    """检测健康数据异常"""
    return AnomalyDetector.analyze_data(data, metric_type, dates)


def calculate_health_score(metrics: Dict[str, float]) -> Dict:
    """计算综合健康评分"""
    return HealthScoreCalculator.calculate_overall_score(metrics)
