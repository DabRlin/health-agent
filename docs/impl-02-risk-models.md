# 风险评估模型——实现细节

> 对应源文件：`backend/services/ml_models/cardiovascular.py`、`diabetes.py`、`metabolic.py`、`osteoporosis.py`、`backend/services/risk_service.py`
> 更新日期：2025-03

---

## 一、整体架构

风险评估模块由两层组成：

```
RiskService（调度层）
    ├── 从 UserHealthProfile 读取用户数据
    ├── 处理缺失字段（填充默认值）
    ├── 分发到对应 ML 模型类
    └── 将结果存入 risk_assessments 表

ml_models/（算法层）
    ├── FraminghamRiskCalculator    — 心血管
    ├── FINDRISCCalculator          — 糖尿病
    ├── MetabolicSyndromeCalculator — 代谢综合征
    └── FRAXCalculator              — 骨质疏松
```

所有模型均以纯 Python 实现，不依赖任何外部医学计算库，算法忠实还原各自参考文献中的公式与评分表。

---

## 二、Framingham Risk Score（心血管风险）

### 参考文献

D'Agostino RB Sr, et al. *General cardiovascular risk profile for use in primary care.* Circulation. 2008;117(6):743-753.

### 输入参数

```python
@dataclass
class CardiovascularRiskInput:
    age: int            # 年龄 30–79 岁
    gender: str         # '男' 或 '女'
    total_cholesterol: float   # 总胆固醇 mg/dL
    hdl_cholesterol: float     # HDL 胆固醇 mg/dL
    systolic_bp: float         # 收缩压 mmHg
    on_bp_medication: bool     # 是否服用降压药
    is_smoker: bool            # 是否吸烟
    has_diabetes: bool         # 是否有糖尿病
```

### 数学模型

采用 **Cox 比例风险模型**，对男女分别使用不同系数矩阵。

**男性系数：**

| 变量 | 系数 |
|------|------|
| ln(年龄) | 3.06117 |
| ln(总胆固醇) | 1.12370 |
| ln(HDL) | -0.93263 |
| ln(收缩压，未治疗) | 1.93303 |
| ln(收缩压，治疗中) | 1.99881 |
| 吸烟 | 0.65451 |
| 糖尿病 | 0.57367 |
| baseline_survival | 0.88936 |
| mean_coefficient_sum | 23.9802 |

**女性系数：**

| 变量 | 系数 |
|------|------|
| ln(年龄) | 2.32888 |
| ln(总胆固醇) | 1.20904 |
| ln(HDL) | -0.70833 |
| ln(收缩压，未治疗) | 2.76157 |
| ln(收缩压，治疗中) | 2.82263 |
| 吸烟 | 0.52873 |
| 糖尿病 | 0.69154 |
| baseline_survival | 0.95012 |
| mean_coefficient_sum | 26.1931 |

**计算公式：**

```python
coefficient_sum = (
    coef['ln_age'] * ln(age) +
    coef['ln_total_chol'] * ln(total_cholesterol) +
    coef['ln_hdl'] * ln(hdl_cholesterol) +
    (coef['ln_sbp_treated'] if on_bp_medication else coef['ln_sbp_untreated']) * ln(systolic_bp) +
    (coef['smoker'] if is_smoker else 0) +
    (coef['diabetes'] if has_diabetes else 0)
)

# 10年风险概率
risk = 1 - baseline_survival ^ exp(coefficient_sum - mean_coefficient_sum)
```

这是标准的 Cox 生存函数形式：`S(t) = S₀(t)^exp(Xβ - mean(Xβ))`，其中 `S₀(t)` 为基础生存率（10年）。

### 风险等级判定

| risk_percentage | 等级 |
|----------------|------|
| < 10% | low（低风险） |
| 10%–20% | medium（中风险） |
| ≥ 20% | high（高风险） |

### 评分归一化

```python
score = min(100, int(risk_percentage * 3))
# 约 33% 风险对应满分 100
```

### 输入验证

年龄限制在 30–79 岁（Framingham 研究的适用范围），超出范围返回 `risk_level='unknown'`。

---

## 三、FINDRISC（2型糖尿病风险）

### 参考文献

Lindström J, Tuomilehto J. *The diabetes risk score: a practical tool to predict type 2 diabetes risk.* Diabetes Care. 2003;26(3):725-731.

### 评分机制

FINDRISC 是积分量表，满分 26 分，8 个维度各自打分后求和。

### 各维度评分规则

**① 年龄（0–4分）**

