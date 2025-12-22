# HealthAI MVP 数据库设计文档

## 概述

本项目使用 SQLite 作为数据库，SQLAlchemy 作为 ORM 框架。

- **数据库文件**: `backend/database/healthai.db`
- **ORM 模型**: `backend/database/models.py`

## 数据表结构

### 1. users - 用户表

存储用户基本信息。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 用户ID |
| name | VARCHAR(50) | NOT NULL | 姓名 |
| gender | VARCHAR(10) | | 性别 |
| age | INTEGER | | 年龄 |
| birthday | VARCHAR(20) | | 生日 |
| phone | VARCHAR(20) | | 手机号 |
| email | VARCHAR(100) | | 邮箱 |
| location | VARCHAR(100) | | 所在地 |
| avatar | VARCHAR(255) | | 头像URL |
| health_score | INTEGER | DEFAULT 80 | 健康评分 |
| created_at | DATETIME | DEFAULT NOW | 创建时间 |
| updated_at | DATETIME | DEFAULT NOW | 更新时间 |

---

### 2. health_records - 健康记录表

存储用户的健康记录（体检报告、问诊记录等）。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 记录ID |
| user_id | INTEGER | FK(users.id), NOT NULL | 用户ID |
| record_type | VARCHAR(50) | NOT NULL | 记录类型 |
| source | VARCHAR(50) | | 数据来源 |
| status | VARCHAR(20) | DEFAULT '已记录' | 状态 |
| risk_level | VARCHAR(20) | DEFAULT 'low' | 风险等级 |
| summary | TEXT | | 摘要 |
| data | JSON | | 详细数据 |
| record_date | DATETIME | DEFAULT NOW | 记录日期 |
| created_at | DATETIME | DEFAULT NOW | 创建时间 |

**record_type 枚举值**:
- `体检报告`
- `日常监测`
- `智能问诊`
- `风险评估`

**source 枚举值**:
- `医院导入`
- `手动录入`
- `智能手表`
- `在线咨询`

**risk_level 枚举值**:
- `low` - 低风险
- `medium` - 中风险
- `high` - 高风险

---

### 3. health_metrics - 健康指标表

存储用户的健康指标数据（心率、血压、血糖等）。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 指标ID |
| user_id | INTEGER | FK(users.id), NOT NULL | 用户ID |
| metric_type | VARCHAR(50) | NOT NULL | 指标类型 |
| value | FLOAT | NOT NULL | 数值 |
| unit | VARCHAR(20) | | 单位 |
| status | VARCHAR(20) | DEFAULT 'normal' | 状态 |
| recorded_at | DATETIME | DEFAULT NOW | 记录时间 |

**metric_type 枚举值**:
| 类型 | 说明 | 单位 | 正常范围 |
|------|------|------|----------|
| heart_rate | 心率 | bpm | 60-100 |
| blood_pressure_sys | 收缩压 | mmHg | 90-140 |
| blood_pressure_dia | 舒张压 | mmHg | 60-90 |
| blood_sugar | 空腹血糖 | mmol/L | 3.9-6.1 |
| bmi | BMI | kg/m² | 18.5-24.9 |
| sleep | 睡眠时长 | 小时 | 7-9 |

**status 枚举值**:
- `normal` - 正常
- `warning` - 警告
- `danger` - 危险

---

### 4. risk_assessments - 风险评估表

存储用户的健康风险评估结果。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 评估ID |
| user_id | INTEGER | FK(users.id), NOT NULL | 用户ID |
| assessment_type | VARCHAR(50) | NOT NULL | 评估类型 |
| name | VARCHAR(100) | | 评估名称 |
| risk_level | VARCHAR(20) | | 风险等级 |
| score | INTEGER | | 风险分数 |
| factors | JSON | | 风险因素 |
| recommendations | JSON | | 建议列表 |
| assessed_at | DATETIME | DEFAULT NOW | 评估时间 |

**assessment_type 枚举值**:
| 类型 | 说明 |
|------|------|
| cardiovascular | 心血管疾病风险 |
| diabetes | 糖尿病风险 |
| metabolic | 代谢综合征风险 |
| osteoporosis | 骨质疏松风险 |

**factors JSON 结构**:
```json
[
  {"name": "血压正常", "positive": true},
  {"name": "胆固醇偏高", "positive": false}
]
```

---

### 5. consultations - 问诊会话表

存储智能问诊的会话信息。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 会话ID |
| user_id | INTEGER | FK(users.id), NOT NULL | 用户ID |
| session_id | VARCHAR(50) | UNIQUE, NOT NULL | 会话标识 |
| summary | VARCHAR(200) | | 会话摘要 |
| status | VARCHAR(20) | DEFAULT '进行中' | 状态 |
| started_at | DATETIME | DEFAULT NOW | 开始时间 |
| ended_at | DATETIME | | 结束时间 |

**status 枚举值**:
- `进行中`
- `已完成`

---

### 6. consultation_messages - 问诊消息表

