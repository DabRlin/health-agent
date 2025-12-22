"""
健康数据路由
"""
from flask import Blueprint, jsonify, request
from services import HealthService, UserService
from utils import login_required, get_current_user_id
from datetime import datetime

health_bp = Blueprint('health', __name__, url_prefix='/api')


@health_bp.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({"status": "ok", "message": "HealthAI API is running"})


@health_bp.route('/metrics', methods=['GET'])
@login_required
def get_metrics():
    """获取健康指标"""
    user_id = get_current_user_id()
    metrics = HealthService.get_metrics(user_id)
    return jsonify({"success": True, "data": metrics})


@health_bp.route('/metrics/trend', methods=['GET'])
@login_required
def get_metrics_trend():
    """获取健康指标趋势"""
    user_id = get_current_user_id()
    days = request.args.get('days', 30, type=int)
    data = HealthService.get_metrics_trend(user_id, days)
    return jsonify({"success": True, "data": data})


@health_bp.route('/metrics/add', methods=['POST'])
@login_required
def add_metric():
    """添加健康指标"""
    user_id = get_current_user_id()
    data = request.json or {}
    metric_type = data.get("type")
    value = data.get("value")
    
    if not metric_type or value is None:
        return jsonify({"success": False, "error": "缺少必要参数"}), 400
    
    result = HealthService.add_metric(user_id, metric_type, value)
    if not result:
        return jsonify({"success": False, "error": "无效的指标类型"}), 400
    
    return jsonify({"success": True, "data": result})


@health_bp.route('/records', methods=['GET'])
@login_required
def get_records():
    """获取健康记录"""
    user_id = get_current_user_id()
    records = HealthService.get_records(user_id)
    return jsonify({"success": True, "data": records})


@health_bp.route('/records', methods=['POST'])
@login_required
def add_record():
    """添加健康记录"""
    user_id = get_current_user_id()
    data = request.json or {}
    record_type = data.get("type", "日常监测")
    source = data.get("source", "手动录入")
    
    result = HealthService.add_record(user_id, record_type, source)
    if not result:
        return jsonify({"success": False, "error": "添加失败"}), 500
    
    return jsonify({"success": True, "data": result})


@health_bp.route('/dashboard', methods=['GET'])
@login_required
def get_dashboard():
    """获取首页仪表盘数据"""
    user_id = get_current_user_id()
    user = UserService.get_user(user_id)
    if not user:
        return jsonify({"success": False, "error": "用户不存在"}), 404
    
    metrics = HealthService.get_metrics(user_id)[:4]  # 取前4个指标
    records = HealthService.get_records(user_id, limit=3)
    
    return jsonify({
        "success": True,
        "data": {
            "user": {
                "name": user["name"],
                "health_score": user["health_score"],
                "health_days": user["health_days"]
            },
            "metrics": metrics,
            "recent_records": records,
            "quick_actions": [
                {"title": "智能问诊", "desc": "描述症状，获取健康建议", "icon": "MessageCircle", "path": "/consultation", "color": "#0866FF"},
                {"title": "健康数据", "desc": "查看和管理健康指标", "icon": "Activity", "path": "/health-data", "color": "#31A24C"},
                {"title": "风险评估", "desc": "评估疾病风险等级", "icon": "ShieldCheck", "path": "/risk-assessment", "color": "#F7B928"},
            ]
        }
    })
