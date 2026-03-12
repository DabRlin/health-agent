"""
HealthAI MVP - 路由层
"""
from .auth import auth_bp
from .user import user_bp
from .health import health_bp
from .consultation import consultation_bp
from .risk import risk_bp
from .trend import trend_bp
from .exam import exam_bp
from .admin import admin_bp
from .medical import medical_bp

__all__ = ['auth_bp', 'user_bp', 'health_bp', 'consultation_bp', 'risk_bp', 'trend_bp', 'exam_bp', 'admin_bp', 'medical_bp']
