"""
认证路由
"""
from flask import Blueprint, jsonify, request
from services import AuthService

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.json or {}
    username = data.get("username", "")
    password = data.get("password", "")
    
    success, user_data, error = AuthService.login(username, password)
    
    if not success:
        return jsonify({"success": False, "error": error}), 401
    
    # token 已包含在 user_data 中
    token = user_data.pop("token", "")
    
    return jsonify({
        "success": True,
        "data": {
            "user": user_data,
            "token": token
        }
    })


@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.json or {}
    username = data.get("username", "")
    password = data.get("password", "")
    name = data.get("name", "")
    
    success, user_data, error = AuthService.register(username, password, name)
    
    if not success:
        return jsonify({"success": False, "error": error}), 400
    
    # token 已包含在 user_data 中
    token = user_data.pop("token", "")
    
    return jsonify({
        "success": True,
        "data": {
            "user": user_data,
            "token": token
        },
        "message": "注册成功"
    })


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """用户登出"""
    return jsonify({"success": True, "message": "已退出登录"})
