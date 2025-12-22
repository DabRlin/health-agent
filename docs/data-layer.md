# HealthAI 数据层设计文档

> 版本: 1.0  
> 更新日期: 2024-12-06

本文档详细说明 HealthAI 系统的数据层设计，包括穿戴设备数据采集、存储和模拟方案。

---

## 一、数据层架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                           数据采集层                                 │
├─────────────────┬─────────────────┬─────────────────────────────────┤
│   穿戴设备       │    手动录入      │       体检报告导入              │
│  (模拟/真实)     │   (前端表单)     │      (OCR/手动)                │
└────────┬────────┴────────┬────────┴────────────┬────────────────────┘
         │                 │                      │
         ▼                 ▼                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           数据存储层                                 │
├─────────────────┬─────────────────┬─────────────────────────────────┤
│ device_readings │  health_metrics │    user_health_profiles         │
│   (高频原始)     │   (日常指标)    │       (基础档案)                │
└────────┬────────┴────────┬────────┴────────────┬────────────────────┘
         │                 │                      │
         ▼                 ▼                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           数据聚合层                                 │
│                    daily_health_summaries                           │
│                       (每日汇总统计)                                 │
└─────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           数据分析层                                 │
├─────────────────┬─────────────────┬─────────────────────────────────┤
│    ML 模型      │    趋势分析      │        健康画像                 │
│   (风险评估)    │   (时序预测)     │       (综合评分)                │
└─────────────────┴─────────────────┴─────────────────────────────────┘
```

---

## 二、新增数据表

### 2.1 device_readings - 穿戴设备原始数据

存储智能穿戴设备的高频采集数据。

```sql
CREATE TABLE device_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    device_type VARCHAR(30),      -- 设备类型
    metric_type VARCHAR(30) NOT NULL,  -- 指标类型
    value REAL NOT NULL,          -- 数值
    unit VARCHAR(20),             -- 单位
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_data JSON,                -- 原始JSON数据
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_device_readings_user_time 
ON device_readings(user_id, recorded_at);
```

**字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| device_type | VARCHAR(30) | smartwatch, band, scale, blood_pressure_monitor |
| metric_type | VARCHAR(30) | heart_rate, steps, spo2, sleep, blood_pressure |
| value | REAL | 测量值 |
| unit | VARCHAR(20) | bpm, %, 步, mmHg 等 |
| raw_data | JSON | 保留原始设备数据 |

**数据量估算**:
- 心率: 每5分钟1条 → 288条/天
- 血氧: 每30分钟1条 → 48条/天
- 合计: ~336条/天/用户

### 2.2 daily_health_summaries - 每日健康汇总

存储每日聚合的健康数据，用于分析和前端展示。

```sql
CREATE TABLE daily_health_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    date VARCHAR(10) NOT NULL,    -- YYYY-MM-DD
    
    -- 心率统计
    avg_heart_rate REAL,
    min_heart_rate REAL,
    max_heart_rate REAL,
    resting_heart_rate REAL,
    
    -- 活动统计
    total_steps INTEGER,
    active_minutes INTEGER,
    calories_burned REAL,
    distance REAL,                -- 公里
    
    -- 睡眠统计
    sleep_start_time VARCHAR(5),  -- HH:MM
    sleep_end_time VARCHAR(5),
    sleep_duration REAL,          -- 小时
    deep_sleep_duration REAL,
    light_sleep_duration REAL,
    rem_duration REAL,
    awake_count INTEGER,
    sleep_quality_score INTEGER,  -- 0-100
    
    -- 血氧统计
    avg_spo2 REAL,
    min_spo2 REAL,
    
    -- 血压统计
    morning_systolic REAL,
    morning_diastolic REAL,
    evening_systolic REAL,
    evening_diastolic REAL,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(user_id, date)
);
```

### 2.3 user_health_profiles - 用户健康档案

存储用于风险评估的用户健康基础数据。

```sql
CREATE TABLE user_health_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    
    -- 身体数据
    height REAL,                  -- cm
    weight REAL,                  -- kg
    bmi REAL,
    waist REAL,                   -- cm
    
    -- 血压基线
    systolic_bp REAL,             -- mmHg
    diastolic_bp REAL,
    on_bp_medication BOOLEAN DEFAULT FALSE,
    
    -- 血液指标
    total_cholesterol REAL,       -- mg/dL
    hdl_cholesterol REAL,
    ldl_cholesterol REAL,
    triglycerides REAL,
    fasting_glucose REAL,         -- mmol/L
    hba1c REAL,                   -- %
    
    -- 生活习惯
    is_smoker BOOLEAN DEFAULT FALSE,
    smoking_years INTEGER,
    alcohol_frequency VARCHAR(20),
    exercise_frequency VARCHAR(20),
    exercise_minutes_per_week INTEGER,
    
    -- 病史
    has_diabetes BOOLEAN DEFAULT FALSE,
    has_hypertension BOOLEAN DEFAULT FALSE,
    has_heart_disease BOOLEAN DEFAULT FALSE,
    family_diabetes BOOLEAN DEFAULT FALSE,
    family_heart_disease BOOLEAN DEFAULT FALSE,
    family_hypertension BOOLEAN DEFAULT FALSE,
    
    -- 饮食
    daily_fruit_vegetable BOOLEAN DEFAULT TRUE,
    high_salt_diet BOOLEAN DEFAULT FALSE,
    
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

