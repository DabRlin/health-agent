# 健康趋势分析——实现细节

> 对应源文件：`backend/services/ml_models/trend_analysis.py`、`backend/services/trend_service.py`、`backend/routes/trend.py`
> 更新日期：2025-03

---

## 一、模块职责

健康趋势分析模块回答两个问题：

1. **这个指标在历史上是怎么变化的？**（趋势方向、强度、变化率）
2. **有没有出现过不正常的值？**（异常检测）

同时提供两个附加能力：

3. **未来 7 天大概会怎样？**（短期预测）
4. **综合多项指标，整体健康分数是多少？**（健康评分）

---

## 二、模块架构

```
trend_service.py（调度层）
    └── 从数据库查询时序数据
    └── 调用 ml_models/trend_analysis.py

ml_models/trend_analysis.py（算法层）
    ├── TrendAnalyzer     — 趋势分析（移动平均 + 线性回归）
    ├── AnomalyDetector   — 异常检测（Z-Score + IQR + 医学阈值）
    └── HealthScoreCalculator — 综合健康评分
```

---

## 三、TrendAnalyzer：趋势分析

### 3.1 移动平均（`calculate_moving_average`）

```python
@classmethod
def calculate_moving_average(cls, data: List[float], window: int = 7) -> List[float]:
    result = []
    for i in range(len(data)):
        if i < window - 1:
            result.append(sum(data[:i+1]) / (i + 1))  # 边界：用已有数据计算
        else:
            result.append(sum(data[i-window+1:i+1]) / window)
    return result
```

7 日移动平均可以平滑日间波动，暴露真实趋势走向，是前端趋势折线图的平滑曲线数据来源。

### 3.2 线性回归（`linear_regression`）

采用最小二乘法，以时间索引（0, 1, 2, ...）为 x，指标值为 y，求斜率和截距：

```python
@classmethod
def linear_regression(cls, data: List[float]) -> Tuple[float, float]:
    n = len(data)
    x_mean = (n - 1) / 2
    y_mean = sum(data) / n
    
    # 最小二乘法
    numerator   = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(data))
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    
    slope     = numerator / denominator if denominator != 0 else 0.0
    intercept = y_mean - slope * x_mean
    return slope, intercept
```

**使用最近 14 天数据进行回归**，而不是全部历史：

```python
recent_data = data[-14:] if len(data) > 14 else data
slope, intercept = cls.linear_regression(recent_data)
```

这样做是因为长期历史数据中的旧趋势对当前趋势判断的参考价值有限，取最近 14 天更能反映"现在的走势"。

### 3.3 趋势方向与强度判定

```python
# 趋势方向（基于斜率符号和绝对值）
if abs(slope) < 0.1:
    direction = 'stable'
elif slope > 0:
    direction = 'rising'
else:
    direction = 'falling'

# 趋势强度
if abs_slope < 0.5:   strength = 'weak'
elif abs_slope < 2:   strength = 'moderate'
else:                 strength = 'strong'
```

阈值的选取考虑了实际健康指标的量纲（例如血压单位 mmHg，0.1/天的变化几乎不可感知；血糖单位 mmol/L，0.1/天则是明显趋势）。当前阈值适合大多数指标，对于量纲差异特别大的场景（如步数万级）可按需调整。

### 3.4 短期预测（`predict_next_values`）

```python
@classmethod
def predict_next_values(cls, data: List[float], steps: int = 7) -> List[float]:
    recent_data = data[-14:] if len(data) > 14 else data
    slope, intercept = cls.linear_regression(recent_data)
    
    n = len(recent_data)
    predictions = []
    for i in range(steps):
        pred = slope * (n + i) + intercept
        predictions.append(pred)
    
    return predictions
```

基于线性外推预测未来 7 天。这是一个故意简化的预测模型——对于健康数据，用户更关心"趋势方向"而非精确的数值预测；同时线性预测无需额外数据，计算开销极低，在每次 API 调用中实时计算完全可行。

---

## 四、AnomalyDetector：三层异常检测

系统采用三种互补的异常检测方法，取并集以提高召回率：

### 4.1 Z-Score 检测（统计方法）

```python
@classmethod
def detect_zscore(cls, data: List[float], threshold: float = 2.5) -> List[Dict]:
    mean = sum(data) / len(data)
    std  = math.sqrt(sum((x - mean) ** 2 for x in data) / len(data))
    
    anomalies = []
    for i, value in enumerate(data):
        zscore = (value - mean) / std
        if abs(zscore) > threshold:          # 超过 2.5σ 视为异常
            anomalies.append({
                'index': i, 'value': value,
                'zscore': round(zscore, 2),
                'type': 'high' if zscore > 0 else 'low'
            })
    return anomalies
```

