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
    DeviceReading, DailyHealthSummary, UserHealthProfile, HealthKnowledge
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
                "session_id": f"conv_{(datetime.now() - timedelta(days=5)).strftime('%Y%m%d')}_001",
                "summary": "头痛症状和诊",
                "status": "已完成",
                "date": datetime.now() - timedelta(days=5),
                "messages": [
                    {"role": "assistant", "content": "您好！我是 HealthAI 智能健康助手。请描述您的症状或健康问题。"},
                    {"role": "user", "content": "最近经常头痛，特别是下午的时候"},
                    {"role": "assistant", "content": "根据您描述的头痛症状，可能与以下因素有关：\n1. 紧张性头痛 - 与压力、疲劳有关\n2. 颈椎问题 - 长期伏案工作可能导致\n\n建议：保证充足睡眠，适当休息，保持正确坐姿。如症状持续，建议就医检查。"},
                ]
            },
            {
                "session_id": f"conv_{(datetime.now() - timedelta(days=10)).strftime('%Y%m%d')}_002",
                "summary": "血压管理和诊",
                "status": "已完成",
                "date": datetime.now() - timedelta(days=10),
                "messages": [
                    {"role": "assistant", "content": "您好！我是 HealthAI 智能健康助手。请描述您的症状或健康问题。"},
                    {"role": "user", "content": "我的血压有点偏高，想了解如何控制"},
                    {"role": "assistant", "content": "关于血压管理，建议：\n1. 减少盐摄入（每日<6g）\n2. 规律运动（每周150分钟）\n3. 控制体重\n4. 每天固定时间测量血压\n\n如血压持续≥140/90mmHg，建议就医。"},
                ]
            },
            {
                "session_id": f"conv_{(datetime.now() - timedelta(days=20)).strftime('%Y%m%d')}_003",
                "summary": "睡眠问题和诊",
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
            (f"{datetime.now().year}年度体检报告", "体检报告", datetime.now() - timedelta(days=2)),
            ("心血管风险评估报告", "风险评估", datetime.now() - timedelta(days=5)),
            (f"{datetime.now().year - 1}年度体检报告", "体检报告", datetime.now() - timedelta(days=365)),
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
        
        # ==================== 7. 健康标签（用户自定义） ====================
        tags_data = [
            ("素食偏好", "neutral"),
            ("久坐办公", "warning"),
        ]
        
        for name, tag_type in tags_data:
            tag = HealthTag(
                user_id=user.id,
                name=name,
                tag_type=tag_type,
                source='user'
            )
            db.add(tag)
        
        print(f"✅ 创建用户自定义标签: {len(tags_data)}条")
        
        # 提交所有数据
        db.commit()
        
        # ==================== 8. 穿戴设备数据 ====================
        print("\n📱 开始生成穿戴设备模拟数据...")
        seed_device_data(user_id=user.id, days=30)

        # ==================== 9. 自动评估系统标签 ====================
        import sys, os
        _backend_dir = os.path.join(os.path.dirname(__file__), '..')
        sys.path.insert(0, os.path.join(_backend_dir, 'services'))
        sys.path.insert(0, _backend_dir)  # 让 auto_tag_service 能 import database
        from auto_tag_service import AutoTagService
        sys_tags = AutoTagService.evaluate_and_sync(user.id)
        sys_count = sum(1 for t in sys_tags if t['source'] == 'system')
        print(f"✅ 自动评估系统标签: {sys_count}条")

        # ==================== 10. 健康知识库 ====================
        _seed_health_knowledge(db)
        
        print("\n🎉 所有种子数据创建完成！")
        
    except Exception as e:
        db.rollback()
        print(f"❌ 错误: {e}")
        raise
    finally:
        db.close()


def _seed_health_knowledge(db):
    """预置健康知识库种子数据"""
    knowledge_items = [
        # ========== 疾病：高血压 ==========
        {
            "category": "disease", "subcategory": "cardiovascular",
            "title": "高血压（原发性高血压）",
            "keywords": "高血压,血压高,收缩压,舒张压,降压,高血压诊断标准",
            "content": (
                "高血压是指在未使用降压药的情况下，非同日3次测量血压，收缩压≥140mmHg和/或舒张压≥90mmHg。"
                "分级：1级（140-159/90-99）、2级（160-179/100-109）、3级（≥180/≥110）。"
                "危险因素：年龄、遗传、肥胖、高盐饮食、吸烟、饮酒、精神压力。"
                "并发症：冠心病、脑卒中、肾损害、视网膜病变。"
                "治疗：生活方式干预（限盐<6g/天、减重、戒烟限酒、运动）+ 药物治疗（ACEI/ARB/CCB/利尿剂/β受体阻滞剂）。"
                "目标血压：一般人群<140/90mmHg；糖尿病或慢性肾病患者<130/80mmHg。"
            ),
            "reference_data": {"normal": "<120/80", "elevated": "120-129/<80", "stage1": "130-139/80-89", "stage2": "≥140/≥90"}
        },
        # ========== 疾病：2型糖尿病 ==========
        {
            "category": "disease", "subcategory": "diabetes",
            "title": "2型糖尿病",
            "keywords": "糖尿病,血糖高,空腹血糖,糖化血红蛋白,HbA1c,胰岛素,降糖",
            "content": (
                "2型糖尿病是以慢性高血糖为特征的代谢性疾病，由胰岛素分泌不足和/或胰岛素抵抗引起。"
                "诊断标准：空腹血糖≥7.0mmol/L，或餐后2h血糖≥11.1mmol/L，或随机血糖≥11.1mmol/L伴症状，或HbA1c≥6.5%。"
                "糖尿病前期：空腹血糖6.1-6.9mmol/L（IFG），或餐后2h血糖7.8-11.0mmol/L（IGT）。"
                "危险因素：超重/肥胖（BMI≥24）、腹型肥胖、家族史、高血压、血脂异常、久坐生活方式。"
                "并发症：视网膜病变、肾病、神经病变、心血管疾病、足部溃疡。"
                "治疗目标：HbA1c<7%，空腹血糖4.4-7.0mmol/L，餐后2h血糖<10.0mmol/L。"
                "治疗：饮食控制（低GI食物）+ 运动 + 口服降糖药（二甲双胍首选）+ 胰岛素。"
            ),
            "reference_data": {"fasting_normal": "<6.1mmol/L", "fasting_prediabetes": "6.1-6.9mmol/L", "fasting_diabetes": "≥7.0mmol/L", "hba1c_normal": "<5.7%", "hba1c_prediabetes": "5.7-6.4%", "hba1c_diabetes": "≥6.5%"}
        },
        # ========== 疾病：冠心病 ==========
        {
            "category": "disease", "subcategory": "cardiovascular",
            "title": "冠心病（冠状动脉粥样硬化性心脏病）",
            "keywords": "冠心病,心绞痛,心肌梗死,胸痛,动脉粥样硬化,心脏病",
            "content": (
                "冠心病是冠状动脉粥样硬化导致管腔狭窄或阻塞，引起心肌缺血、缺氧或坏死的心脏病。"
                "主要类型：稳定型心绞痛、不稳定型心绞痛、急性心肌梗死、猝死。"
                "典型症状：胸骨后压榨性疼痛或憋闷感，可放射至左臂、下颌，持续3-5分钟，休息或含服硝酸甘油可缓解。"
                "危险因素：高血压、高血脂、糖尿病、吸烟、肥胖、家族史、年龄（男>45岁，女>55岁）。"
                "心梗预警：持续胸痛>30分钟不缓解，伴大汗、面色苍白，需立即拨打120。"
                "预防：控制危险因素、服用他汀类药物降脂、阿司匹林抗血小板（遵医嘱）、戒烟、适量运动。"
            ),
            "reference_data": None
        },
        # ========== 疾病：代谢综合征 ==========
        {
            "category": "disease", "subcategory": "metabolic",
            "title": "代谢综合征",
            "keywords": "代谢综合征,腰围,腹型肥胖,血脂异常,胰岛素抵抗",
            "content": (
                "代谢综合征是多种心血管危险因素的聚集，包括腹型肥胖、血糖升高、血压升高、血脂异常。"
                "中国诊断标准（中华医学会2013）满足以下3项或以上："
                "①腹型肥胖：腰围男性≥90cm，女性≥85cm；"
                "②高血糖：空腹血糖≥6.1mmol/L或已诊断糖尿病；"
                "③高血压：收缩压≥130或舒张压≥85mmHg或已治疗；"
                "④甘油三酯≥1.70mmol/L；"
                "⑤HDL-C降低：男性<1.04mmol/L，女性<1.30mmol/L。"
                "干预：生活方式改变是核心，减重5-10%可显著改善各项指标。"
            ),
            "reference_data": {"waist_male_limit": "90cm", "waist_female_limit": "85cm"}
        },
        # ========== 疾病：骨质疏松 ==========
        {
            "category": "disease", "subcategory": "bone",
            "title": "骨质疏松症",
            "keywords": "骨质疏松,骨密度,钙,维生素D,骨折,腰背痛",
            "content": (
                "骨质疏松是以骨量减低、骨微结构损坏为特征，导致骨脆性增加、易发骨折的全身性骨病。"
                "高危人群：老年人、绝经后女性、长期使用糖皮质激素者、低体重者、吸烟者、钙摄入不足者。"
                "症状：早期无明显症状，进展后出现腰背痛、身高变矮、驼背，严重时发生脆性骨折（髋部、脊椎、腕部）。"
                "诊断：DXA骨密度检测，T值≤-2.5SD诊断为骨质疏松。"
                "预防与治疗：充足钙摄入（成人1000mg/天，老年人1200mg/天）、维生素D（800-1200IU/天）、"
                "负重运动、防跌倒、戒烟限酒。药物：双膦酸盐、地舒单抗（遵医嘱）。"
            ),
            "reference_data": {"t_score_normal": ">-1.0", "t_score_low_bone_mass": "-2.5 to -1.0", "t_score_osteoporosis": "≤-2.5"}
        },
        # ========== 指标：血压参考范围 ==========
        {
            "category": "indicator", "subcategory": "cardiovascular",
            "title": "血压参考范围与分级",
            "keywords": "血压,收缩压,舒张压,血压正常值,血压标准",
            "content": (
                "血压分级（中国高血压指南2018）："
                "正常血压：收缩压<120mmHg 且 舒张压<80mmHg；"
                "正常高值：收缩压120-139mmHg 和/或 舒张压80-89mmHg；"
                "1级高血压：收缩压140-159mmHg 和/或 舒张压90-99mmHg；"
                "2级高血压：收缩压160-179mmHg 和/或 舒张压100-109mmHg；"
                "3级高血压：收缩压≥180mmHg 和/或 舒张压≥110mmHg。"
                "测量注意：安静休息5分钟后测量，取坐位，连续测2次取平均值。"
                "家庭自测目标值：<135/85mmHg。"
            ),
            "reference_data": {"normal": "<120/80", "elevated": "120-139/80-89", "stage1": "140-159/90-99", "stage2": "160-179/100-109", "stage3": "≥180/≥110"}
        },
        # ========== 指标：血糖参考范围 ==========
        {
            "category": "indicator", "subcategory": "diabetes",
            "title": "血糖参考范围",
            "keywords": "血糖,空腹血糖,餐后血糖,糖化血红蛋白,血糖正常值",
            "content": (
                "空腹血糖（FPG，禁食8h以上）：正常<6.1mmol/L；"
                "糖尿病前期（IFG）：6.1-6.9mmol/L；糖尿病：≥7.0mmol/L。"
                "餐后2小时血糖：正常<7.8mmol/L；糖耐量减低（IGT）：7.8-11.0mmol/L；糖尿病：≥11.1mmol/L。"
                "随机血糖：正常<7.8mmol/L（参考）；伴症状时≥11.1mmol/L可诊断糖尿病。"
                "糖化血红蛋白（HbA1c，反映3个月平均血糖）：正常<5.7%；前期5.7-6.4%；糖尿病≥6.5%；"
                "糖尿病控制目标<7%（一般人群），<8%（老年/低血糖风险高者）。"
            ),
            "reference_data": {"fasting_normal": "<6.1mmol/L", "fasting_ifg": "6.1-6.9mmol/L", "fasting_dm": "≥7.0mmol/L", "pp2h_normal": "<7.8mmol/L", "pp2h_igt": "7.8-11.0mmol/L", "hba1c_target": "<7%"}
        },
        # ========== 指标：血脂参考范围 ==========
        {
            "category": "indicator", "subcategory": "lipid",
            "title": "血脂参考范围",
            "keywords": "血脂,胆固醇,甘油三酯,低密度脂蛋白,高密度脂蛋白,LDL,HDL,TC",
            "content": (
                "总胆固醇（TC）：合适水平<5.2mmol/L；边缘升高5.2-6.19mmol/L；升高≥6.2mmol/L。"
                "低密度脂蛋白胆固醇（LDL-C，'坏胆固醇'）：合适<3.4mmol/L；边缘3.4-4.09mmol/L；升高≥4.1mmol/L。"
                "高密度脂蛋白胆固醇（HDL-C，'好胆固醇'）：男性≥1.0mmol/L，女性≥1.3mmol/L为合适；<1.0mmol/L为降低。"
                "甘油三酯（TG）：正常<1.7mmol/L；边缘1.7-2.25mmol/L；升高≥2.26mmol/L；极高≥5.65mmol/L。"
                "LDL-C 目标值（因人而异）：极高危患者<1.8mmol/L；高危<2.6mmol/L；中低危<3.4mmol/L。"
            ),
            "reference_data": {"TC_normal": "<5.2mmol/L", "LDL_normal": "<3.4mmol/L", "HDL_male_normal": "≥1.0mmol/L", "TG_normal": "<1.7mmol/L"}
        },
        # ========== 指标：BMI ==========
        {
            "category": "indicator", "subcategory": "body",
            "title": "BMI（身体质量指数）参考范围",
            "keywords": "BMI,体重指数,肥胖,超重,体重,身高",
            "content": (
                "BMI = 体重(kg) / 身高²(m²)。"
                "中国标准：偏低<18.5；正常18.5-23.9；超重24-27.9；肥胖≥28。"
                "世卫组织（WHO）标准：偏低<18.5；正常18.5-24.9；超重25-29.9；肥胖≥30。"
                "腹型肥胖（内脏脂肪风险更大）：腰围男性≥90cm，女性≥85cm。"
                "BMI与健康风险：BMI≥28时，高血压、糖尿病、血脂异常风险显著增加。"
                "建议将BMI维持在18.5-23.9之间，腰围控制在正常范围内。"
            ),
            "reference_data": {"underweight": "<18.5", "normal": "18.5-23.9", "overweight": "24-27.9", "obese": "≥28"}
        },
        # ========== 指标：心率 ==========
        {
            "category": "indicator", "subcategory": "cardiovascular",
            "title": "心率参考范围",
            "keywords": "心率,脉搏,静息心率,心跳,正常心率",
            "content": (
                "正常静息心率：60-100次/分钟（成人）。"
                "心动过缓：<60次/分钟，运动员可低至40-50次（属于生理性）。"
                "心动过速：>100次/分钟，可能由发热、贫血、甲亢、焦虑、心律失常等引起。"
                "目标心率（运动）：最大心率约为220-年龄；有氧运动目标心率为最大心率的50-85%。"
                "静息心率偏高（>80次/分钟）是心血管风险增加的独立危险因素。"
                "建议：若静息心率持续>100次/分钟，或出现心悸、胸闷，应就医检查。"
            ),
            "reference_data": {"resting_normal": "60-100 bpm", "bradycardia": "<60 bpm", "tachycardia": ">100 bpm"}
        },
        # ========== 饮食：高血压饮食 ==========
        {
            "category": "diet", "subcategory": "cardiovascular",
            "title": "高血压饮食建议（DASH饮食）",
            "keywords": "高血压饮食,限盐,DASH饮食,降压饮食,低钠",
            "content": (
                "DASH饮食（控制高血压的饮食方法）核心原则："
                "①限制钠盐：每日<6g食盐（约2400mg钠），理想<3g（<1200mg钠）；"
                "②增加钾摄入：多吃香蕉、菠菜、土豆、豆类（有助拮抗钠的升压效果）；"
                "③增加钙镁：低脂乳制品、绿叶蔬菜、坚果；"
                "④多蔬果：每日7-8份蔬菜水果；"
                "⑤选择全谷物：燕麦、糙米代替精白米面；"
                "⑥控制饱和脂肪和反式脂肪；"
                "⑦限制饮酒：男性<25g/天，女性<15g/天（酒精量）。"
                "注意：酱油、腌制食品、加工食品含盐量高，需注意隐性盐。"
            ),
            "reference_data": None
        },
        # ========== 饮食：糖尿病饮食 ==========
        {
            "category": "diet", "subcategory": "diabetes",
            "title": "糖尿病饮食管理",
            "keywords": "糖尿病饮食,低GI食物,控糖,碳水化合物,血糖指数",
            "content": (
                "糖尿病饮食核心原则："
                "①控制总热量：根据体重和活动量计算，避免超重；"
                "②低血糖生成指数（低GI）食物优先：全谷物、豆类、蔬菜（GI<55）；"
                "③分配碳水化合物：占总热量45-60%，每餐定量，避免大量集中摄入；"
                "④增加膳食纤维：≥25-30g/天，有助延缓糖吸收；"
                "⑤控制升糖食物：白米饭、白面包、甜点、果汁、含糖饮料需限制；"
                "⑥优质蛋白：鱼、禽、蛋、豆制品为主；"
                "⑦健康脂肪：橄榄油、坚果，减少饱和脂肪；"
                "⑧规律进餐：定时定量，避免暴饮暴食。"
                "常见高GI食物：白面包(75)、白米饭(72)、土豆泥(87)；"
                "常见低GI食物：燕麦片(55)、豆类(30)、苹果(38)。"
            ),
            "reference_data": None
        },
        # ========== 饮食：心血管健康饮食 ==========
        {
            "category": "diet", "subcategory": "cardiovascular",
            "title": "心血管健康饮食建议",
            "keywords": "心脏健康饮食,降脂饮食,地中海饮食,胆固醇饮食",
            "content": (
                "心血管健康饮食（参考地中海饮食）："
                "①增加Omega-3脂肪酸：深海鱼（三文鱼、沙丁鱼）每周≥2次，亚麻籽、核桃；"
                "②减少饱和脂肪：红肉、全脂乳制品、棕榈油、椰子油；"
                "③禁止反式脂肪：人造黄油、油炸快餐、部分饼干点心；"
                "④增加可溶性膳食纤维：燕麦、大麦、豆类（可降低LDL-C）；"
                "⑤植物固醇：每天2g（某些强化食品）可降低LDL-C约10%；"
                "⑥限制胆固醇摄入：蛋黄（每周3-4个）、动物内脏少吃；"
                "⑦多吃蔬菜水果：每日≥500g，富含抗氧化物质。"
            ),
            "reference_data": None
        },
        # ========== 运动：有氧运动指南 ==========
        {
            "category": "lifestyle", "subcategory": "exercise",
            "title": "成人有氧运动指南",
            "keywords": "有氧运动,运动建议,运动频率,步行,跑步,运动量",
            "content": (
                "WHO成人体力活动建议（18-64岁）："
                "①每周至少150-300分钟中等强度有氧活动，或75-150分钟高强度有氧活动；"
                "②中等强度：快走（5-6km/h）、骑行、游泳、广场舞；心率约最大心率的50-70%；"
                "③高强度：跑步、跳绳、快速骑行；心率约最大心率的70-85%；"
                "④每周≥2天肌肉强化活动（抗阻训练）；"
                "⑤减少久坐，每坐1小时起身活动5分钟。"
                "高血压患者：推荐中等强度有氧运动，避免高强度举重，运动时血压<160/100方可进行。"
                "糖尿病患者：餐后1小时运动效果最佳（降低餐后血糖），避免空腹运动（低血糖风险）。"
                "计步目标：每天6000-10000步。"
            ),
            "reference_data": None
        },
        # ========== 运动：糖尿病运动 ==========
        {
            "category": "lifestyle", "subcategory": "diabetes",
            "title": "糖尿病运动管理",
            "keywords": "糖尿病运动,运动降血糖,低血糖,运动时机",
            "content": (
                "糖尿病运动建议："
                "①最佳时机：餐后1-1.5小时开始运动（降低餐后血糖峰值效果最好）；"
                "②避免空腹运动：防止低血糖（尤其使用胰岛素或磺脲类药物者）；"
                "③运动前检测血糖：<5.6mmol/L需补充碳水后再运动；>16.7mmol/L暂缓运动；"
                "④推荐：快走、游泳、骑车、太极、抗阻训练（改善胰岛素敏感性）；"
                "⑤每次运动30-60分钟，每周5天；"
                "⑥携带含糖食品以备低血糖急救；"
                "⑦穿合适鞋袜，运动后检查足部。"
            ),
            "reference_data": None
        },
        # ========== 生活方式：睡眠 ==========
        {
            "category": "lifestyle", "subcategory": "sleep",
            "title": "睡眠健康建议",
            "keywords": "睡眠,失眠,睡眠质量,睡眠时间,睡眠障碍",
            "content": (
                "推荐睡眠时长：成人7-9小时/天，老年人7-8小时/天。"
                "睡眠不足（<6小时）危害：增加肥胖、糖尿病、高血压、心脏病、抑郁风险，降低免疫力。"
                "睡眠卫生建议："
                "①固定作息：每天同一时间入睡和起床（包括周末）；"
                "②卧室环境：黑暗、安静、凉爽（18-22°C）；"
                "③睡前1小时：避免蓝光（手机、电脑）、咖啡因、剧烈运动、大量进食；"
                "④白天限制小睡：≤30分钟，下午3点后避免；"
                "⑤规律运动有助于睡眠，但避免睡前2小时剧烈运动；"
                "⑥睡前放松：温水浴、冥想、轻柔伸展。"
                "长期失眠：建议就医，首选认知行为疗法（CBT-I），而非长期依赖安眠药。"
            ),
            "reference_data": {"adult_recommended": "7-9 hours", "elderly_recommended": "7-8 hours"}
        },
        # ========== 生活方式：吸烟 ==========
        {
            "category": "lifestyle", "subcategory": "smoking",
            "title": "吸烟危害与戒烟",
            "keywords": "吸烟,戒烟,烟草,尼古丁,二手烟",
            "content": (
                "吸烟危害：吸烟是心血管疾病、肺癌、COPD、口腔癌等多种疾病的主要危险因素。"
                "吸烟使冠心病风险增加2-4倍，脑卒中风险增加2-3倍。"
                "戒烟效果（戒烟后时间线）："
                "20分钟：血压和心率下降；"
                "12小时：血液中CO恢复正常；"
                "1年：冠心病风险降低50%；"
                "5年：脑卒中风险接近非吸烟者；"
                "10年：肺癌死亡风险降低50%。"
                "戒烟方法：尼古丁替代疗法（贴片/口香糖）、处方药（伐尼克兰/安非他酮）、心理行为支持。"
                "戒断症状：烦躁、焦虑、注意力不集中通常在1-2周内最强，逐渐减轻。"
            ),
            "reference_data": None
        },
        # ========== 药物：二甲双胍 ==========
        {
            "category": "drug", "subcategory": "diabetes",
            "title": "二甲双胍",
            "keywords": "二甲双胍,降糖药,格华止,metformin,糖尿病用药",
            "content": (
                "二甲双胍是2型糖尿病一线首选药物，属于双胍类降糖药。"
                "作用机制：抑制肝脏葡萄糖输出，改善外周胰岛素敏感性。"
                "优点：不引起低血糖（单独使用）、可轻度减重、心血管保护证据充分、价格低廉。"
                "常见副作用：恶心、腹胀、腹泻（多为初始用药，餐中/餐后服用可减轻）。"
                "禁忌：eGFR<30（肾功能严重不全）；进行含碘造影剂检查前48h需暂停。"
                "使用注意：从小剂量开始（500mg/天）逐渐增加；定期监测肾功能（每年1次）。"
                "注意：具体用药方案须遵医嘱，切勿自行调整剂量。"
            ),
            "reference_data": None
        },
        # ========== 药物：他汀类 ==========
        {
            "category": "drug", "subcategory": "cardiovascular",
            "title": "他汀类药物（降脂药）",
            "keywords": "他汀,降脂药,阿托伐他汀,瑞舒伐他汀,辛伐他汀,胆固醇药",
            "content": (
                "他汀类药物（HMG-CoA还原酶抑制剂）是最常用的降脂药，主要降低LDL-C（坏胆固醇）。"
                "常用药物：阿托伐他汀、瑞舒伐他汀、辛伐他汀、匹伐他汀等。"
                "主要作用：降低LDL-C（25-55%）、轻度降低TG、轻度升高HDL-C；抗动脉粥样硬化。"
                "最佳服用时间：多数他汀晚上服用（夜间胆固醇合成最旺盛）；阿托伐他汀任意时间均可。"
                "常见副作用：肌肉酸痛（肌病）、转氨酶升高（约1-3%），需定期监测肝功能和CK。"
                "禁忌：活动性肝病、妊娠/哺乳、与某些药物相互作用（需告知医生所有用药）。"
                "注意：任何降脂药物须在医生指导下使用，不可自行增减剂量或停药。"
            ),
            "reference_data": None
        },
        # ========== 药物：降压药 ==========
        {
            "category": "drug", "subcategory": "cardiovascular",
            "title": "常用降压药分类",
            "keywords": "降压药,ACEI,ARB,钙拮抗剂,利尿剂,β受体阻滞剂,血压药",
            "content": (
                "五大类常用降压药："
                "①ACEI（普利类）：卡托普利、依那普利、培哚普利；保护肾脏，适合糖尿病/肾病；副作用：干咳。"
                "②ARB（沙坦类）：氯沙坦、缬沙坦、厄贝沙坦；与ACEI类似但无干咳；不能与ACEI联用。"
                "③钙通道拮抗剂（CCB）：氨氯地平、硝苯地平；适合老年人和单纯收缩期高血压；副作用：踝部水肿。"
                "④利尿剂：氢氯噻嗪、吲达帕胺；价格便宜，常作联合用药；注意监测血钾。"
                "⑤β受体阻滞剂：美托洛尔、比索洛尔；适合合并冠心病/心衰者；不适合哮喘患者。"
                "注意：降压药需长期规律服药，不可因血压正常就自行停药，具体用药遵医嘱。"
            ),
            "reference_data": None
        },
        # ========== 症状：胸痛 ==========
        {
            "category": "symptom", "subcategory": "cardiovascular",
            "title": "胸痛的常见原因与鉴别",
            "keywords": "胸痛,心绞痛,心肌梗死,胸闷,胸部疼痛",
            "content": (
                "胸痛常见原因及特点："
                "①心绞痛：胸骨后压榨感/憋闷，活动/情绪激动诱发，持续3-5分钟，休息或硝酸甘油可缓解。"
                "②急性心肌梗死：持续性剧烈胸痛>30分钟不缓解，可伴大汗淋漓、恶心呕吐、面色苍白——【紧急：立即拨打120】。"
                "③主动脉夹层：撕裂样剧痛，可放射至背部/腹部，血压两侧不等——【紧急：立即就医】。"
                "④肺栓塞：突发胸痛伴呼吸困难、咯血，有近期制动/手术/肿瘤史——【紧急就医】。"
                "⑤气胸：突发单侧胸痛伴呼吸困难——【急诊就医】。"
                "⑥食管反流：烧灼感，餐后或平卧加重，抗酸药可缓解。"
                "⑦肋软骨炎：局部压痛，与活动相关，非心脏来源。"
                "重要提示：不明原因胸痛，尤其伴有呼吸困难、出冷汗、放射痛者，应立即就医！"
            ),
            "reference_data": None
        },
        # ========== 症状：头晕 ==========
        {
            "category": "symptom", "subcategory": "general",
            "title": "头晕的常见原因",
            "keywords": "头晕,眩晕,低血压,低血糖,耳石症",
            "content": (
                "头晕常见原因："
                "①体位性低血压：突然站起时头晕，血压骤降所致，见于老年人、脱水、降压药过量；"
                "②良性阵发性位置性眩晕（BPPV/耳石症）：改变头位时短暂旋转感，可通过耳石复位治疗；"
                "③低血糖：头晕、乏力、出冷汗、心慌，多见于糖尿病患者用药过量或未按时进食；"
                "④高血压：血压急剧升高可引起头晕、头痛；"
                "⑤贫血：慢性头晕伴乏力、面色苍白；"
                "⑥心律失常：心悸伴头晕，需心电图检查；"
                "⑦颈椎病：颈部转动后头晕；"
                "⑧脑供血不足/TIA（短暂性脑缺血发作）：突发头晕伴肢体无力/言语障碍——【紧急就医】。"
            ),
            "reference_data": None
        },
        # ========== 症状：多饮多尿 ==========
        {
            "category": "symptom", "subcategory": "diabetes",
            "title": "多饮、多尿、多食、体重下降",
            "keywords": "多饮,多尿,多食,消瘦,糖尿病症状,三多一少",
            "content": (
                "\"三多一少\"（多饮、多尿、多食、体重下降）是糖尿病的典型症状，但多数2型糖尿病早期症状不明显。"
                "多尿机制：高血糖导致渗透性利尿，尿量可达3-5升/天甚至更多。"
                "多饮：多尿导致脱水，刺激口渴中枢。"
                "多食：胰岛素不足导致细胞无法利用葡萄糖，产生饥饿感。"
                "体重下降：脂肪和蛋白质分解供能。"
                "其他糖尿病症状：视物模糊、伤口愈合慢、反复皮肤感染、手脚麻木刺痛（神经病变）。"
                "注意：出现多饮多尿症状应及时检测空腹血糖和餐后血糖，早期发现早期干预。"
            ),
            "reference_data": None
        },
        # ========== 疾病：高脂血症 ==========
        {
            "category": "disease", "subcategory": "lipid",
            "title": "高脂血症（血脂异常）",
            "keywords": "高脂血症,高胆固醇,高甘油三酯,血脂异常,动脉粥样硬化",
            "content": (
                "血脂异常包括：高胆固醇血症（TC升高）、高甘油三酯血症（TG升高）、"
                "混合型高脂血症（TC和TG均升高）、低HDL-C血症。"
                "危害：LDL-C是动脉粥样硬化的核心因素，是冠心病、脑卒中的主要危险因素。"
                "继发原因：甲状腺功能减退、肾病综合征、糖尿病、肝病等可引起继发性血脂异常。"
                "治疗："
                "生活方式：低脂低糖饮食、增加运动、减重、戒烟限酒（TG对生活方式干预最敏感）；"
                "药物：他汀类（降LDL-C首选）、贝特类（降TG）、依折麦布（联合降LDL-C）。"
                "监测：血脂正常者每3-5年检查一次；异常者治疗后每3-6个月复查。"
            ),
            "reference_data": None
        },
        # ========== 生活方式：压力与心理健康 ==========
        {
            "category": "lifestyle", "subcategory": "mental",
            "title": "心理健康与压力管理",
            "keywords": "压力,焦虑,抑郁,心理健康,减压,情绪管理",
            "content": (
                "长期心理压力对健康的影响：升高血压、扰乱血糖调节、损害免疫系统、增加心脏病风险。"
                "压力管理方法："
                "①规律运动：是最有循证依据的减压方式，运动产生内啡肽改善情绪；"
                "②正念冥想：每天10-20分钟，降低皮质醇水平；"
                "③充足睡眠：睡眠不足会放大压力反应；"
                "④社交支持：保持与家人朋友的联系；"
                "⑤时间管理：合理规划任务，减少拖延；"
                "⑥呼吸练习：4-7-8呼吸法（吸气4秒，屏气7秒，呼气8秒）快速缓解紧张。"
                "焦虑/抑郁症状持续≥2周并影响日常生活，建议就医进行专业评估和治疗。"
            ),
            "reference_data": None
        },
        # ========== 饮食：减重饮食 ==========
        {
            "category": "diet", "subcategory": "weight",
            "title": "科学减重饮食建议",
            "keywords": "减肥,减重,热量赤字,低卡饮食,体重管理",
            "content": (
                "科学减重原则："
                "①热量赤字：每天摄入比消耗少500-750kcal，可实现每周减重0.5-0.75kg（健康减重速率）；"
                "②不建议极低热量饮食（<800kcal/天）：导致肌肉流失、代谢下降；"
                "③足够蛋白质：每公斤体重1.2-1.6g（约占总热量25-30%），减重期间保留肌肉；"
                "④减少精制碳水：白米饭、白面、甜饮料、点心是主要\"空热量\"来源；"
                "⑤增加膳食纤维：蔬菜、豆类增加饱腹感；"
                "⑥规律进餐：避免不吃早饭导致午晚饭暴食；"
                "⑦配合抗阻训练：增加肌肉量，提升基础代谢率。"
                "减重5-10%即可显著改善血压、血糖、血脂、睡眠呼吸暂停。"
            ),
            "reference_data": None
        },
        # ========== 体检项目解读：血常规 ==========
        {
            "category": "indicator", "subcategory": "blood_routine",
            "title": "血常规主要指标解读",
            "keywords": "血常规,白细胞,红细胞,血红蛋白,血小板,WBC,RBC,HGB,PLT",
            "content": (
                "血常规主要指标参考范围（成人）："
                "白细胞（WBC）：4-10×10⁹/L；升高见于感染、炎症；降低见于病毒感染、药物影响。"
                "红细胞（RBC）：男性4.5-5.5×10¹²/L，女性3.8-4.8×10¹²/L。"
                "血红蛋白（HGB）：男性130-175g/L，女性115-150g/L；低于正常为贫血。"
                "贫血分级：轻度90-正常下限；中度60-90；重度30-60；极重度<30（单位g/L）。"
                "血小板（PLT）：100-300×10⁹/L；<100为血小板减少（出血风险）；>400为增多。"
                "中性粒细胞比例：50-70%；升高提示细菌感染；降低见于病毒感染。"
                "淋巴细胞比例：20-40%；升高见于病毒感染；严重降低见于免疫缺陷。"
            ),
            "reference_data": {"WBC": "4-10×10⁹/L", "HGB_male": "130-175g/L", "HGB_female": "115-150g/L", "PLT": "100-300×10⁹/L"}
        },
        # ========== 体检项目解读：肝功能 ==========
        {
            "category": "indicator", "subcategory": "liver",
            "title": "肝功能主要指标解读",
            "keywords": "肝功能,转氨酶,ALT,AST,胆红素,白蛋白,肝功能异常",
            "content": (
                "肝功能主要指标参考范围："
                "丙氨酸氨基转移酶（ALT）：0-40U/L；升高见于肝炎、脂肪肝、药物性肝损伤；>3倍正常上限需关注。"
                "天冬氨酸氨基转移酶（AST）：0-40U/L；心肌损伤时也升高（AST/ALT>2提示心脏来源）。"
                "总胆红素（TBIL）：5-21μmol/L；升高见于溶血性贫血、肝病、胆道梗阻。"
                "白蛋白（ALB）：35-55g/L；降低见于肝硬化、肾病综合征、营养不良。"
                "碱性磷酸酶（ALP）：40-150U/L；升高见于胆道疾病、骨病。"
                "γ-谷氨酰转肽酶（GGT）：0-60U/L；对酒精性肝病和胆道疾病敏感。"
                "注意：转氨酶轻度升高（<3倍）需复查，追踪是否持续；明显升高须就医查明原因。"
            ),
            "reference_data": {"ALT": "0-40U/L", "AST": "0-40U/L", "TBIL": "5-21μmol/L", "ALB": "35-55g/L"}
        },
        # ========== 体检项目解读：肾功能 ==========
        {
            "category": "indicator", "subcategory": "kidney",
            "title": "肾功能主要指标解读",
            "keywords": "肾功能,肌酐,尿素氮,尿酸,eGFR,肾功能异常",
            "content": (
                "肾功能主要指标参考范围："
                "血清肌酐（Scr）：男性57-111μmol/L，女性45-84μmol/L；升高提示肾功能受损。"
                "估算肾小球滤过率（eGFR）：正常≥90mL/min/1.73m²；<60持续3个月以上诊断慢性肾病。"
                "慢性肾病分期：G1(≥90)、G2(60-89)、G3a(45-59)、G3b(30-44)、G4(15-29)、G5(<15/透析)。"
                "血尿素氮（BUN）：2.9-7.1mmol/L；受蛋白质摄入影响，特异性低于肌酐。"
                "尿酸（UA）：男性200-416μmol/L，女性142-340μmol/L；>420（男）/360（女）为高尿酸血症，痛风风险。"
                "糖尿病/高血压患者：建议每年检查肾功能和尿微量白蛋白。"
            ),
            "reference_data": {"Scr_male": "57-111μmol/L", "Scr_female": "45-84μmol/L", "eGFR_normal": "≥90mL/min/1.73m²", "UA_male": "200-416μmol/L"}
        },
    ]

    count = 0
    for item in knowledge_items:
        k = HealthKnowledge(
            category=item["category"],
            subcategory=item.get("subcategory"),
            title=item["title"],
            keywords=item.get("keywords"),
            content=item["content"],
            reference_data=item.get("reference_data"),
        )
        db.add(k)
        count += 1
    db.commit()
    print(f"✅ 健康知识库种子数据: {count}条")


if __name__ == '__main__':
    print("🌱 开始生成种子数据...\n")
    generate_seed_data()