---

## 三、穿戴设备数据模拟器

### 3.1 模拟器设计

`device_simulator.py` 实现了符合真实生理规律的健康数据生成。

```
backend/database/device_simulator.py
├── DeviceSimulator              # 主模拟器类
│   ├── generate_heart_rate()    # 心率生成
│   ├── generate_daily_steps()   # 步数生成
│   ├── generate_sleep_data()    # 睡眠数据生成
│   ├── generate_spo2()          # 血氧生成
│   ├── generate_blood_pressure()# 血压生成
│   ├── generate_day_readings()  # 生成一天的设备读数
│   ├── generate_daily_summary() # 生成每日汇总
│   └── generate_historical_data()# 生成历史数据
├── generate_sample_health_profile()  # 生成示例健康档案
└── seed_device_data()           # 种子数据入口
```

### 3.2 心率模拟算法

```python
def generate_heart_rate(timestamp: datetime) -> float:
    """
    根据时间段生成符合生理规律的心率
    
    时间段分布:
    - 00:00-06:00 深夜睡眠: 基础心率 - 10~20 bpm
    - 06:00-08:00 起床: 基础心率 ± 5~10 bpm
    - 08:00-12:00 上午活动: 基础心率 + 0~20 bpm
    - 12:00-14:00 午餐后: 基础心率 + 5~15 bpm
    - 14:00-18:00 下午: 基础心率 + 0~15 bpm
    - 18:00-20:00 晚间: 可能运动，心率波动大
    - 20:00-24:00 休息: 逐渐降低
    """
```

**心率范围**:
- 睡眠时: 50-65 bpm
- 静息时: 60-80 bpm
- 轻度活动: 80-100 bpm
- 运动时: 100-150 bpm

### 3.3 步数模拟算法

```python
def generate_daily_steps(date: datetime) -> Dict:
    """
    生成符合日常活动规律的步数
    
    时段分布:
    - 00:00-06:00: 0-50 步 (睡眠)
    - 06:00-08:00: 200-800 步 (起床)
    - 08:00-09:00: 500-2000 步 (通勤)
    - 09:00-12:00: 100-500 步 (工作)
    - 12:00-14:00: 300-1000 步 (午餐)
    - 14:00-18:00: 100-500 步 (工作)
    - 18:00-19:00: 500-2000 步 (下班)
    - 19:00-21:00: 200-1500 步 (晚间活动)
    - 21:00-24:00: 50-300 步 (休息)
    
    周末步数 × 1.1~1.4 (更多户外活动)
    """
```

**日均步数**: 6000-12000 步

### 3.4 睡眠模拟算法

```python
def generate_sleep_data(date: datetime) -> Dict:
    """
    生成睡眠数据
    
    参数:
    - 入睡时间: 22:00-01:00
    - 睡眠时长: 5.5-8.5 小时
    
    睡眠阶段分布:
    - 深睡: 15-25%
    - REM: 20-25%
    - 浅睡: 剩余
    
    睡眠质量评分 (0-100):
    - 时长 7-8h: +20分
    - 深睡比例 ≥20%: +20分
    - 每次觉醒: -5分
    """
```

### 3.5 血氧模拟

```python
def generate_spo2(timestamp: datetime) -> float:
    """
    血氧饱和度
    - 清醒时: 96-100%
    - 睡眠时: 94-98% (略低)
    """
```

### 3.6 血压模拟

```python
def generate_blood_pressure(timestamp: datetime, has_hypertension: bool) -> Dict:
    """
    血压数据
    
    正常人:
    - 收缩压: 105-125 mmHg
    - 舒张压: 65-80 mmHg
    
    高血压患者:
    - 收缩压: 135-155 mmHg
    - 舒张压: 85-95 mmHg
    
    早晨血压略高 (+5~15 mmHg)
    """
```

---

## 四、数据生成示例

### 4.1 运行种子脚本

```bash
cd MVP/backend
source ../.venv/bin/activate
cd database
python seed.py
```

