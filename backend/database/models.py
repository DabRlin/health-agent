"""
HealthAI MVP - 数据库模型定义
使用 SQLAlchemy ORM
"""
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(__file__), 'healthai.db')
DATABASE_URL = f'sqlite:///{DB_PATH}'

# 创建引擎和会话
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==================== 数据模型 ====================

class Account(Base):
    """账户表 - 用于登录认证"""
    __tablename__ = 'accounts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)  # 实际项目应加密存储
    user_id = Column(Integer, ForeignKey('users.id'))
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    
    user = relationship("User", back_populates="account")


class User(Base):
    """用户表"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    gender = Column(String(10))
    age = Column(Integer)
    birthday = Column(String(20))
    phone = Column(String(20))
    email = Column(String(100))
    location = Column(String(100))
    avatar = Column(String(255))
    health_score = Column(Integer, default=80)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 关联
    account = relationship("Account", back_populates="user", uselist=False)
    health_records = relationship("HealthRecord", back_populates="user")
    health_metrics = relationship("HealthMetric", back_populates="user")
    risk_assessments = relationship("RiskAssessment", back_populates="user")
    consultations = relationship("Consultation", back_populates="user")


class HealthRecord(Base):
    """健康记录表"""
    __tablename__ = 'health_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    record_type = Column(String(50), nullable=False)  # 体检报告、日常监测、智能问诊、风险评估
    source = Column(String(50))  # 医院导入、手动录入、智能手表、在线咨询
    status = Column(String(20), default='已记录')
    risk_level = Column(String(20), default='low')  # low, medium, high
    summary = Column(Text)
    data = Column(JSON)  # 存储详细数据
    record_date = Column(DateTime, default=datetime.now)
    created_at = Column(DateTime, default=datetime.now)
    
    user = relationship("User", back_populates="health_records")


class HealthMetric(Base):
    """健康指标表"""
    __tablename__ = 'health_metrics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    metric_type = Column(String(50), nullable=False)  # heart_rate, blood_pressure_sys, blood_pressure_dia, blood_sugar, bmi, sleep
    value = Column(Float, nullable=False)
    unit = Column(String(20))
    status = Column(String(20), default='normal')  # normal, warning, danger
    recorded_at = Column(DateTime, default=datetime.now)
    
    user = relationship("User", back_populates="health_metrics")


class RiskAssessment(Base):
    """风险评估表"""
    __tablename__ = 'risk_assessments'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    assessment_type = Column(String(50), nullable=False)  # cardiovascular, diabetes, metabolic, osteoporosis
    name = Column(String(100))
    risk_level = Column(String(20))  # low, medium, high
    score = Column(Integer)
    factors = Column(JSON)  # 风险因素列表
    recommendations = Column(JSON)  # 建议列表
    assessed_at = Column(DateTime, default=datetime.now)
    
    user = relationship("User", back_populates="risk_assessments")


class Consultation(Base):
    """问诊会话表"""
    __tablename__ = 'consultations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    session_id = Column(String(50), unique=True, nullable=False)
    summary = Column(String(200))
    status = Column(String(20), default='进行中')  # 进行中、已完成
    started_at = Column(DateTime, default=datetime.now)
    ended_at = Column(DateTime)
    
    user = relationship("User", back_populates="consultations")
    messages = relationship("ConsultationMessage", back_populates="consultation")


class ConsultationMessage(Base):
    """问诊消息表"""
    __tablename__ = 'consultation_messages'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    consultation_id = Column(Integer, ForeignKey('consultations.id'), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    consultation = relationship("Consultation", back_populates="messages")


class HealthReport(Base):
    """健康报告表"""
    __tablename__ = 'health_reports'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(100), nullable=False)
    report_type = Column(String(50))  # 体检报告、风险评估、健康总结
    file_path = Column(String(255))
    data = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)


class HealthTag(Base):
    """健康标签表"""
    __tablename__ = 'health_tags'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(50), nullable=False)
    tag_type = Column(String(20))  # positive, warning, neutral
    created_at = Column(DateTime, default=datetime.now)


# ==================== 穿戴设备数据模型 ====================

class DeviceReading(Base):
    """穿戴设备原始数据表 - 高频采集数据"""
    __tablename__ = 'device_readings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    device_type = Column(String(30))  # smartwatch, band, scale, blood_pressure_monitor
    metric_type = Column(String(30), nullable=False)  # heart_rate, steps, sleep, spo2, blood_pressure
    value = Column(Float, nullable=False)
    unit = Column(String(20))
    recorded_at = Column(DateTime, default=datetime.now, index=True)
    raw_data = Column(JSON)  # 保留原始 JSON 数据
    
    user = relationship("User", backref="device_readings")


class DailyHealthSummary(Base):
    """每日健康汇总表 - 用于分析和展示"""
    __tablename__ = 'daily_health_summaries'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    date = Column(String(10), nullable=False)  # YYYY-MM-DD
    
    # 心率统计
    avg_heart_rate = Column(Float)
    min_heart_rate = Column(Float)
    max_heart_rate = Column(Float)
    resting_heart_rate = Column(Float)
    
    # 活动统计
    total_steps = Column(Integer)
    active_minutes = Column(Integer)
    calories_burned = Column(Float)
    distance = Column(Float)  # 公里
    
    # 睡眠统计
    sleep_start_time = Column(String(5))  # HH:MM
    sleep_end_time = Column(String(5))    # HH:MM
    sleep_duration = Column(Float)        # 小时
    deep_sleep_duration = Column(Float)   # 小时
    light_sleep_duration = Column(Float)  # 小时
    rem_duration = Column(Float)          # 小时
    awake_count = Column(Integer)
    sleep_quality_score = Column(Integer)  # 0-100
    
    # 血氧统计
    avg_spo2 = Column(Float)
    min_spo2 = Column(Float)
    
    # 血压统计（如有设备）
    morning_systolic = Column(Float)
    morning_diastolic = Column(Float)
    evening_systolic = Column(Float)
    evening_diastolic = Column(Float)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    user = relationship("User", backref="daily_summaries")
    
    __table_args__ = (
        # 每个用户每天只有一条汇总记录
        {'sqlite_autoincrement': True},
    )


class UserHealthProfile(Base):
    """用户健康档案表 - 用于风险评估的基础数据"""
    __tablename__ = 'user_health_profiles'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, unique=True)
    
    # 基本身体数据
    height = Column(Float)          # 身高 cm
    weight = Column(Float)          # 体重 kg
    bmi = Column(Float)             # BMI
    waist = Column(Float)           # 腰围 cm
    
    # 血压基线
    systolic_bp = Column(Float)     # 收缩压 mmHg
    diastolic_bp = Column(Float)    # 舒张压 mmHg
    on_bp_medication = Column(Boolean, default=False)  # 是否服用降压药
    
    # 血液指标
    total_cholesterol = Column(Float)   # 总胆固醇 mg/dL
    hdl_cholesterol = Column(Float)     # HDL 胆固醇 mg/dL
    ldl_cholesterol = Column(Float)     # LDL 胆固醇 mg/dL
    triglycerides = Column(Float)       # 甘油三酯 mg/dL
    fasting_glucose = Column(Float)     # 空腹血糖 mmol/L
    hba1c = Column(Float)               # 糖化血红蛋白 %
    
    # 生活习惯
    is_smoker = Column(Boolean, default=False)
    smoking_years = Column(Integer)
    alcohol_frequency = Column(String(20))  # never, occasional, regular, heavy
    exercise_frequency = Column(String(20)) # never, 1-2/week, 3-4/week, daily
    exercise_minutes_per_week = Column(Integer)
    
    # 病史
    has_diabetes = Column(Boolean, default=False)
    has_hypertension = Column(Boolean, default=False)
    has_heart_disease = Column(Boolean, default=False)
    family_diabetes = Column(Boolean, default=False)
    family_heart_disease = Column(Boolean, default=False)
    family_hypertension = Column(Boolean, default=False)
    
    # 饮食习惯
    daily_fruit_vegetable = Column(Boolean, default=True)  # 每天吃蔬果
    high_salt_diet = Column(Boolean, default=False)
    
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    user = relationship("User", backref="health_profile", uselist=False)


def init_db():
    """初始化数据库，创建所有表"""
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表创建完成")


def drop_db():
    """删除所有表"""
    Base.metadata.drop_all(bind=engine)
    print("🗑️ 数据库表已删除")


if __name__ == '__main__':
    init_db()
