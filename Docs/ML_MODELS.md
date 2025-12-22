# HealthAI ML 模型文档

> 版本: 1.0  
> 更新日期: 2024-12-06

本文档详细说明 HealthAI 系统中使用的机器学习模型和风险评估算法。

---

## 一、模型概览

| 模型 | 评估目标 | 算法来源 | 输出 |
|------|---------|---------|------|
| Framingham Risk Score | 心血管疾病风险 | Framingham Heart Study (2008) | 10年风险概率 |
| FINDRISC | 2型糖尿病风险 | Finnish Diabetes Risk Score | 风险评分 (0-26) |
| 代谢综合征评估 | 代谢综合征诊断 | IDF/NCEP ATP III 标准 | 是否患病 + 风险等级 |

---

## 二、心血管疾病风险评估

### 2.1 算法说明

**Framingham Risk Score** 是基于美国 Framingham Heart Study 的经典心血管风险评估公式，用于预测未来 10 年内发生心血管事件（心肌梗死、冠心病死亡、中风等）的概率。

**参考文献**:
> D'Agostino RB Sr, et al. General cardiovascular risk profile for use in primary care. Circulation. 2008;117(6):743-753.

### 2.2 输入参数

| 参数 | 类型 | 范围 | 说明 |
|------|------|------|------|
| age | int | 30-79 | 年龄 |
| gender | str | 男/女 | 性别 |
| total_cholesterol | float | mg/dL | 总胆固醇 |
| hdl_cholesterol | float | mg/dL | HDL胆固醇 |
| systolic_bp | float | mmHg | 收缩压 |
| on_bp_medication | bool | - | 是否服用降压药 |
| is_smoker | bool | - | 是否吸烟 |
| has_diabetes | bool | - | 是否有糖尿病 |

### 2.3 计算公式

```
风险 = 1 - S₀^exp(ΣβᵢXᵢ - M)

其中:
- S₀: 基线生存率 (男性 0.88936, 女性 0.95012)
- βᵢ: 各因素系数
- Xᵢ: 各因素值（对数变换）
- M: 平均系数和
```

**男性系数**:
| 因素 | 系数 |
|------|------|
| ln(年龄) | 3.06117 |
| ln(总胆固醇) | 1.12370 |
| ln(HDL) | -0.93263 |
| ln(收缩压-未治疗) | 1.93303 |
| ln(收缩压-治疗中) | 1.99881 |
| 吸烟 | 0.65451 |
| 糖尿病 | 0.57367 |

**女性系数**:
| 因素 | 系数 |
|------|------|
| ln(年龄) | 2.32888 |
| ln(总胆固醇) | 1.20904 |
| ln(HDL) | -0.70833 |
| ln(收缩压-未治疗) | 2.76157 |
| ln(收缩压-治疗中) | 2.82263 |
| 吸烟 | 0.52873 |
| 糖尿病 | 0.69154 |

### 2.4 风险等级划分

| 10年风险 | 等级 | 说明 |
|---------|------|------|
| < 10% | low | 低风险 |
| 10-20% | medium | 中风险 |
| ≥ 20% | high | 高风险 |

### 2.5 使用示例

```python
from services.ml_models.cardiovascular import calculate_cardiovascular_risk

result = calculate_cardiovascular_risk(
    age=55,
    gender='男',
    total_cholesterol=240,
    hdl_cholesterol=45,
    systolic_bp=140,
    on_bp_medication=True,
    is_smoker=False,
    has_diabetes=False
)

print(f"10年风险: {result['risk_percentage']}%")
print(f"风险等级: {result['risk_level']}")
```

---

## 三、糖尿病风险评估

### 3.1 算法说明

**FINDRISC (Finnish Diabetes Risk Score)** 是芬兰开发的糖尿病风险评分工具，用于评估未来 10 年内发生 2 型糖尿病的风险，无需实验室检查即可完成评估。

**参考文献**:
> Lindström J, Tuomilehto J. The diabetes risk score: a practical tool to predict type 2 diabetes risk. Diabetes Care. 2003;26(3):725-731.

### 3.2 评分标准