### 4.2 输出示例

```
🌱 开始生成种子数据...

🗑️ 数据库表已删除
✅ 数据库表创建完成
✅ 创建用户: 张三 (ID: 1)
✅ 创建账户: 3个
✅ 创建健康指标数据: 30天 x 6种指标 = 180条记录
✅ 创建健康记录: 8条
✅ 创建风险评估: 3条
✅ 创建问诊记录: 3条
✅ 创建健康报告: 4条
✅ 创建健康标签: 6条

📱 开始生成穿戴设备模拟数据...
✅ 已为用户 1 创建健康档案
🔄 开始为用户 1 生成 30 天的模拟数据...
  📅 2025-11-08 - 已生成 336 条读数
  📅 2025-11-15 - 已生成 336 条读数
  ...
✅ 数据生成完成！共生成 10080 条设备读数

🎉 所有种子数据创建完成！
```

### 4.3 数据统计

| 数据类型 | 数量 | 说明 |
|---------|------|------|
| 设备读数 | 10,080 条 | 30天 × 336条/天 |
| 每日汇总 | 30 条 | 每天1条 |
| 健康档案 | 1 条 | 每用户1条 |
| 健康指标 | 180 条 | 30天 × 6种指标 |

---

## 五、数据查询示例

### 5.1 获取最近7天心率趋势

```python
from database import SessionLocal, DeviceReading
from datetime import datetime, timedelta
from sqlalchemy import func

db = SessionLocal()

# 最近7天每日平均心率
seven_days_ago = datetime.now() - timedelta(days=7)

daily_hr = db.query(
    func.date(DeviceReading.recorded_at).label('date'),
    func.avg(DeviceReading.value).label('avg_hr'),
    func.min(DeviceReading.value).label('min_hr'),
    func.max(DeviceReading.value).label('max_hr')
).filter(
    DeviceReading.user_id == 1,
    DeviceReading.metric_type == 'heart_rate',
    DeviceReading.recorded_at >= seven_days_ago
).group_by(
    func.date(DeviceReading.recorded_at)
).all()

for row in daily_hr:
    print(f"{row.date}: 平均{row.avg_hr:.0f}, 范围{row.min_hr:.0f}-{row.max_hr:.0f}")
```

### 5.2 获取睡眠质量趋势

```python
from database import SessionLocal, DailyHealthSummary

db = SessionLocal()

summaries = db.query(DailyHealthSummary).filter(
    DailyHealthSummary.user_id == 1
).order_by(DailyHealthSummary.date.desc()).limit(7).all()

for s in summaries:
    print(f"{s.date}: 睡眠{s.sleep_duration:.1f}h, 质量{s.sleep_quality_score}分")
```

### 5.3 获取用户健康档案

```python
from database import SessionLocal, UserHealthProfile

db = SessionLocal()

profile = db.query(UserHealthProfile).filter(
    UserHealthProfile.user_id == 1
).first()

if profile:
    print(f"BMI: {profile.bmi}")
    print(f"血压: {profile.systolic_bp}/{profile.diastolic_bp}")
    print(f"空腹血糖: {profile.fasting_glucose}")
```

---

## 六、与 ML 模型的集成

数据层为 ML 模型提供输入数据：

```
UserHealthProfile ──────┬──────▶ Framingham (心血管)
                        │
                        ├──────▶ FINDRISC (糖尿病)
                        │
                        └──────▶ 代谢综合征评估

DailyHealthSummary ────────────▶ 趋势分析 (Phase 3)

DeviceReading ─────────────────▶ 异常检测 (Phase 3)
```

---

## 七、未来扩展

### 7.1 真实设备对接

```python
# 未来可扩展的设备接口
class DeviceConnector:
    def connect_apple_health(self):
        """对接 Apple HealthKit"""
        pass
    
    def connect_xiaomi_band(self):
        """对接小米手环"""
        pass
    
    def connect_huawei_health(self):
        """对接华为健康"""
        pass
```

### 7.2 实时数据流

```
设备 → WebSocket/MQTT → 后端 → 实时处理 → 存储
                              ↓
                         异常检测 → 告警
```

### 7.3 数据聚合任务

```python
# 定时任务：每日凌晨聚合前一天数据
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

@scheduler.scheduled_job('cron', hour=1)
def aggregate_daily_data():
    """每日1点聚合前一天的设备数据"""
    pass
```

---

## 八、文件结构

```
backend/database/
├── __init__.py           # 模块导出
├── models.py             # 数据模型定义
├── seed.py               # 种子数据脚本
├── device_simulator.py   # 穿戴设备模拟器
└── healthai.db           # SQLite 数据库文件
```
