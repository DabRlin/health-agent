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


@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    """修改密码"""
    from utils import login_required, get_current_user_id
    from flask import g
    # 手动验证 token
    auth_header = request.headers.get('Authorization', '')
    parts = auth_header.split()
    if len(parts) != 2:
        return jsonify({"success": False, "error": "未登录"}), 401
    from utils.jwt_utils import verify_token
    is_valid, payload, error = verify_token(parts[1])
    if not is_valid:
        return jsonify({"success": False, "error": error}), 401

    user_id = payload.get('user_id')
    data = request.json or {}
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')

    success, error = AuthService.change_password(user_id, old_password, new_password)
    if not success:
        return jsonify({"success": False, "error": error}), 400
    return jsonify({"success": True, "message": "密码修改成功"})


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """用户登出"""
    return jsonify({"success": True, "message": "已退出登录"})
