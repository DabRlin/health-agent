"""
趋势分析 API 路由
"""
from flask import Blueprint, request, jsonify
from services import TrendService
from utils import login_required, get_current_user_id

trend_bp = Blueprint('trend', __name__, url_prefix='/api/trend')


@trend_bp.route('/metric/<metric_type>', methods=['GET'])
@login_required
def get_metric_trend(metric_type):
    """
    获取指定指标的趋势分析
    
    GET /api/trend/metric/<metric_type>?days=30
    
    支持的 metric_type:
    - heart_rate: 心率
    - blood_pressure_sys: 收缩压
    - blood_pressure_dia: 舒张压
    - blood_sugar: 血糖
    - weight: 体重
    """
    user_id = get_current_user_id()
    days = request.args.get('days', 30, type=int)
    days = min(max(days, 7), 90)  # 限制在7-90天
    
    result = TrendService.get_metric_trend(user_id, metric_type, days)
    
    return jsonify({
        'success': True,
        'data': result
    })


@trend_bp.route('/device/<metric_type>', methods=['GET'])
@login_required
def get_device_trend(metric_type):
    """
    获取穿戴设备数据趋势
    
    GET /api/trend/device/<metric_type>?days=7
    
    支持的 metric_type:
    - heart_rate: 心率
    - spo2: 血氧
    - steps: 步数
    """
    user_id = get_current_user_id()
    days = request.args.get('days', 7, type=int)
    days = min(max(days, 1), 30)  # 限制在1-30天
    
    result = TrendService.get_device_data_trend(user_id, metric_type, days)
    
    return jsonify({
        'success': True,
        'data': result
    })


@trend_bp.route('/sleep', methods=['GET'])
@login_required
def get_sleep_trend():
    """
    获取睡眠趋势分析
    
    GET /api/trend/sleep?days=14
    """
    user_id = get_current_user_id()
    days = request.args.get('days', 14, type=int)
    days = min(max(days, 7), 30)
    
    result = TrendService.get_sleep_trend(user_id, days)
    
    return jsonify({
        'success': True,
        'data': result
    })


@trend_bp.route('/activity', methods=['GET'])
@login_required
def get_activity_trend():
    """
    获取活动量趋势分析
    
    GET /api/trend/activity?days=14
    """
    user_id = get_current_user_id()
    days = request.args.get('days', 14, type=int)
    days = min(max(days, 7), 30)
    
    result = TrendService.get_activity_trend(user_id, days)
    
    return jsonify({
        'success': True,
        'data': result
    })


@trend_bp.route('/score', methods=['GET'])
@login_required
def get_health_score():
    """
    获取综合健康评分
    
    GET /api/trend/score
    """
    user_id = get_current_user_id()
    result = TrendService.get_health_score(user_id)
    
    return jsonify({
        'success': True,
        'data': result
    })


@trend_bp.route('/analysis', methods=['GET'])
@login_required
def get_comprehensive_analysis():
    """
    获取综合健康分析报告
    
    GET /api/trend/analysis
    
    返回:
    - 健康评分
    - 各项趋势摘要
    - 异常汇总
    - 综合建议
    """
    user_id = get_current_user_id()
    result = TrendService.get_comprehensive_analysis(user_id)
    
    return jsonify({
        'success': True,
        'data': result
    })