| 因素 | 条件 | 得分 |
|------|------|------|
| **年龄** | < 45岁 | 0 |
| | 45-54岁 | 2 |
| | 55-64岁 | 3 |
| | ≥ 65岁 | 4 |
| **BMI** | < 25 | 0 |
| | 25-30 | 1 |
| | > 30 | 3 |
| **腰围(男)** | < 94cm | 0 |
| | 94-102cm | 3 |
| | > 102cm | 4 |
| **腰围(女)** | < 80cm | 0 |
| | 80-88cm | 3 |
| | > 88cm | 4 |
| **每日运动** | 是 | 0 |
| | 否 | 2 |
| **每日蔬果** | 是 | 0 |
| | 否 | 1 |
| **降压药** | 否 | 0 |
| | 是 | 2 |
| **高血糖史** | 否 | 0 |
| | 是 | 5 |
| **家族史** | 无 | 0 |
| | 二级亲属 | 3 |
| | 一级亲属 | 5 |

**总分范围: 0-26 分**

### 3.3 风险等级划分

| 总分 | 等级 | 10年风险 | 说明 |
|------|------|---------|------|
| < 7 | low | ~1% | 低风险 |
| 7-11 | low | ~4% | 轻度风险 |
| 12-14 | medium | ~17% | 中度风险 |
| 15-20 | high | ~33% | 高风险 |
| > 20 | high | ~50% | 极高风险 |

### 3.4 使用示例

```python
from services.ml_models.diabetes import calculate_diabetes_risk

result = calculate_diabetes_risk(
    age=50,
    bmi=28,
    waist=95,
    gender='男',
    on_bp_medication=True,
    history_high_glucose=False,
    daily_physical_activity=False,
    daily_fruit_vegetable=True,
    family_diabetes='first_degree'
)

print(f"总分: {result['total_score']}/26")
print(f"10年风险: {result['risk_percentage']}%")
print(f"风险等级: {result['risk_level']}")
```

---

## 四、代谢综合征评估

### 4.1 算法说明

代谢综合征评估基于 **IDF (国际糖尿病联盟)** 和 **NCEP ATP III** 的联合诊断标准。满足 5 项标准中的 3 项及以上即可诊断为代谢综合征。

**参考文献**:
> Alberti KG, et al. Harmonizing the metabolic syndrome. Circulation. 2009;120(16):1640-1645.

### 4.2 诊断标准（亚洲人群）

| 标准 | 男性 | 女性 |
|------|------|------|
| **腹型肥胖** | 腰围 ≥ 90cm | 腰围 ≥ 80cm |
| **甘油三酯升高** | ≥ 150 mg/dL 或正在治疗 | 同左 |
| **HDL降低** | < 40 mg/dL 或正在治疗 | < 50 mg/dL 或正在治疗 |
| **血压升高** | ≥ 130/85 mmHg 或正在治疗 | 同左 |
| **空腹血糖升高** | ≥ 5.6 mmol/L 或正在治疗 | 同左 |

**诊断**: 满足 ≥ 3 项即确诊代谢综合征

### 4.3 风险等级划分

| 满足标准数 | 等级 | 说明 |
|-----------|------|------|
| 0 | low | 无风险 |
| 1-2 | medium | 有风险因素，需关注 |
| ≥ 3 | high | 确诊代谢综合征 |

### 4.4 使用示例

```python
from services.ml_models.metabolic import calculate_metabolic_risk

result = calculate_metabolic_risk(
    waist=95,
    gender='男',
    triglycerides=180,
    hdl_cholesterol=38,
    systolic_bp=135,
    diastolic_bp=88,
    fasting_glucose=6.0,
    on_bp_medication=False
)

print(f"满足标准: {result['criteria_met']}/5")
print(f"是否患病: {result['has_metabolic_syndrome']}")
print(f"风险等级: {result['risk_level']}")
```

---

## 五、数据依赖

### 5.1 用户健康档案 (UserHealthProfile)

ML 模型依赖 `user_health_profiles` 表中的数据：

