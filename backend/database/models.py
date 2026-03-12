"""
HealthAI MVP - 数据库模型定义
使用 SQLAlchemy ORM
"""
import os
import logging
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

logger = logging.getLogger(__name__)

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
    password = Column(String(255), nullable=False)  # werkzeug scrypt hash
    role = Column(String(20), default='user')  # user, admin
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
    exam_reports = relationship("ExamReport", back_populates="user")


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

    __table_args__ = (
        Index('ix_health_metrics_user_type_time', 'user_id', 'metric_type', 'recorded_at'),
    )


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
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    session_id = Column(String(50), unique=True, nullable=False)
    department = Column(String(30), default='general')  # general, cardiology, endocrinology, dermatology
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
    consultation_id = Column(Integer, ForeignKey('consultations.id'), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    consultation = relationship("Consultation", back_populates="messages")


class ExamReport(Base):
    """体检报告表"""
    __tablename__ = 'exam_reports'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    filename = Column(String(255), nullable=False)       # 原始文件名
    file_path = Column(String(512))                      # 服务器存储路径
    report_date = Column(String(20))                     # 报告日期 YYYY-MM-DD（由 LLM 提取）
    hospital = Column(String(200))                       # 医院名称
    raw_text = Column(Text)                              # OCR 提取的原始文字
    parsed_data = Column(JSON)                           # LLM 结构化解析结果
    status = Column(String(20), default='pending')       # pending / processing / done / failed
    uploaded_at = Column(DateTime, default=datetime.now)
    
    user = relationship("User", back_populates="exam_reports")


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
    source = Column(String(10), default='user')  # user=用户手动, system=系统自动评估
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

    __table_args__ = (
        Index('ix_device_readings_user_type_time', 'user_id', 'metric_type', 'recorded_at'),
    )


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
        Index('ix_daily_summary_user_date', 'user_id', 'date'),
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


class HealthKnowledge(Base):
    """健康知识库表"""
    __tablename__ = 'health_knowledge'

    id = Column(Integer, primary_key=True, autoincrement=True)
    # 分类：disease（疾病）/ indicator（指标参考范围）/ diet（饮食）/ drug（药物）/ symptom（症状）/ lifestyle（生活方式）
    category = Column(String(20), nullable=False, index=True)
    # 子分类，如 cardiovascular / diabetes / nutrition 等
    subcategory = Column(String(50), index=True)
    title = Column(String(100), nullable=False)
    # 关键词，逗号分隔，用于全文检索
    keywords = Column(Text)
    content = Column(Text, nullable=False)
    # 参考范围结构化数据（适用于 indicator 类）
    reference_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)


class Medication(Base):
    """用药记录表 - 混合存储（结构化触发 + 非结构化展示）"""
    __tablename__ = 'medications'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)

    # ── 结构化部分（用于通知调度）──
    name = Column(String(100), nullable=False)
    med_type = Column(String(20), default='oral')  # oral / injection / topical / patch / wash
    # reminders: [{"time": "08:00", "relation": "after_meal", "dose": "1粒"}, ...]
    reminders = Column(JSON, default=list)
    duration_days = Column(Integer)               # 疗程天数，可为空
    start_date = Column(String(20))               # 开始服药日期 YYYY-MM-DD

    # ── 非结构化部分（原始信息，直接展示）──
    raw_instructions = Column(Text)               # 用法用量原文
    contraindications = Column(Text)              # 禁忌
    side_effects = Column(Text)                   # 不良反应
    storage = Column(Text)                        # 储存条件
    ocr_raw_text = Column(Text)                   # VL/OCR 识别全文

    # ── 附件 ──
    image_path = Column(String(500))              # 说明书图片路径

    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("User", backref="medications")


def init_db():
    """初始化数据库，创建所有表"""
    Base.metadata.create_all(bind=engine)
    logger.info("数据库表创建完成")


def drop_db():
    """删除所有表"""
    Base.metadata.drop_all(bind=engine)
    logger.info("数据库表已删除")


if __name__ == '__main__':
    init_db()
