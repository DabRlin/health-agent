"""
风险评估路由
"""
from flask import Blueprint, jsonify, request
from services import RiskService
from utils import login_required, get_current_user_id

risk_bp = Blueprint('risk', __name__, url_prefix='/api/risk')


@risk_bp.route('/assessments', methods=['GET'])
@login_required
def get_risk_assessments():
    """获取风险评估列表"""
    user_id = get_current_user_id()
    assessments = RiskService.get_assessments(user_id)
    return jsonify({"success": True, "data": assessments})


@risk_bp.route('/assess', methods=['POST'])
@login_required
def create_risk_assessment():
    """创建风险评估"""
    user_id = get_current_user_id()
    data = request.json or {}
    assessment_type = data.get("type", "cardiovascular")
    
    result = RiskService.create_assessment(user_id, assessment_type)
    if not result:
        return jsonify({"success": False, "error": "评估失败"}), 500
    
    return jsonify({"success": True, "data": result})