| 字段 | 用于模型 | 说明 |
|------|---------|------|
| height, weight, bmi | 糖尿病、代谢 | 身体指标 |
| waist | 糖尿病、代谢 | 腰围 |
| systolic_bp, diastolic_bp | 全部 | 血压 |
| total_cholesterol, hdl_cholesterol | 心血管、代谢 | 胆固醇 |
| triglycerides | 代谢 | 甘油三酯 |
| fasting_glucose | 糖尿病、代谢 | 空腹血糖 |
| is_smoker | 心血管 | 吸烟状态 |
| has_diabetes | 心血管 | 糖尿病史 |
| on_bp_medication | 全部 | 降压药使用 |
| family_diabetes | 糖尿病 | 家族史 |
| exercise_frequency | 糖尿病 | 运动频率 |
| daily_fruit_vegetable | 糖尿病 | 饮食习惯 |

### 5.2 数据完整性处理

当用户健康档案数据不完整时，系统会：
1. 使用默认值进行评估（可能不准确）
2. 在结果中标注数据缺失
3. 建议用户完善健康档案

---

## 六、API 集成

### 6.1 风险评估 API

**请求**:
```
POST /api/risk/assessment
Content-Type: application/json
Authorization: Bearer <token>

{
    "type": "cardiovascular"  // 或 "diabetes", "metabolic"
}
```

**响应**:
```json
{
    "success": true,
    "data": {
        "id": 1,
        "type": "cardiovascular",
        "name": "心血管疾病风险",
        "date": "2024-12-06",
        "risk_level": "medium",
        "score": 45,
        "factors": [
            {"name": "年龄适中", "positive": true, "detail": "45岁"},
            {"name": "总胆固醇偏高", "positive": false, "detail": "220 mg/dL"}
        ],
        "recommendations": [
            "控制饮食中的饱和脂肪和胆固醇摄入",
            "增加有氧运动，每周至少150分钟"
        ],
        "details": {
            "model": "Framingham Risk Score (2008)",
            "risk_percentage": 14.9
        }
    }
}
```

---

## 七、模型局限性

### 7.1 Framingham Risk Score
- 基于美国人群数据，可能不完全适用于亚洲人群
- 仅适用于 30-79 岁人群
- 不考虑家族史、肥胖等因素

### 7.2 FINDRISC
- 基于芬兰人群数据
- 腰围标准已调整为亚洲人群标准
- 不包含实验室检查指标

### 7.3 代谢综合征
- 已采用亚洲人群腰围标准
- 诊断为二元结果，不提供概率

### 7.4 改进方向
- 收集本地化数据进行模型校准
- 引入更多风险因素
- 开发基于机器学习的预测模型
- 结合时序数据进行动态风险评估

---

## 八、趋势分析模块

### 8.1 TrendAnalyzer - 趋势分析器

**功能**:
- 移动平均计算
- 线性回归预测
- 趋势方向和强度判断

```python
from services.ml_models import analyze_health_trend

# 分析30天心率数据
data = [72, 75, 71, 73, 78, ...]  # 30天数据
result = analyze_health_trend(data, 'heart_rate')

# 返回结果
{
    'direction': 'stable',      # rising/falling/stable
    'strength': 'weak',         # strong/moderate/weak
    'change_rate': 2.5,         # 变化率 %
    'prediction': [73, 74, ...], # 未来7天预测
    'moving_avg': [...],        # 移动平均
    'analysis': '心率保持稳定，变化幅度2.5%'
}
```

### 8.2 AnomalyDetector - 异常检测器

**检测方法**:
| 方法 | 说明 | 适用场景 |
|------|------|---------|
| Z-Score | 基于标准差 | 正态分布数据 |
| IQR | 基于四分位距 | 非正态分布数据 |
| 医学阈值 | 基于临床标准 | 所有健康指标 |

**医学阈值定义**:
| 指标 | 严重偏低 | 偏低 | 偏高 | 严重偏高 |
|------|---------|------|------|---------|
| 心率 | ≤40 | ≤50 | ≥100 | ≥120 |
| 收缩压 | ≤80 | ≤90 | ≥140 | ≥180 |
| 舒张压 | ≤50 | ≤60 | ≥90 | ≥120 |
| 血糖 | ≤3.0 | ≤3.9 | ≥6.1 | ≥11.1 |
| 血氧 | ≤90 | ≤94 | - | - |

