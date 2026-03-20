# HealthAI 各模块详细介绍

> 更新日期：2025-03

---

## 一、智能问诊模块（AI Consultation）

### 1.1 概述

智能问诊是系统的核心模块，基于 **LLM Function Calling + ReAct 循环**实现多轮对话式健康咨询。用户进入后需先选择科室，系统根据科室加载对应的专科 System Prompt 和工具集。

### 1.2 科室划分

| 科室 ID | 科室名称 | 专注领域 | 可用工具 |
|---------|---------|---------|---------|
| `general` | 全科门诊 | 通用健康咨询、慢病管理 | 全量 7 个工具 |
| `cardiology` | 心血管科 | 血压、心率、心血管风险 | 7 个工具 |
| `endocrinology` | 内分泌科 | 血糖、糖尿病、代谢综合征 | 7 个工具 |
| `dermatology` | 皮肤科 | 皮肤症状、图片分析 | 仅知识库工具 |

### 1.3 ReAct Agent 循环

核心实现在 `backend/services/agent_service.py` 的 `_agent_loop` 方法：

```
用户消息
   ↓
[第一轮] stream=True + tools
   ├─ 无工具调用 → 直接流式输出文本给前端（真正实时流）
   └─ 有工具调用 → 收集完整 tool_calls
         ↓
     执行工具（最多 5 轮）
         ↓
     向前端发送 thinking 事件
         ↓
[后续轮] stream=False 判断是否继续调用工具
   ├─ 无工具调用 → 调用 _stream_final_response() 流式输出
   └─ 有工具调用 → 执行工具，继续循环
         ↓
[超出最大轮次] → 强制流式输出最终回复
```

**关键设计**：第一轮采用 `stream=True` + tools，工具调用与文本输出互斥，因此可以在无工具调用时实现真正的逐字流式输出，有工具调用时无损切换为工具执行模式。

### 1.4 Agent 工具链（7 个工具）

| 工具名 | 功能 | 触发时机 |
|--------|------|---------|
| `get_health_metrics` | 查询用户最新健康指标 | 用户询问自己的数据 |
| `get_health_trend` | 分析指标历史趋势与异常 | 用户询问趋势/走势 |
| `run_risk_assessment` | 运行医学风险评估模型 | 用户询问患病风险 |
| `get_user_profile` | 获取用户基本信息档案 | 需要了解用户基础情况 |
| `add_health_metric` | 录入新的健康指标数据 | 用户表示要记录数据 |
| `get_health_knowledge` | RAG 检索健康知识库 | 用户询问疾病/饮食/药物等知识 |
| `analyze_exam_report` | 获取体检报告解析结果 | 用户询问体检结果 |

### 1.5 皮肤科图像分析流程

皮肤科支持用户上传图片，流程如下：

```
用户上传图片（base64）+ 文字描述
   ↓
后端检测 department == "dermatology" && 有图片
   ↓
VLService.analyze_skin_image()
   → 调用 Qwen2.5-VL-72B
   → 返回外观描述、可能方向、护理建议
   ↓
VL 分析结果注入对话上下文（作为 assistant 消息前置）
   ↓
Agent 继续正常 ReAct 循环（可调用知识库补充）
```

### 1.6 对话历史管理

- 采用**滑动窗口**策略，每次构建消息时只取最近 `LLM_MAX_HISTORY`（默认 10）条历史
- 会话首条消息自动截取前 20 字作为会话标题
- 支持会话重命名、删除、历史列表查看

### 1.7 SSE 流式协议

后端通过 Server-Sent Events（SSE）向前端推送以下事件类型：

| type | 含义 |
|------|------|
| `user_message` | 用户消息写库确认 |
| `thinking` | 工具调用中（附提示文字，前端显示思考气泡） |
| `chunk` | AI 回复文本片段（逐字流式） |
| `done` | 回复完成 |
| `error` | 错误信息 |

---

## 二、健康数据模块（Health Data）

### 2.1 健康指标

支持 6 类指标的录入、查询与状态评估：

| 指标类型 | 名称 | 单位 | 正常范围 |
|---------|------|------|---------|
| `heart_rate` | 心率 | bpm | 60–100 |
| `blood_pressure_sys` | 收缩压 | mmHg | 90–140 |
| `blood_pressure_dia` | 舒张压 | mmHg | 60–90 |
| `blood_sugar` | 空腹血糖 | mmol/L | 3.9–6.1 |
| `bmi` | BMI | kg/m² | 18.5–24.9 |
| `sleep` | 睡眠时长 | 小时 | 7–9 |

每条记录在写入时自动计算 `status`（normal / warning / danger）。

### 2.2 穿戴设备数据

系统设计了穿戴设备数据链路：
- `DeviceReading` 表：高频原始数据（心率、步数、睡眠、血氧、血压）
- `DailyHealthSummary` 表：每日汇总统计（平均/最大/最小心率、步数、睡眠分期、血氧等）
- `device_simulator.py`：模拟穿戴设备数据生成脚本

---

## 三、趋势分析模块（Trend Analysis）

### 3.1 功能

由 `backend/services/trend_service.py` + `backend/services/ml_models/trend_analysis.py` 协同实现：

- **趋势分析**：线性回归判断指标走势（上升/下降/稳定），输出斜率与置信度
- **异常检测**：基于 Z-score 与 IQR 联合检测异常点，返回异常索引与详情
- **7 天预测**：利用趋势模型外推未来 7 天预测值
- **统计摘要**：均值、标准差、最大值、最小值、达标率

### 3.2 数据来源

优先从 `HealthMetric` 表读取用户手动录入数据；亦支持从 `DeviceReading` 高频数据生成趋势。

