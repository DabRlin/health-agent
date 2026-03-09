"""
JWT 工具模块
用于生成和验证 JSON Web Token
"""
import jwt
from datetime import datetime, timedelta
from typing import Optional, Tuple
from functools import wraps
from flask import request, jsonify, g
import os

# JWT 配置
JWT_SECRET = os.getenv('JWT_SECRET', 'healthai-mvp-secret-key-2024')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24 * 7  # Token 有效期 7 天


def generate_token(user_id: int, username: str, role: str = 'user') -> str:
    """
    生成 JWT Token
    
    Args:
        user_id: 用户ID
        username: 用户名
        role: 角色 (user/admin)
    
    Returns:
        JWT Token 字符串
    """
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_token(token: str) -> Tuple[bool, Optional[dict], Optional[str]]:
    """
    验证 JWT Token
    
    Args:
        token: JWT Token 字符串
    
    Returns:
        (is_valid, payload, error_message)
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return True, payload, None
    except jwt.ExpiredSignatureError:
        return False, None, "Token 已过期"
    except jwt.InvalidTokenError:
        return False, None, "无效的 Token"


def login_required(f):
    """
    登录验证装饰器
    验证请求头中的 Authorization Token，并将用户信息注入到 g.current_user
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 获取 Authorization 头
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({"success": False, "error": "缺少认证信息"}), 401
        
        # 解析 Bearer Token
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({"success": False, "error": "认证格式错误"}), 401
        
        token = parts[1]
        
        # 验证 Token
        is_valid, payload, error = verify_token(token)
        if not is_valid:
            return jsonify({"success": False, "error": error}), 401
        
        # 将用户信息存入 Flask g 对象
        g.current_user = {
            'user_id': payload.get('user_id'),
            'username': payload.get('username'),
            'role': payload.get('role', 'user')
        }
        
        return f(*args, **kwargs)
    
    return decorated_function


def admin_required(f):
    """
    管理员权限装饰器
    必须登录且角色为 admin
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({"success": False, "error": "缺少认证信息"}), 401

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({"success": False, "error": "认证格式错误"}), 401

        is_valid, payload, error = verify_token(parts[1])
        if not is_valid:
            return jsonify({"success": False, "error": error}), 401

        if payload.get('role') != 'admin':
            return jsonify({"success": False, "error": "权限不足"}), 403

        g.current_user = {
            'user_id': payload.get('user_id'),
            'username': payload.get('username'),
            'role': 'admin'
        }
        return f(*args, **kwargs)

    return decorated_function


def get_current_user_id() -> Optional[int]:
    """获取当前登录用户的 ID"""
    if hasattr(g, 'current_user') and g.current_user:
        return g.current_user.get('user_id')
    return None


def get_current_role() -> str:
    """获取当前登录用户的角色"""
    if hasattr(g, 'current_user') and g.current_user:
        return g.current_user.get('role', 'user')
    return 'user'


def optional_login(f):
    """
    可选登录装饰器
    如果有 Token 则解析用户信息，没有也不报错
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
                is_valid, payload, _ = verify_token(token)
                if is_valid:
                    g.current_user = {
                        'user_id': payload.get('user_id'),
                        'username': payload.get('username'),
                        'role': payload.get('role', 'user')
                    }
                else:
                    g.current_user = None
            else:
                g.current_user = None
        else:
            g.current_user = None
        
        return f(*args, **kwargs)
    
    return decorated_function