**原理**：假设数据正态分布，超过均值 ±2.5 个标准差的点视为统计异常。  
**阈值选择 2.5 而非 3**：健康数据的真实分布往往有轻微偏态，2.5σ 的灵敏度更适合医疗场景（宁可多报警一次，也不漏掉异常）。

### 4.2 IQR 检测（鲁棒方法）

```python
@classmethod
def detect_iqr(cls, data: List[float], multiplier: float = 1.5) -> List[Dict]:
    sorted_data = sorted(data)
    n = len(sorted_data)
    q1 = sorted_data[n // 4]
    q3 = sorted_data[3 * n // 4]
    iqr = q3 - q1
    
    lower_bound = q1 - multiplier * iqr
    upper_bound = q3 + multiplier * iqr
    
    anomalies = []
    for i, value in enumerate(data):
        if value < lower_bound or value > upper_bound:
            anomalies.append({'index': i, 'value': value, ...})
    return anomalies
```

**原理**：基于四分位距，不受极端值影响（比 Z-Score 鲁棒）。  
**IQR 与 Z-Score 互补**：当数据分布非正态（健康数据的常见情况）时，IQR 更可靠；当数据接近正态时，Z-Score 更精确。两者取并集，能捕获单一方法可能遗漏的异常。

### 4.3 医学阈值检测（领域知识方法）

```python
MEDICAL_THRESHOLDS = {
    'heart_rate':         { 'critical_low': 40,  'low': 50,  'high': 100, 'critical_high': 120, 'unit': 'bpm' },
    'blood_pressure_sys': { 'critical_low': 80,  'low': 90,  'high': 140, 'critical_high': 180, 'unit': 'mmHg' },
    'blood_pressure_dia': { 'critical_low': 50,  'low': 60,  'high': 90,  'critical_high': 120, 'unit': 'mmHg' },
    'blood_sugar':        { 'critical_low': 3.0, 'low': 3.9, 'high': 6.1, 'critical_high': 11.1,'unit': 'mmol/L' },
    'spo2':               { 'critical_low': 90,  'low': 94,  'high': 100, 'critical_high': 100, 'unit': '%' },
}
```

医学阈值检测直接对最新值和历史值与绝对阈值比较，输出 `warning`（偏高/偏低）或 `critical`（严重偏高/偏低）。

| 严重程度 | 说明 | 前端展示 |
|---------|------|---------|
| `warning` | 超出正常范围 | 黄色警告 |
| `critical` | 超出危险范围 | 红色警告 + 建议就医 |

### 4.4 综合分析流程（`analyze_data`）

```python
@classmethod
def analyze_data(cls, data: List[float], metric_type: str, dates: List[str] = None) -> Dict:
    zscore_anomalies = cls.detect_zscore(data)
    iqr_anomalies    = cls.detect_iqr(data)
    
    # 合并两种统计检测结果（取并集）
    anomaly_indices = set()
    for a in zscore_anomalies + iqr_anomalies:
        anomaly_indices.add(a['index'])
    
    # 构建最终异常列表，叠加医学阈值判断
    anomalies = []
    for idx in sorted(anomaly_indices):
        medical = cls.detect_medical_anomaly(data[idx], metric_type)
        anomalies.append({
            'index': idx, 'value': data[idx],
            'date': dates[idx] if dates else None,
            'severity': medical['severity'] if medical else 'warning',
            'message': medical['message'] if medical else '统计异常值'
        })
    
    # 最新值的医学状态（独立于历史异常）
    latest_status = cls.detect_medical_anomaly(data[-1], metric_type)
    
    return {
        'has_anomaly': len(anomalies) > 0,
        'anomaly_count': len(anomalies),
        'anomalies': anomalies,
        'latest_status': latest_status,    # 用于前端当前状态提示
        'summary': cls._generate_summary(anomalies, latest_status, metric_type)
    }
```

---

## 五、HealthScoreCalculator：综合健康评分

### 5.1 指标权重设计

```python
WEIGHTS = {
    'heart_rate':     0.15,   # 心率
    'blood_pressure': 0.20,   # 血压（权重最高，心血管风险重要指标）
    'blood_sugar':    0.15,   # 血糖
    'sleep':          0.15,   # 睡眠
    'activity':       0.15,   # 活动量（步数）
    'weight':         0.10,   # 体重/BMI
    'spo2':           0.10,   # 血氧
}
```

血压权重最高（0.20），反映其在心血管健康评估中的重要性。各维度权重之和为 1.00，允许在只有部分数据时做加权平均（`total_weight` 只累加实际有数据的维度）。

### 5.2 单项指标评分逻辑

对每个指标定义**最优范围**和**正常范围**：