```python
from services.ml_models import detect_anomalies

result = detect_anomalies(data, 'heart_rate', dates)

# 返回结果
{
    'has_anomaly': True,
    'anomaly_count': 2,
    'anomalies': [
        {'index': 15, 'value': 120, 'severity': 'critical', 'message': '严重偏高'}
    ],
    'latest_status': None,  # 最新值状态
    'summary': '近期有1次严重异常'
}
```

### 8.3 HealthScoreCalculator - 健康评分

**评分维度和权重**:
| 维度 | 权重 | 最优范围 |
|------|------|---------|
| 心率 | 15% | 60-80 bpm |
| 血压 | 20% | 100-120/60-80 mmHg |
| 血糖 | 15% | 4.0-5.5 mmol/L |
| 睡眠 | 15% | 7-8 小时 |
| 活动量 | 15% | 8000-12000 步 |
| 体重(BMI) | 10% | 18.5-24 |
| 血氧 | 10% | 97-100% |

**评分等级**:
| 分数 | 等级 | 说明 |
|------|------|------|
| ≥90 | excellent | 健康状况优秀 |
| 75-89 | good | 健康状况良好 |
| 60-74 | fair | 健康状况一般 |
| <60 | poor | 需要关注 |

```python
from services.ml_models import calculate_health_score

metrics = {
    'heart_rate': 72,
    'blood_pressure_sys': 118,
    'blood_pressure_dia': 75,
    'blood_sugar': 5.0,
    'sleep_duration': 7.5,
    'steps': 9000,
    'spo2': 98,
    'bmi': 22
}

result = calculate_health_score(metrics)

# 返回结果
{
    'overall_score': 92,
    'category_scores': {
        'heart_rate': 95,
        'blood_pressure': 95,
        'blood_sugar': 95,
        ...
    },
    'level': 'excellent',
    'summary': '健康状况优秀，请继续保持！'
}
```

---

## 九、趋势分析 API

### 9.1 API 列表

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/trend/metric/<type>` | GET | 指标趋势分析 |
| `/api/trend/device/<type>` | GET | 设备数据趋势 |
| `/api/trend/sleep` | GET | 睡眠趋势 |
| `/api/trend/activity` | GET | 活动量趋势 |
| `/api/trend/score` | GET | 健康评分 |
| `/api/trend/analysis` | GET | 综合分析报告 |

### 9.2 综合分析报告示例

```
GET /api/trend/analysis
Authorization: Bearer <token>
```

**响应**:
```json
{
    "success": true,
    "data": {
        "health_score": {
            "overall_score": 85,
            "level": "good",
            "category_scores": {...}
        },
        "trends": {
            "heart_rate": {
                "direction": "stable",
                "analysis": "心率保持稳定"
            },
            "sleep": {
                "avg_duration": 7.2,
                "avg_quality": 75,
                "summary": "睡眠时长充足，质量良好"
            },
            "activity": {
                "avg_steps": 8500,
                "reach_rate": 85,
                "summary": "运动量适中，目标达成率85%"
            }
        },
        "anomalies": [...],
        "anomaly_count": 2,
        "recommendations": [
            "继续保持良好的生活习惯",
            "定期进行健康检查"
        ],
        "generated_at": "2024-12-07T08:00:00"
    }
}
```

---

## 十、文件结构

```
backend/services/ml_models/
├── __init__.py              # 模块导出
├── cardiovascular.py        # 心血管风险评估 (Framingham)
├── diabetes.py              # 糖尿病风险评估 (FINDRISC)
├── metabolic.py             # 代谢综合征评估
└── trend_analysis.py        # 趋势分析和异常检测

backend/services/
├── trend_service.py         # 趋势分析服务

backend/routes/
├── trend.py                 # 趋势分析 API 路由
```

---

## 十一、参考资料

1. **Framingham Heart Study**: https://framinghamheartstudy.org/
2. **FINDRISC**: https://www.diabetes.fi/english
3. **IDF Metabolic Syndrome Definition**: https://www.idf.org/
4. **NCEP ATP III Guidelines**: JAMA. 2001;285(19):2486-2497
