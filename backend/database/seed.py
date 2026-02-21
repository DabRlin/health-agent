"""
HealthAI MVP - 数据库种子数据
生成模拟数据并写入数据库
"""
import random
from datetime import datetime, timedelta
from models import (
    init_db, drop_db, SessionLocal,
    Account, User, HealthRecord, HealthMetric, RiskAssessment,
    Consultation, ConsultationMessage, HealthReport, HealthTag,
    DeviceReading, DailyHealthSummary, UserHealthProfile
)
from device_simulator import seed_device_data


def generate_seed_data():
    """生成并插入种子数据"""
    
    # 重置数据库
    drop_db()
    init_db()
    
    db = SessionLocal()
    
    try:
        # ==================== 1. 创建用户 ====================
        user = User(
            name="张三",
            gender="男",
            age=35,
            birthday="1989-05-15",
            phone="138****8888",
            email="zhang***@example.com",
            location="北京市朝阳区",
            avatar="https://api.dicebear.com/7.x/avataaars/svg?seed=health",
            health_score=85,
            created_at=datetime.now() - timedelta(days=30)
        )
        db.add(user)
        db.flush()  # 获取 user.id
        print(f"✅ 创建用户: {user.name} (ID: {user.id})")
        
        # ==================== 1.1 创建账户 ====================
        accounts_data = [
            {"username": "admin", "password": "123456", "user_id": user.id},
            {"username": "user", "password": "123456", "user_id": None},
            {"username": "demo", "password": "demo", "user_id": None},
        ]
        
        for acc_data in accounts_data:
            account = Account(
                username=acc_data["username"],
                password=acc_data["password"],  # 实际项目应加密
                user_id=acc_data["user_id"],
                is_active=True
            )
            db.add(account)
        
        print(f"✅ 创建账户: {len(accounts_data)}个 (admin/123456, user/123456, demo/demo)")
        
        # ==================== 1.2 创建用户健康档案（ML 模型必需）====================
        profile = UserHealthProfile(
            user_id=user.id,
            # 基本身体数据
            height=175.0,           # cm
            weight=72.0,            # kg
            bmi=23.5,               # kg/m²
            waist=85.0,             # cm
            # 血压基线
            systolic_bp=122.0,      # mmHg
            diastolic_bp=78.0,      # mmHg
            on_bp_medication=False,
            # 血液指标
            total_cholesterol=210.0,    # mg/dL（偏高，增加趣味性）
            hdl_cholesterol=52.0,       # mg/dL
            ldl_cholesterol=138.0,      # mg/dL
            triglycerides=145.0,        # mg/dL
            fasting_glucose=5.8,        # mmol/L（轻度偏高）
            hba1c=5.9,                  # %
            # 生活习惯
            is_smoker=False,
            smoking_years=0,
            alcohol_frequency='occasional',   # never/occasional/regular/heavy
            exercise_frequency='1-2/week',    # never/1-2/week/3-4/week/daily
            exercise_minutes_per_week=90,
            # 病史
            has_diabetes=False,
            has_hypertension=False,
            has_heart_disease=False,
            family_diabetes=True,             # 有家族糖尿病史（增加风险）
            family_heart_disease=False,
            family_hypertension=False,
            # 饮食习惯
            daily_fruit_vegetable=True,
            high_salt_diet=False,
        )
        db.add(profile)
        print(f"✅ 创建用户健康档案: BMI={profile.bmi}, 收缩压={profile.systolic_bp}, 总胆固醇={profile.total_cholesterol}")

        # ==================== 2. 健康指标数据 (30天) ====================
        metric_types = [
            ('heart_rate', 'bpm', 60, 100, 72),
            ('blood_pressure_sys', 'mmHg', 90, 140, 120),
            ('blood_pressure_dia', 'mmHg', 60, 90, 80),
            ('blood_sugar', 'mmol/L', 3.9, 6.1, 5.2),
            ('bmi', 'kg/m²', 18.5, 24.9, 23.5),
            ('sleep', '小时', 6, 9, 7.5),
        ]
        
        for days_ago in range(30, 0, -1):
            record_time = datetime.now() - timedelta(days=days_ago)
            for metric_type, unit, min_val, max_val, base_val in metric_types:
                # 生成有波动的数据
                if metric_type in ['heart_rate', 'blood_pressure_sys', 'blood_pressure_dia']:
                    value = base_val + random.randint(-10, 10)
                elif metric_type == 'blood_sugar':
                    value = round(base_val + random.uniform(-0.5, 0.5), 1)
                elif metric_type == 'bmi':
                    value = round(base_val + random.uniform(-0.3, 0.3), 1)
                else:
                    value = round(base_val + random.uniform(-1, 1), 1)
                
                # 判断状态
                if value < min_val or value > max_val:
                    status = 'warning'
                else:
                    status = 'normal'
                
                metric = HealthMetric(
                    user_id=user.id,
                    metric_type=metric_type,
                    value=value,
                    unit=unit,
                    status=status,
                    recorded_at=record_time
                )
                db.add(metric)
        
        print(f"✅ 创建健康指标数据: 30天 x 6种指标 = 180条记录")
        
        # ==================== 3. 健康记录 ====================
        records_data = [
            ("体检报告", "医院导入", "已分析", "low", datetime.now() - timedelta(days=2)),
            ("智能问诊", "在线咨询", "已完成", "medium", datetime.now() - timedelta(days=5)),
            ("风险评估", "自助评估", "已完成", "low", datetime.now() - timedelta(days=10)),
            ("日常监测", "手动录入", "已记录", "low", datetime.now() - timedelta(days=15)),
            ("体检报告", "医院导入", "已分析", "low", datetime.now() - timedelta(days=45)),
            ("智能问诊", "在线咨询", "已完成", "low", datetime.now() - timedelta(days=60)),
            ("日常监测", "智能手表", "已记录", "low", datetime.now() - timedelta(days=75)),
            ("风险评估", "自助评估", "已完成", "medium", datetime.now() - timedelta(days=90)),
        ]
        
        for record_type, source, status, risk, record_date in records_data:
            record = HealthRecord(
                user_id=user.id,
                record_type=record_type,
                source=source,
                status=status,
                risk_level=risk,
                record_date=record_date,
                created_at=record_date
            )
            db.add(record)
        
        print(f"✅ 创建健康记录: {len(records_data)}条")
        
        # ==================== 4. 风险评估 ====================
        assessments_data = [
            {
                "type": "cardiovascular",
                "name": "心血管疾病风险",
                "risk_level": "low",
                "score": 18,
                "factors": [
                    {"name": "血压正常", "positive": True},
                    {"name": "胆固醇偏高", "positive": False},
                    {"name": "不吸烟", "positive": True},
                    {"name": "规律运动", "positive": True},
                    {"name": "BMI正常", "positive": True},
                ],
                "recommendations": [
                    "继续保持健康的生活方式",
                    "建议定期监测胆固醇水平",
                    "每周进行150分钟中等强度运动"
                ],
                "date": datetime.now() - timedelta(days=5)
            },
            {
                "type": "diabetes",
                "name": "糖尿病风险",
                "risk_level": "medium",
                "score": 42,
                "factors": [
                    {"name": "BMI正常", "positive": True},
                    {"name": "空腹血糖偏高", "positive": False},
                    {"name": "有家族史", "positive": False},
                    {"name": "饮食习惯良好", "positive": True},
                    {"name": "运动量不足", "positive": False},
                ],
                "recommendations": [
                    "建议增加运动量，每天步行30分钟",
                    "控制碳水化合物摄入",
                    "定期监测血糖水平",
                    "建议3个月后复查"
                ],
                "date": datetime.now() - timedelta(days=15)
            },
            {
                "type": "metabolic",
                "name": "代谢综合征风险",
                "risk_level": "low",
                "score": 22,
                "factors": [
                    {"name": "腰围正常", "positive": True},
                    {"name": "血压正常", "positive": True},
                    {"name": "血糖偏高", "positive": False},
                    {"name": "血脂正常", "positive": True},
                ],
                "recommendations": [
                    "保持健康体重",
                    "注意控制血糖",
                    "定期体检"
                ],
                "date": datetime.now() - timedelta(days=30)
            }
        ]
        
        for data in assessments_data:
            assessment = RiskAssessment(
                user_id=user.id,
                assessment_type=data["type"],
                name=data["name"],
                risk_level=data["risk_level"],
                score=data["score"],
                factors=data["factors"],
                recommendations=data["recommendations"],
                assessed_at=data["date"]
            )
            db.add(assessment)
        
        print(f"✅ 创建风险评估: {len(assessments_data)}条")
        
        # ==================== 5. 问诊记录 ====================
        consultations_data = [
            {
                "session_id": "conv_20240115_001",
                "summary": "头痛症状咨询",
                "status": "已完成",
                "date": datetime.now() - timedelta(days=5),
                "messages": [
                    {"role": "assistant", "content": "您好！我是 HealthAI 智能健康助手。请描述您的症状或健康问题。"},
                    {"role": "user", "content": "最近经常头痛，特别是下午的时候"},
                    {"role": "assistant", "content": "根据您描述的头痛症状，可能与以下因素有关：\n1. 紧张性头痛 - 与压力、疲劳有关\n2. 颈椎问题 - 长期伏案工作可能导致\n\n建议：保证充足睡眠，适当休息，保持正确坐姿。如症状持续，建议就医检查。"},
                ]
            },
            {
                "session_id": "conv_20240110_002",
                "summary": "血压管理咨询",
                "status": "已完成",
                "date": datetime.now() - timedelta(days=10),
                "messages": [
                    {"role": "assistant", "content": "您好！我是 HealthAI 智能健康助手。请描述您的症状或健康问题。"},
                    {"role": "user", "content": "我的血压有点偏高，想了解如何控制"},
                    {"role": "assistant", "content": "关于血压管理，建议：\n1. 减少盐摄入（每日<6g）\n2. 规律运动（每周150分钟）\n3. 控制体重\n4. 每天固定时间测量血压\n\n如血压持续≥140/90mmHg，建议就医。"},
                ]
            },
            {
                "session_id": "conv_20240105_003",
                "summary": "睡眠问题咨询",
                "status": "已完成",
                "date": datetime.now() - timedelta(days=20),
                "messages": [
                    {"role": "assistant", "content": "您好！我是 HealthAI 智能健康助手。请描述您的症状或健康问题。"},
                    {"role": "user", "content": "最近睡眠质量不好，经常失眠"},
                    {"role": "assistant", "content": "改善睡眠建议：\n1. 固定作息时间\n2. 睡前1小时避免使用手机\n3. 保持卧室安静、黑暗\n4. 白天适当运动\n5. 避免下午3点后摄入咖啡因\n\n如长期失眠（超过1个月），建议就医。"},
                ]
            }
        ]
        
        for data in consultations_data:
            consultation = Consultation(
                user_id=user.id,
                session_id=data["session_id"],
                summary=data["summary"],
                status=data["status"],
                started_at=data["date"],
                ended_at=data["date"] + timedelta(minutes=10)
            )
            db.add(consultation)
            db.flush()
            
            for msg in data["messages"]:
                message = ConsultationMessage(
                    consultation_id=consultation.id,
                    role=msg["role"],
                    content=msg["content"],
                    created_at=data["date"]
                )
                db.add(message)
        
        print(f"✅ 创建问诊记录: {len(consultations_data)}条")
        
        # ==================== 6. 健康报告 ====================
        reports_data = [
            ("2024年度体检报告", "体检报告", datetime.now() - timedelta(days=2)),
            ("心血管风险评估报告", "风险评估", datetime.now() - timedelta(days=5)),
            ("2023年度体检报告", "体检报告", datetime.now() - timedelta(days=180)),
            ("糖尿病风险评估报告", "风险评估", datetime.now() - timedelta(days=15)),
        ]
        
        for name, report_type, date in reports_data:
            report = HealthReport(
                user_id=user.id,
                name=name,
                report_type=report_type,
                created_at=date
            )
            db.add(report)
        
        print(f"✅ 创建健康报告: {len(reports_data)}条")
        
        # ==================== 7. 健康标签 ====================
        tags_data = [
            ("血压正常", "positive"),
            ("血糖偏高", "warning"),
            ("BMI正常", "positive"),
            ("睡眠良好", "positive"),
            ("需增加运动", "neutral"),
            ("胆固醇偏高", "warning"),
        ]
        
        for name, tag_type in tags_data:
            tag = HealthTag(
                user_id=user.id,
                name=name,
                tag_type=tag_type
            )
            db.add(tag)
        
        print(f"✅ 创建健康标签: {len(tags_data)}条")
        
        # 提交所有数据
        db.commit()
        
        # ==================== 8. 穿戴设备数据 ====================
        print("\n📱 开始生成穿戴设备模拟数据...")
        seed_device_data(user_id=user.id, days=30)
        
        print("\n🎉 所有种子数据创建完成！")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 错误: {e}")
        raise
    finally:
        db.close()


if __name__ == '__main__':
    print("🌱 开始生成种子数据...\n")
    generate_seed_data()