| 年龄 | 分数 |
|------|------|
| < 45 岁 | 0 |
| 45–54 岁 | 2 |
| 55–64 岁 | 3 |
| ≥ 65 岁 | 4 |

**② BMI（0–3分）**

| BMI | 分数 |
|-----|------|
| < 25 | 0 |
| 25–29.9 | 1 |
| ≥ 30 | 3 |

**③ 腰围（0–4分，男女标准不同）**

| | 男性 | 女性 | 分数 |
|--|------|------|------|
| 正常 | < 94cm | < 80cm | 0 |
| 偏大 | 94–101cm | 80–87cm | 3 |
| 过大 | ≥ 102cm | ≥ 88cm | 4 |

**④ 每日运动（0–2分）**

| 是否每天运动≥30分钟 | 分数 |
|-------------------|------|
| 是 | 0 |
| 否 | 2 |

**⑤ 每日蔬果摄入（0–1分）**

| 是否每天吃蔬果 | 分数 |
|--------------|------|
| 是 | 0 |
| 否 | 1 |

**⑥ 服用降压药（0–2分）**

| 是否服用降压药 | 分数 |
|--------------|------|
| 否 | 0 |
| 是 | 2 |

**⑦ 高血糖史（0–5分）**

| 曾检出血糖偏高 | 分数 |
|--------------|------|
| 否 | 0 |
| 是 | 5 |

**⑧ 家族糖尿病史（0–5分）**

| 家族史 | 分数 |
|--------|------|
| 无 | 0 |
| 二级亲属（祖父母/叔伯） | 3 |
| 一级亲属（父母/兄弟姐妹） | 5 |

### 总分与风险等级对应

| 总分 | 风险等级 | 10年发生概率 |
|------|---------|------------|
| 0–6 | low | ~1% |
| 7–11 | low | ~4% |
| 12–14 | medium | ~17% |
| 15–20 | high | ~33% |
| ≥ 21 | high | ~50% |

### 评分归一化

```python
normalized_score = min(100, int(total_score * 100 / 26))
# 满分 26 分 → 标准化为 0-100
```

---

## 四、代谢综合征评估（IDF/NCEP ATP III）

### 参考文献

- Alberti KG, et al. *Harmonizing the metabolic syndrome.* Circulation. 2009;120(16):1640-1645.
- NCEP ATP III Guidelines. JAMA. 2001;285(19):2486-2497.

### 诊断逻辑

代谢综合征不同于其他评分模型——它是**诊断性判断**，满足 5 项标准中的 3 项及以上即可诊断。

系统采用**亚洲人群腰围标准**（比欧美标准更严格）：

| 诊断标准 | 异常阈值（亚洲） | 备注 |
|---------|---------------|------|
| ① 腹型肥胖 | 男≥90cm，女≥80cm | IDF 亚洲标准 |
| ② 甘油三酯升高 | ≥150 mg/dL | 或正在接受降脂治疗 |
| ③ HDL 降低 | 男<40，女<50 mg/dL | 或正在接受降脂治疗 |
| ④ 血压升高 | ≥130/85 mmHg | 或正在接受降压治疗 |
| ⑤ 空腹血糖升高 | ≥5.6 mmol/L | 或正在接受降糖治疗 |

### 治疗状态的处理

**关键设计**：正在接受相关治疗的患者即使当前测量值正常，对应标准也计为"满足"。例如：

```python
# 甘油三酯
tg_abnormal = (input_data.triglycerides >= 150) or input_data.on_lipid_medication

# HDL
hdl_abnormal = (input_data.hdl_cholesterol < hdl_threshold) or input_data.on_lipid_medication

# 血压
bp_abnormal = (input_data.systolic_bp >= 130 or input_data.diastolic_bp >= 85) or input_data.on_bp_medication
```

这符合临床实际：患者已在用药控制的事实本身就说明该项指标存在问题。

### 风险评分

```python
score = criteria_met * 20  # 每满足 1 项 20 分，最高 100 分
risk_level:
  0 项 → 'low'
  1–2 项 → 'medium'
  ≥ 3 项 → 'high'（确诊代谢综合征）
```

---

## 五、FRAX® 骨质疏松骨折风险

### 参考文献

Kanis JA, et al. *FRAX® and the assessment of fracture probability in men and women from the UK.* Osteoporos Int. 2008;19(4):385-397.

### 无 BMD 版本

本系统实现的是 **FRAX® 无骨密度（BMD）简化版**，仅依靠临床风险因子估算骨折风险，适合在没有 DXA 骨密度检测设备的场景下使用。