存储问诊会话中的消息记录。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 消息ID |
| consultation_id | INTEGER | FK(consultations.id), NOT NULL | 会话ID |
| role | VARCHAR(20) | NOT NULL | 角色 |
| content | TEXT | NOT NULL | 消息内容 |
| created_at | DATETIME | DEFAULT NOW | 创建时间 |

**role 枚举值**:
- `user` - 用户
- `assistant` - AI 助手

---

### 7. health_reports - 健康报告表

存储用户的健康报告文件信息。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 报告ID |
| user_id | INTEGER | FK(users.id), NOT NULL | 用户ID |
| name | VARCHAR(100) | NOT NULL | 报告名称 |
| report_type | VARCHAR(50) | | 报告类型 |
| file_path | VARCHAR(255) | | 文件路径 |
| data | JSON | | 报告数据 |
| created_at | DATETIME | DEFAULT NOW | 创建时间 |

---

### 8. health_tags - 健康标签表

存储用户的健康状态标签。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 标签ID |
| user_id | INTEGER | FK(users.id), NOT NULL | 用户ID |
| name | VARCHAR(50) | NOT NULL | 标签名称 |
| tag_type | VARCHAR(20) | | 标签类型 |
| created_at | DATETIME | DEFAULT NOW | 创建时间 |

**tag_type 枚举值**:
- `positive` - 正面（绿色）
- `warning` - 警告（黄色）
- `neutral` - 中性（灰色）

---

### 9. accounts - 账户表

存储用户登录认证信息。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 账户ID |
| username | VARCHAR(50) | UNIQUE, NOT NULL | 用户名 |
| password | VARCHAR(255) | NOT NULL | 密码 |
| user_id | INTEGER | FK(users.id) | 关联用户ID |
| is_active | BOOLEAN | DEFAULT TRUE | 是否激活 |
| last_login | DATETIME | | 最后登录时间 |
| created_at | DATETIME | DEFAULT NOW | 创建时间 |

---

### 10. device_readings - 穿戴设备读数表

存储智能穿戴设备的原始采集数据（高频）。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 读数ID |
| user_id | INTEGER | FK(users.id), NOT NULL | 用户ID |
| device_type | VARCHAR(30) | | 设备类型 |
| metric_type | VARCHAR(30) | NOT NULL | 指标类型 |
| value | FLOAT | NOT NULL | 数值 |
| unit | VARCHAR(20) | | 单位 |
| recorded_at | DATETIME | INDEX, DEFAULT NOW | 记录时间 |
| raw_data | JSON | | 原始JSON数据 |

**device_type 枚举值**:
- `smartwatch` - 智能手表
- `band` - 手环
- `scale` - 体脂秤
- `blood_pressure_monitor` - 血压计

**metric_type 枚举值**:
- `heart_rate` - 心率 (bpm)
- `steps` - 步数
- `spo2` - 血氧饱和度 (%)
- `sleep` - 睡眠数据
- `blood_pressure` - 血压

---

### 11. daily_health_summaries - 每日健康汇总表

存储每日聚合的健康数据，用于分析和展示。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 汇总ID |
| user_id | INTEGER | FK(users.id), NOT NULL | 用户ID |
| date | VARCHAR(10) | NOT NULL | 日期 YYYY-MM-DD |
| avg_heart_rate | FLOAT | | 平均心率 |
| min_heart_rate | FLOAT | | 最低心率 |
| max_heart_rate | FLOAT | | 最高心率 |
| resting_heart_rate | FLOAT | | 静息心率 |
| total_steps | INTEGER | | 总步数 |
| active_minutes | INTEGER | | 活动分钟数 |
| calories_burned | FLOAT | | 消耗卡路里 |
| distance | FLOAT | | 距离(公里) |
| sleep_start_time | VARCHAR(5) | | 入睡时间 HH:MM |
| sleep_end_time | VARCHAR(5) | | 起床时间 HH:MM |
| sleep_duration | FLOAT | | 睡眠时长(小时) |
| deep_sleep_duration | FLOAT | | 深睡时长(小时) |
| light_sleep_duration | FLOAT | | 浅睡时长(小时) |
| rem_duration | FLOAT | | REM时长(小时) |
| awake_count | INTEGER | | 觉醒次数 |
| sleep_quality_score | INTEGER | | 睡眠质量评分 0-100 |
| avg_spo2 | FLOAT | | 平均血氧 |
| min_spo2 | FLOAT | | 最低血氧 |
| morning_systolic | FLOAT | | 晨起收缩压 |
| morning_diastolic | FLOAT | | 晨起舒张压 |
| evening_systolic | FLOAT | | 晚间收缩压 |
| evening_diastolic | FLOAT | | 晚间舒张压 |
| created_at | DATETIME | DEFAULT NOW | 创建时间 |
| updated_at | DATETIME | DEFAULT NOW | 更新时间 |

---

### 12. user_health_profiles - 用户健康档案表