---

## 四、风险评估模块（Risk Assessment）

### 4.1 四大医学模型

| 评估类型 | 模型名称 | 评估对象 | 关键输入 |
|---------|---------|---------|---------|
| `cardiovascular` | Framingham Risk Score | 10 年心血管事件风险 | 年龄、性别、总胆固醇、HDL、收缩压、吸烟史、糖尿病史 |
| `diabetes` | FINDRISC | 10 年 2 型糖尿病风险 | 年龄、BMI、腰围、运动习惯、饮食习惯、血糖史、家族史 |
| `metabolic` | IDF/NCEP ATP III | 代谢综合征诊断 | 腰围、甘油三酯、HDL、血压、空腹血糖 |
| `osteoporosis` | FRAX® (无 BMD) | 骨质疏松骨折风险 | 年龄、性别、BMI、骨折史、吸烟、饮酒、激素使用史 |

### 4.2 缺失数据处理

当用户健康档案中某些字段未填写时，系统：
1. 使用合理默认值完成计算
2. 在评估结果的 `factors` 中追加"部分数据使用默认值"提示
3. 建议用户完善健康档案以提高准确性

### 4.3 风险等级

所有模型统一输出：`low`（低风险）、`medium`（中风险）、`high`（高风险），附带评分（0-100）、风险因素列表和改善建议列表。

---

## 五、体检报告模块（Exam Report）

### 5.1 处理流程

```
用户上传 PDF / 图片
   ↓
ExamService.upload_and_parse()
   ↓
① OCR：DeepSeek-OCR 提取全文文字
   ↓
② 结构化解析：GLM-4.7（JSON mode）
   提取：报告日期、医院名称、各项指标（名称/数值/单位/参考范围/状态）、总结
   ↓
③ 保存到 exam_reports 表（status: pending → processing → done / failed）
   ↓
④ Agent 可通过 analyze_exam_report 工具读取解析结果并进行专业解读
```

### 5.2 数据结构

解析后的 `parsed_data` JSON 字段包含：
- `report_date`：报告日期
- `hospital`：医院名称
- `items`：指标数组（每项含 name、value、unit、reference_range、status）
- `summary`：一句话总结
- `abnormal_items`：自动筛选出偏高/偏低/异常的指标

---

## 六、用药管理模块（Medication）

### 6.1 说明书智能识别

用户拍摄药品说明书图片，系统通过 `VLService.extract_medication_info()` 调用 `Qwen2.5-VL-72B` 提取：

- 药品名称、剂型（口服/注射/外用/贴敷/洗剂）
- 用法用量结构化为提醒列表（时间、餐食关系、剂量）
- 疗程天数、禁忌、不良反应、储存条件
- 识别全文（OCR 原文摘要）

提取结果**先展示给用户确认**，用户确认后才写入数据库，避免误识别。

### 6.2 用药提醒数据结构

```json
{
  "reminders": [
    { "time": "08:00", "relation": "after_meal", "dose": "1片" },
    { "time": "18:00", "relation": "after_meal", "dose": "1片" }
  ]
}
```

---

## 七、RAG 知识检索模块

### 7.1 知识源

以《默克家庭诊疗手册》（3.5MB 中文文本）作为知识源，涵盖疾病、症状、药物、检查指标等权威医学内容。

### 7.2 检索流程

```
用户查询 query
   ↓
① bge-m3 向量化 query（硅基流动 Embedding API）
   ↓
② ChromaDB 向量检索，召回 Top-20 相关片段
   ↓
③ bge-reranker-v2-m3 精排，返回 Top-3
   ↓
④ 返回 title + text + relevance_score
```

### 7.3 科室专属 Collection

索引构建时按科室拆分为 5 个 Collection：

| Collection | 覆盖内容 |
|-----------|---------|
| `merck_manual` | 全量兜底（默认） |
| `dept_general` | 通用健康、慢病 |
| `dept_cardiology` | 心血管专项 |
| `dept_endocrinology` | 内分泌专项 |
| `dept_dermatology` | 皮肤科专项 |

Agent 调用 `get_health_knowledge` 时自动路由至对应科室 Collection，Collection 不存在时降级到全量。

### 7.4 降级机制

若 RAG 索引未构建或检索失败，自动降级到结构化 `health_knowledge` 数据库表（SQLite 全文模糊匹配）。

---

## 八、管理后台模块（Admin）

管理员账户（`role=admin`）可访问 `/admin` 页面，功能包括：

- **用户管理**：查看所有用户列表、启用/禁用账户、重置密码
- **知识库管理**：增删改查 `health_knowledge` 结构化知识条目（分类：disease/indicator/diet/drug/symptom/lifestyle）
- **RAG 管理**：查看 ChromaDB 索引统计、分页浏览 chunks、语义搜索测试
- **系统统计**：用户总数、问诊总数、健康记录总数等

---

## 九、用户档案与健康标签

### 9.1 健康档案（UserHealthProfile）

包含用于风险评估的完整健康数据：身高体重BMI腰围、血压基线、血液指标（胆固醇/血糖/HbA1c）、生活习惯（吸烟/运动/饮食）、病史与家族史。

### 9.2 自动健康标签

`AutoTagService` 在用户更新健康档案时自动触发，根据 25 条规则生成系统标签（`source=system`），用户也可手动添加自定义标签（`source=user`）。

标签类型：
- `positive`（绿色）：如"体重正常"、"规律运动"、"血糖正常"
- `warning`（黄/橙色）：如"血压偏高"、"BMI偏高"、"糖尿病风险"

标签实时反映在首页仪表盘和健康档案页面。
