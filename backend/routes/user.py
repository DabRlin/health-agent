"""
用户路由
"""
from flask import Blueprint, jsonify, request
from services import UserService
from utils import login_required, get_current_user_id

user_bp = Blueprint('user', __name__, url_prefix='/api/user')


@user_bp.route('', methods=['GET'])
@login_required
def get_user():
    """获取用户信息"""
    user_id = get_current_user_id()
    user = UserService.get_user(user_id)
    if not user:
        return jsonify({"success": False, "error": "用户不存在"}), 404
    return jsonify({"success": True, "data": user})


@user_bp.route('/stats', methods=['GET'])
@login_required
def get_user_stats():
    """获取用户健康统计"""
    user_id = get_current_user_id()
    stats = UserService.get_user_stats(user_id)
    return jsonify({"success": True, "data": stats})


@user_bp.route('/tags', methods=['GET'])
@login_required
def get_user_tags():
    """获取用户健康标签"""
    user_id = get_current_user_id()
    tags = UserService.get_user_tags(user_id)
    return jsonify({"success": True, "data": tags})


@user_bp.route('/reports', methods=['GET'])
@login_required
def get_user_reports():
    """获取用户健康报告"""
    user_id = get_current_user_id()
    reports = UserService.get_user_reports(user_id)
    return jsonify({"success": True, "data": reports})


@user_bp.route('', methods=['PUT'])
@login_required
def update_user():
    """更新用户信息"""
    user_id = get_current_user_id()
    data = request.json or {}
    
    success, user_data, error = UserService.update_user(user_id, data)
    
    if not success:
        return jsonify({"success": False, "error": error}), 400
    
    return jsonify({
        "success": True,
        "data": user_data,
        "message": "更新成功"
    })