存储用于风险评估的用户健康基础数据。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PK, AUTO | 档案ID |
| user_id | INTEGER | FK(users.id), UNIQUE, NOT NULL | 用户ID |
| height | FLOAT | | 身高(cm) |
| weight | FLOAT | | 体重(kg) |
| bmi | FLOAT | | BMI |
| waist | FLOAT | | 腰围(cm) |
| systolic_bp | FLOAT | | 收缩压(mmHg) |
| diastolic_bp | FLOAT | | 舒张压(mmHg) |
| on_bp_medication | BOOLEAN | DEFAULT FALSE | 是否服用降压药 |
| total_cholesterol | FLOAT | | 总胆固醇(mg/dL) |
| hdl_cholesterol | FLOAT | | HDL胆固醇(mg/dL) |
| ldl_cholesterol | FLOAT | | LDL胆固醇(mg/dL) |
| triglycerides | FLOAT | | 甘油三酯(mg/dL) |
| fasting_glucose | FLOAT | | 空腹血糖(mmol/L) |
| hba1c | FLOAT | | 糖化血红蛋白(%) |
| is_smoker | BOOLEAN | DEFAULT FALSE | 是否吸烟 |
| smoking_years | INTEGER | | 吸烟年数 |
| alcohol_frequency | VARCHAR(20) | | 饮酒频率 |
| exercise_frequency | VARCHAR(20) | | 运动频率 |
| exercise_minutes_per_week | INTEGER | | 每周运动分钟数 |
| has_diabetes | BOOLEAN | DEFAULT FALSE | 是否有糖尿病 |
| has_hypertension | BOOLEAN | DEFAULT FALSE | 是否有高血压 |
| has_heart_disease | BOOLEAN | DEFAULT FALSE | 是否有心脏病 |
| family_diabetes | BOOLEAN | DEFAULT FALSE | 家族糖尿病史 |
| family_heart_disease | BOOLEAN | DEFAULT FALSE | 家族心脏病史 |
| family_hypertension | BOOLEAN | DEFAULT FALSE | 家族高血压史 |
| daily_fruit_vegetable | BOOLEAN | DEFAULT TRUE | 每天吃蔬果 |
| high_salt_diet | BOOLEAN | DEFAULT FALSE | 高盐饮食 |
| updated_at | DATETIME | DEFAULT NOW | 更新时间 |

---

## ER 图

```
┌─────────────┐
│   users     │
├─────────────┤
│ id (PK)     │
│ name        │
│ gender      │
│ age         │
│ ...         │
└──────┬──────┘
       │
       │ 1:N
       ├──────────────────┬──────────────────┬──────────────────┐
       │                  │                  │                  │
       ▼                  ▼                  ▼                  ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│health_records│   │health_metrics│   │risk_assessments│ │consultations│
├─────────────┤    ├─────────────┤    ├─────────────┤    ├─────────────┤
│ id (PK)     │    │ id (PK)     │    │ id (PK)     │    │ id (PK)     │
│ user_id (FK)│    │ user_id (FK)│    │ user_id (FK)│    │ user_id (FK)│
│ record_type │    │ metric_type │    │ assessment_ │    │ session_id  │
│ ...         │    │ value       │    │   type      │    │ ...         │
└─────────────┘    │ ...         │    │ ...         │    └──────┬──────┘
                   └─────────────┘    └─────────────┘           │
                                                                │ 1:N
                                                                ▼
                                                    ┌───────────────────┐
                                                    │consultation_      │
                                                    │    messages       │
                                                    ├───────────────────┤
                                                    │ id (PK)           │
                                                    │ consultation_id   │
                                                    │   (FK)            │
                                                    │ role              │
                                                    │ content           │
                                                    └───────────────────┘
```

---

## 数据库操作

### 初始化数据库

```python
from database import init_db
init_db()
```

### 生成种子数据

```bash
cd backend
python3 database/seed.py
```

### 获取数据库会话

```python
from database import SessionLocal

db = SessionLocal()
try:
    # 数据库操作
    users = db.query(User).all()
finally:
    db.close()
```

### 常用查询示例

```python
from database import User, HealthMetric, SessionLocal
from sqlalchemy import desc

db = SessionLocal()

# 获取用户
user = db.query(User).first()

# 获取最新心率
latest_hr = db.query(HealthMetric).filter(
    HealthMetric.user_id == user.id,
    HealthMetric.metric_type == 'heart_rate'
).order_by(desc(HealthMetric.recorded_at)).first()

# 获取30天内的指标
from datetime import datetime, timedelta
start_date = datetime.now() - timedelta(days=30)
metrics = db.query(HealthMetric).filter(
    HealthMetric.recorded_at >= start_date
).all()

db.close()
```

---

## 注意事项

1. SQLite 数据库文件位于 `backend/database/healthai.db`
2. 开发环境下可随时运行 `seed.py` 重置数据
3. JSON 字段在 SQLite 中以文本形式存储
4. 建议定期备份数据库文件