```python
ranges = {
    'heart_rate':         { 'optimal': (60, 80),    'normal': (50, 100)   },
    'blood_pressure_sys': { 'optimal': (100, 120),  'normal': (90, 140)   },
    'blood_sugar':        { 'optimal': (4.0, 5.5),  'normal': (3.9, 6.1)  },
    'sleep_duration':     { 'optimal': (7, 8),      'normal': (6, 9)      },
    'bmi':                { 'optimal': (18.5, 24),  'normal': (18.5, 28)  },
}
```

评分规则：
- **最优范围内**：90–100 分（固定返回 95）
- **正常范围内但不在最优范围**：70–90 分（线性插值，离最优越近分越高）
- **超出正常范围**：0–70 分（按偏离程度线性衰减）

```python
# 在最优范围 → 95分
if optimal[0] <= value <= optimal[1]:
    return 95

# 在正常范围（偏低侧）→ 70-90分，线性插值
if normal[0] <= value < optimal[0]:
    ratio = (value - normal[0]) / (optimal[0] - normal[0])
    return 70 + ratio * 20

# 超出正常范围（偏高侧）→ 0-70分
ratio = max(0, 1 - (value - normal[1]) / normal[1])
return ratio * 70
```

### 5.3 综合评分等级

| 综合评分 | 等级 | 说明 |
|---------|------|------|
| ≥ 90 | excellent | 健康状况优秀 |
| 75–89 | good | 健康状况良好 |
| 60–74 | fair | 健康状况一般 |
| < 60 | poor | 健康状况需要关注 |

该评分存入 `User.health_score` 字段，在首页仪表盘以圆形进度条展示。

---

## 六、TrendService 调度层

```python
class TrendService:
    
    @classmethod
    def get_metric_trend(cls, user_id: int, metric_type: str, days: int = 30) -> Dict:
        db = SessionLocal()
        try:
            # 按时间倒序查询指定天数内的数据
            since = datetime.now() - timedelta(days=days)
            records = db.query(HealthMetric).filter(
                HealthMetric.user_id == user_id,
                HealthMetric.metric_type == metric_type,
                HealthMetric.measured_at >= since
            ).order_by(HealthMetric.measured_at.asc()).all()
            
            if not records:
                return {"error": "暂无足够数据进行趋势分析"}
            
            values = [r.value for r in records]
            dates  = [r.measured_at.strftime("%Y-%m-%d") for r in records]
            
            # 趋势分析
            trend   = analyze_health_trend(values, metric_type)
            # 异常检测
            anomaly = detect_anomalies(values, metric_type, dates)
            # 统计摘要
            stats = {
                "count":  len(values),
                "mean":   round(sum(values) / len(values), 1),
                "max":    max(values),
                "min":    min(values),
                "latest": values[-1],
                "std":    round(math.sqrt(sum((v - sum(values)/len(values))**2 for v in values) / len(values)), 2)
            }
            
            return {
                "metric_type": metric_type,
                "days": days,
                "values": values,
                "dates": dates,
                "trend": trend,
                "anomaly": anomaly,
                "stats": stats
            }
        finally:
            db.close()
```

---

## 七、Agent 工具集成（`get_health_trend`）

```python
def get_health_trend(user_id, metric_type="all", days=30, **kwargs) -> str:
    if metric_type == "all":
        # 查询所有指标类型的趋势摘要
        results = {}
        for mt in ["heart_rate", "blood_pressure_sys", "blood_sugar", "bmi", "sleep"]:
            result = TrendService.get_metric_trend(user_id, mt, days)
            if "error" not in result:
                results[mt] = {
                    "direction": result["trend"]["direction"],
                    "change_rate": result["trend"]["change_rate"],
                    "latest": result["stats"]["latest"],
                    "anomaly_count": result["anomaly"]["anomaly_count"]
                }
        return json.dumps({"success": True, "trends": results})
    else:
        result = TrendService.get_metric_trend(user_id, metric_type, days)
        return json.dumps({"success": True, **result})
```

`metric_type="all"` 时返回所有指标的摘要，适合用户问"我最近整体健康趋势怎样"；指定单个类型时返回完整数据，适合"帮我分析血压趋势"。

---

## 八、前端数据可视化对接

趋势分析 API 返回的数据结构直接对应前端图表：

| 字段 | 用途 |
|------|------|
| `values` + `dates` | 折线图原始数据点 |
| `trend.moving_avg` | 折线图平滑曲线 |
| `trend.prediction` | 预测线（虚线，7个点） |
| `anomaly.anomalies` | 异常点标记（红点） |
| `trend.direction` / `trend.change_rate` | 趋势文字说明 |
| `stats` | 统计卡片（均值/最大值/最小值/标准差） |