### 输入参数

```python
age, gender, bmi,
previous_fracture,    # 既往骨折史
parent_hip_fracture,  # 父母髋部骨折史
current_smoker,       # 吸烟
glucocorticoids,      # 长期服用糖皮质激素
rheumatoid_arthritis, # 类风湿性关节炎
secondary_osteoporosis, # 继发性骨质疏松
alcohol_3_or_more     # 每日饮酒≥3单位
```

### 计算逻辑

系统采用**基于年龄查表 + 风险因子叠加**的方法（非原始 FRAX® 回归方程，但结果趋势一致）：

1. **基础风险**：按年龄区间查基础骨折概率表（男女不同）
2. **BMI 调整**：BMI < 20 时风险上调；BMI > 25 时风险下调
3. **风险因子累加**：每个阳性因子按权重叠加到基础概率

| 风险因子 | 权重调整 |
|---------|---------|
| 既往骨折史 | +1.5倍 |
| 父母髋部骨折史 | +1.2倍 |
| 当前吸烟 | +1.15倍 |
| 长期糖皮质激素 | +1.35倍 |
| 类风湿性关节炎 | +1.25倍 |
| 继发性骨质疏松 | +1.2倍 |
| 每日饮酒≥3单位 | +1.15倍 |

### 风险等级

| 10年主要骨质疏松骨折风险 | 等级 |
|----------------------|------|
| < 10% | low |
| 10%–20% | medium |
| ≥ 20% | high |

---

## 六、RiskService 调度层

`risk_service.py` 负责从数据库读取用户数据、处理缺失字段、分发到对应模型，并将结果持久化。

### 数据读取

```python
profile = db.query(UserHealthProfile).filter(
    UserHealthProfile.user_id == user_id
).first()
user = db.query(User).filter(User.id == user_id).first()
```

### 缺失数据处理策略

用户健康档案中往往存在空字段，系统采用**有原则的默认值**填充：

```python
# 以心血管评估为例
total_cholesterol = profile.total_cholesterol or 200.0  # 正常上限
hdl_cholesterol   = profile.hdl_cholesterol or 50.0     # 正常水平
systolic_bp       = profile.systolic_bp or 120.0        # 正常收缩压
```

同时将使用默认值的字段名称追加到结果的 `factors` 列表：

```python
if not profile.total_cholesterol:
    missing_fields.append("总胆固醇")
...
if missing_fields:
    result['factors'].append({
        'name': f'部分数据使用默认值（{", ".join(missing_fields)}）',
        'positive': False,
        'detail': '请完善健康档案以提高评估准确性'
    })
```

### 结果持久化

```python
assessment = RiskAssessment(
    user_id=user_id,
    assessment_type=assessment_type,    # cardiovascular / diabetes / metabolic / osteoporosis
    risk_level=result['risk_level'],
    score=result['score'],
    factors=json.dumps(result['factors']),
    recommendations=json.dumps(result['recommendations']),
    details=json.dumps(result.get('details', {})),
)
db.add(assessment)
db.commit()
```

每次评估都会写库，前端历史列表可查看评估变化趋势。

### 统一输出格式

所有四个模型的返回结果均遵循相同结构：

```json
{
    "risk_level": "low | medium | high",
    "score": 0,
    "risk_percentage": 0.0,
    "factors": [
        { "name": "...", "positive": true/false, "detail": "..." }
    ],
    "recommendations": ["建议1", "建议2", ...],
    "details": { "model": "...", ... }
}
```

这种统一格式使前端风险评估页面可以用同一套组件渲染四种不同类型的评估结果。

---

## 七、Agent 调用风险评估工具的流程

当用户在问诊中说"帮我评估心血管风险"，Agent 会调用 `run_risk_assessment` 工具：

```python
def run_risk_assessment(user_id, assessment_type="cardiovascular", **kwargs) -> str:
    result = RiskService.run_assessment(user_id, assessment_type)
    # 将结果格式化为 Agent 友好的文字摘要
    summary = f"""
    评估类型：{assessment_type}
    风险等级：{result['risk_level']}
    风险评分：{result['score']}/100
    主要风险因素：{[f['name'] for f in result['factors'] if not f['positive']]}
    建议：{result['recommendations'][:3]}
    """
    return json.dumps({"success": True, "summary": summary, "full_result": result})
```

Agent 拿到工具结果后，结合知识库内容对风险因素逐条解释，最终给出个性化建议。
