"""
HealthAI MVP - 路由层
"""
from .auth import auth_bp
from .user import user_bp
from .health import health_bp
from .consultation import consultation_bp
from .risk import risk_bp
from .trend import trend_bp

__all__ = ['auth_bp', 'user_bp', 'health_bp', 'consultation_bp', 'risk_bp', 'trend_bp']
