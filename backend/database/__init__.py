"""
HealthAI MVP - 数据库模块
"""
from .models import (
    engine, SessionLocal, Base, get_db, init_db, drop_db,
    Account, User, HealthRecord, HealthMetric, RiskAssessment,
    Consultation, ConsultationMessage, HealthReport, HealthTag,
    DeviceReading, DailyHealthSummary, UserHealthProfile
)

__all__ = [
    'engine', 'SessionLocal', 'Base', 'get_db', 'init_db', 'drop_db',
    'Account', 'User', 'HealthRecord', 'HealthMetric', 'RiskAssessment',
    'Consultation', 'ConsultationMessage', 'HealthReport', 'HealthTag',
    'DeviceReading', 'DailyHealthSummary', 'UserHealthProfile'
]
