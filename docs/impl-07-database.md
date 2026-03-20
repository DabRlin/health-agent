# 数据库设计——完整文档

> 对应源文件：`backend/database/models.py`
> 数据库：SQLite（`backend/database/healthai.db`），SQLAlchemy 2.0 ORM
> 更新日期：2025-03

---

## 一、整体设计概览

系统使用单文件 SQLite 数据库，共 **13 张表**，分为四个功能域：

```
用户体系（3张）
  accounts ──── users ──── user_health_profiles

健康数据（5张）
  health_metrics
  health_records
  health_tags
  device_readings
  daily_health_summaries

AI 交互（3张）
  consultations ──── consultation_messages
  exam_reports
  risk_assessments

内容管理（2张）
  health_knowledge
  medications
  health_reports（辅助）
```

---

## 二、ER 关系图

```
accounts (1) ──────── (1) users
                           │
           ┌───────────────┼───────────────────────────┐
           │               │                           │
    (1)────┤          (1)──┤                           │
user_health_profiles  health_metrics (N)               │
                      health_records (N)               │
                      risk_assessments (N)             │
                      exam_reports (N)                 │
                      health_tags (N)                  │
                      device_readings (N)              │
                      daily_health_summaries (N)       │
                      medications (N)                  │
                      consultations (N) ───── consultation_messages (N)
```

所有业务表均以 `user_id` 外键关联到 `users` 表（而非 `accounts` 表），`accounts` 仅用于认证。

---

## 三、各表详细设计

### 3.1 accounts（账户表）

**职责**：存储登录凭据，与用户信息解耦。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK, AI | 账户 ID |
| `username` | String(50) | UNIQUE, NOT NULL | 登录用户名 |
| `password` | String(255) | NOT NULL | werkzeug scrypt 哈希值 |
| `role` | String(20) | DEFAULT 'user' | 角色：`user` / `admin` |
| `user_id` | Integer | FK → users.id | 关联用户信息 |
| `is_active` | Boolean | DEFAULT True | 账户是否启用（管理员可禁用） |
| `last_login` | DateTime | | 最近登录时间 |
| `created_at` | DateTime | DEFAULT now | 注册时间 |

**设计决策**：
- `accounts` 和 `users` 分表——认证信息（密码、角色）与业务信息（姓名、性别、健康档案）分离，符合单一职责原则。
- 密码使用 **werkzeug scrypt** 哈希存储，不可逆，即使数据库泄露也无法还原明文。
- `is_active` 支持管理员禁用账户，无需删除记录，保留操作历史。

---

### 3.2 users（用户信息表）

**职责**：存储用户基本个人信息和综合健康评分。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK, AI | 用户 ID（业务主键） |
| `name` | String(50) | NOT NULL | 姓名 |
| `gender` | String(10) | | 性别 |
| `age` | Integer | | 年龄 |
| `birthday` | String(20) | | 生日 |
| `phone` | String(20) | | 手机号 |
| `email` | String(100) | | 邮箱 |
| `location` | String(100) | | 所在地 |
| `avatar` | String(255) | | 头像路径/URL |
| `health_score` | Integer | DEFAULT 80 | 综合健康评分 0–100 |
| `created_at` | DateTime | DEFAULT now | 创建时间 |
| `updated_at` | DateTime | AUTO UPDATE | 最后更新时间 |

**设计决策**：
- `health_score` 由 `HealthScoreCalculator` 基于最新指标计算后更新，在首页仪表盘展示。
- `age` 与 `birthday` 同时保留：`age` 用于快速查询和风险评估，`birthday` 用于精确计算。

---

### 3.3 user_health_profiles（健康档案表）

**职责**：存储用于医学风险评估的完整健康基线数据，与 `users` 一对一关联。

| 字段组 | 字段 | 类型 | 单位 |
|--------|------|------|------|
| **体型** | `height` | Float | cm |
| | `weight` | Float | kg |
| | `bmi` | Float | kg/m²（自动计算） |
| | `waist` | Float | cm |
| **血压基线** | `systolic_bp` | Float | mmHg |
| | `diastolic_bp` | Float | mmHg |
| | `on_bp_medication` | Boolean | |
| **血液指标** | `total_cholesterol` | Float | mg/dL |
| | `hdl_cholesterol` | Float | mg/dL |
| | `ldl_cholesterol` | Float | mg/dL |
| | `triglycerides` | Float | mg/dL |
| | `fasting_glucose` | Float | mmol/L |
| | `hba1c` | Float | % |
| **生活习惯** | `is_smoker` | Boolean | |
| | `smoking_years` | Integer | 年 |
| | `alcohol_frequency` | String | never/occasional/regular/heavy |
| | `exercise_frequency` | String | never/1-2/week/3-4/week/daily |
| | `exercise_minutes_per_week` | Integer | 分钟 |
| | `daily_fruit_vegetable` | Boolean | |
| | `high_salt_diet` | Boolean | |
| **病史** | `has_diabetes` | Boolean | |
| | `has_hypertension` | Boolean | |
| | `has_heart_disease` | Boolean | |
| | `family_diabetes` | Boolean | |
| | `family_heart_disease` | Boolean | |
| | `family_hypertension` | Boolean | |

**设计决策**：
- 独立为单独表（而非塞进 `users`）：健康档案字段多（25+），且更新频率与基本信息不同。
- `UNIQUE(user_id)` 约束保证每个用户只有一份档案，用 `UPSERT` 语义更新。
- 所有字段均可为 NULL：允许用户部分填写，风险评估时对空字段使用默认值并提示。
- 单位选择：血脂用 mg/dL（国际习惯），血糖用 mmol/L（国内标准），避免单位混用。

---

### 3.4 health_metrics（健康指标时序表）

**职责**：记录用户健康指标的每次测量值，是趋势分析和 Agent 查询的核心数据源。

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | Integer | PK, AI | |
| `user_id` | Integer | FK, NOT NULL | |
| `metric_type` | String(50) | NOT NULL | heart_rate / blood_pressure_sys / blood_pressure_dia / blood_sugar / bmi / sleep |
| `value` | Float | NOT NULL | 测量值 |
| `unit` | String(20) | | 单位（bpm / mmHg / mmol/L 等） |
| `status` | String(20) | DEFAULT 'normal' | normal / warning / danger |
| `recorded_at` | DateTime | DEFAULT now | 测量时间 |

**索引**：
```sql
CREATE INDEX ix_health_metrics_user_type_time
ON health_metrics (user_id, metric_type, recorded_at);
```

这是系统中最高频查询的表，复合索引覆盖了最常见的查询模式：「某用户的某类指标在某时间段内的记录」。

**设计决策**：
- 每次测量一行（时序设计），而非用一行存所有指标——便于按类型查询、计算趋势、做异常检测。
- `status` 在写入时由服务层计算（对比 `config.py` 中的正常范围），不在查询时实时计算，提高读取性能。
- `metric_type` 使用枚举字符串而非外键——指标类型是固定集合，字符串更直观，避免关联查询。

---

### 3.5 health_records（健康记录流水表）

**职责**：记录各类健康事件的流水日志，作为时间线视图的数据源。

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer | PK |
| `user_id` | Integer | FK |
| `record_type` | String(50) | 体检报告 / 日常监测 / 智能问诊 / 风险评估 |
| `source` | String(50) | 医院导入 / 手动录入 / 智能手表 / 在线咨询 |
| `status` | String(20) | 已记录 / 处理中 / 已完成 |
| `risk_level` | String(20) | low / medium / high |
| `summary` | Text | 一句话摘要 |
| `data` | JSON | 事件详细数据（灵活结构） |
| `record_date` | DateTime | 事件发生时间 |
| `created_at` | DateTime | 记录创建时间 |

**设计决策**：
- `data` 字段用 JSON 存储事件详情，不同 `record_type` 的 data 结构不同——这是有意的灵活设计，避免为每种记录类型单独建表。
- 与 `health_metrics` 的区别：`health_metrics` 是精确的数值时序，`health_records` 是事件日志，粒度更粗但覆盖更广。

---

### 3.6 risk_assessments（风险评估历史表）

**职责**：保存每次风险评估的完整结果，支持历史对比。

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer | PK |
| `user_id` | Integer | FK |
| `assessment_type` | String(50) | cardiovascular / diabetes / metabolic / osteoporosis |
| `name` | String(100) | 评估名称（如"Framingham 心血管风险"） |
| `risk_level` | String(20) | low / medium / high |
| `score` | Integer | 0–100 风险评分 |
| `factors` | JSON | 风险因素列表（含 name / positive / detail） |
| `recommendations` | JSON | 建议列表（字符串数组） |
| `assessed_at` | DateTime | 评估时间 |

**设计决策**：
- `factors` 和 `recommendations` 用 JSON 存储：每次评估结果的条目数量不固定，JSON 比多行关联表更简洁，且此数据主要用于展示，无需按字段查询。
- 每次重新评估都写新行（不覆盖旧行），保留历史记录，支持"我的风险在改善吗"这类问题。

---

### 3.7 consultations（问诊会话表）

**职责**：管理智能问诊的会话生命周期。

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer | PK（内部使用） |
| `user_id` | Integer | FK（带索引） |
| `session_id` | String(50) | UNIQUE，UUID，前端使用的会话标识 |
| `department` | String(30) | general / cardiology / endocrinology / dermatology |
| `summary` | String(200) | 会话标题（首条消息前 20 字，可手动重命名） |
| `status` | String(20) | 进行中 / 已完成 |
| `started_at` | DateTime | 会话开始时间 |
| `ended_at` | DateTime | 会话结束时间（可空） |

**设计决策**：
- 用 `session_id`（UUID）而非 `id` 作为前端标识符：避免暴露自增 ID 导致遍历攻击。
- `department` 存储在会话层，而不是在每条消息上——一次问诊只会属于一个科室，避免冗余。

---

### 3.8 consultation_messages（问诊消息表）

**职责**：存储会话中的所有消息，是 Agent 历史上下文的持久化层。

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer | PK |
| `consultation_id` | Integer | FK → consultations.id（带索引） |
| `role` | String(20) | user / assistant |
| `content` | Text | 消息内容（支持 Markdown） |
| `created_at` | DateTime | 消息时间 |

**设计决策**：
- `role` 只有 `user` 和 `assistant` 两种——Agent 调用工具的中间过程（`role=tool` 消息）不写库，只在当次请求的内存中存在。这使对话历史对用户而言是干净的一问一答格式，不暴露工具调用细节。
- `content` 存储 AI 回复的完整拼接文本（流式结束后写入），而非分块存储。
- `consultation_id` 带索引，支持高效的「按会话查消息」查询。

---

### 3.9 exam_reports（体检报告表）

**职责**：存储上传的体检报告文件信息及 AI 解析结果。

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer | PK |
| `user_id` | Integer | FK |
| `filename` | String(255) | 原始文件名 |
| `file_path` | String(512) | 服务器存储路径 |
| `report_date` | String(20) | LLM 提取的报告日期（YYYY-MM-DD） |
| `hospital` | String(200) | LLM 提取的医院名称 |
| `raw_text` | Text | OCR 提取的原始全文 |
| `parsed_data` | JSON | LLM 结构化解析结果 |
| `status` | String(20) | pending / processing / done / failed |
| `uploaded_at` | DateTime | 上传时间 |

**`parsed_data` JSON 结构**：
```json
{
  "report_date": "2024-06-15",
  "hospital": "某某医院",
  "items": [
    {
      "name": "空腹血糖",
      "value": 5.8,
      "unit": "mmol/L",
      "reference_range": "3.9-6.1",
      "status": "正常"
    }
  ],
  "abnormal_items": [...],
  "summary": "本次体检各项指标基本正常，血糖稍偏高"
}
```

**设计决策**：
- `raw_text` 和 `parsed_data` 都保留：`raw_text` 是 OCR 原始输出，供重新解析或人工核对；`parsed_data` 是 AI 结构化结果，供 Agent 工具直接使用。
- `status` 四状态流转支持异步处理模式，前端可根据状态显示进度提示。

---

### 3.10 health_tags（健康标签表）

**职责**：存储用户的健康标签，支持用户自建和系统自动评估两种来源。

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer | PK |
| `user_id` | Integer | FK |
| `name` | String(50) | 标签名（如"血压偏高"、"规律运动"） |
| `tag_type` | String(20) | positive / warning / neutral |
| `source` | String(10) | `user`（手动）/ `system`（自动评估） |
| `created_at` | DateTime | |

**设计决策**：
- `source` 字段区分两类标签，在同步逻辑中只重算 `source=system` 的标签，保留用户手动添加的标签不受影响。
- 系统标签每次健康档案更新时由 `AutoTagService` 全量重算（删除旧的 + 添加新的），避免脏数据。
- `tag_type` 驱动前端颜色渲染：`positive` 绿色，`warning` 黄/橙色，`neutral` 灰色。

---

### 3.11 device_readings（穿戴设备原始数据表）

**职责**：高频存储穿戴设备的原始采集数据。

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer | PK |
| `user_id` | Integer | FK |
| `device_type` | String(30) | smartwatch / band / scale / blood_pressure_monitor |
| `metric_type` | String(30) | heart_rate / steps / sleep / spo2 / blood_pressure |
| `value` | Float | 测量值 |
| `unit` | String(20) | 单位 |
| `recorded_at` | DateTime | 采集时间（带索引） |
| `raw_data` | JSON | 设备原始 JSON 数据（保留完整上下文） |

**索引**：
```sql
CREATE INDEX ix_device_readings_user_type_time
ON device_readings (user_id, metric_type, recorded_at);
```

**设计决策**：
- 与 `health_metrics` 的区别：`device_readings` 是高频原始数据（每分钟/每步），`health_metrics` 是用户主动录入的关键测量值。两张表职责分离，不混用。
- `raw_data` JSON 字段保留设备上报的完整原始包，便于日后重新处理或调试。

---

### 3.12 daily_health_summaries（每日健康汇总表）

**职责**：将 `device_readings` 的高频原始数据聚合为每日统计摘要，用于趋势分析和仪表盘展示。

主要字段按类别划分：

| 类别 | 字段 |
|------|------|
| **心率** | avg_heart_rate, min_heart_rate, max_heart_rate, resting_heart_rate |
| **活动** | total_steps, active_minutes, calories_burned, distance |
| **睡眠** | sleep_start_time, sleep_end_time, sleep_duration, deep_sleep_duration, light_sleep_duration, rem_duration, awake_count, sleep_quality_score |
| **血氧** | avg_spo2, min_spo2 |
| **血压** | morning_systolic, morning_diastolic, evening_systolic, evening_diastolic |

**索引**：
```sql
CREATE INDEX ix_daily_summary_user_date
ON daily_health_summaries (user_id, date);
```

**设计决策**：
- `date` 用 `String(10)` 存储 YYYY-MM-DD 而非 `Date` 类型——SQLite 的 Date 类型在 Python ORM 层偶有时区问题，字符串更稳定且查询方便。
- 睡眠时间存 `HH:MM` 字符串而非 DateTime——跨午夜的睡眠场景（如 23:00–07:00）用时间字符串比 DateTime 更直观，避免日期语义混乱。
- `(user_id, date)` 联合索引支持「查某用户某段时间的每日汇总」这一最常见查询。

---

### 3.13 health_knowledge（结构化知识库表）

**职责**：作为 RAG 检索失败时的降级知识库，同时供管理员维护结构化健康知识。

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer | PK |
| `category` | String(20) | disease / indicator / diet / drug / symptom / lifestyle |
| `subcategory` | String(50) | 子分类（如 cardiovascular / diabetes） |
| `title` | String(100) | 知识标题 |
| `keywords` | Text | 逗号分隔关键词，用于模糊搜索 |
| `content` | Text | 知识正文 |
| `reference_data` | JSON | 参考范围结构化数据（indicator 类专用） |
| `created_at` | DateTime | |

**`reference_data` 示例（indicator 类）**：
```json
{
  "normal_range": "60-100",
  "unit": "bpm",
  "warning_high": 100,
  "warning_low": 60,
  "danger_high": 120,
  "danger_low": 40
}
```

**设计决策**：
- `keywords` 字段为逗号分隔字符串，配合 SQLite `LIKE` 查询实现简单全文检索——不引入 FTS5 扩展，降低部署复杂度。
- `category` + `subcategory` 双层分类，支持管理界面按类目过滤和 Agent 工具按科室过滤。

---

### 3.14 medications（用药记录表）

**职责**：混合存储结构化用药提醒和非结构化说明书原文。

| 字段组 | 字段 | 类型 | 说明 |
|--------|------|------|------|
| **结构化** | `name` | String(100) | 药品名称 |
| | `med_type` | String(20) | oral/injection/topical/patch/wash |
| | `reminders` | JSON | 用药提醒列表（时间+餐食关系+剂量） |
| | `duration_days` | Integer | 疗程天数 |
| | `start_date` | String(20) | 开始服药日期 |
| **非结构化** | `raw_instructions` | Text | 用法用量原文 |
| | `contraindications` | Text | 禁忌原文 |
| | `side_effects` | Text | 不良反应原文 |
| | `storage` | Text | 储存条件原文 |
| | `ocr_raw_text` | Text | VL/OCR 识别全文 |
| **附件** | `image_path` | String(500) | 说明书图片路径 |

**`reminders` JSON 结构**：
```json
[
  { "time": "08:00", "relation": "after_meal", "dose": "1片" },
  { "time": "20:00", "relation": "after_meal", "dose": "1片" }
]
```

**设计决策**：
- **混合存储策略**：结构化部分（`reminders`）用于调度提醒通知，非结构化部分（`raw_instructions` 等）直接展示给用户，无需再解析。两者并存，各司其职。
- `reminders` 用 JSON 数组而非独立的 `medication_reminders` 表：每条药品的提醒数量通常 ≤ 4 次/天，JSON 存储避免了不必要的多表 JOIN，且前端直接可用。
- 保留 `ocr_raw_text` 字段存储 VL 识别全文，用户可查看 AI 原始识别内容，便于验证准确性。

---

## 四、跨表关系汇总

| 关系 | 类型 | 说明 |
|------|------|------|
| `accounts` → `users` | 1:1 | 一个账户对应一个用户档案 |
| `users` → `user_health_profiles` | 1:1 | 每个用户一份健康档案 |
| `users` → `health_metrics` | 1:N | 用户的所有健康指标记录 |
| `users` → `health_records` | 1:N | 用户的健康事件流水 |
| `users` → `risk_assessments` | 1:N | 用户的历次风险评估 |
| `users` → `consultations` | 1:N | 用户的问诊会话 |
| `consultations` → `consultation_messages` | 1:N | 会话中的所有消息 |
| `users` → `exam_reports` | 1:N | 用户上传的体检报告 |
| `users` → `health_tags` | 1:N | 用户的健康标签 |
| `users` → `device_readings` | 1:N | 穿戴设备原始数据 |
| `users` → `daily_health_summaries` | 1:N | 每日汇总 |
| `users` → `medications` | 1:N | 用药记录 |

`health_knowledge` 是独立内容表，无用户外键，全局共享。

---

## 五、索引设计汇总

| 表 | 索引 | 类型 | 目的 |
|----|------|------|------|
| `accounts` | `username` | UNIQUE | 登录查询 |
| `consultations` | `session_id` | UNIQUE | 会话查找 |
| `consultations` | `user_id` | 普通 | 按用户查会话列表 |
| `consultation_messages` | `consultation_id` | 普通 | 按会话查消息 |
| `health_metrics` | `(user_id, metric_type, recorded_at)` | 复合 | 趋势查询核心索引 |
| `device_readings` | `(user_id, metric_type, recorded_at)` | 复合 | 设备数据查询 |
| `daily_health_summaries` | `(user_id, date)` | 复合 | 按日期查汇总 |
| `health_knowledge` | `category` | 普通 | 按分类过滤 |
| `health_knowledge` | `subcategory` | 普通 | 按子分类过滤 |
| `user_health_profiles` | `user_id` | UNIQUE | 健康档案唯一性 |
| `medications` | `user_id` | 普通 | 按用户查用药列表 |

---

## 六、向量数据库（ChromaDB）

除 SQLite 外，系统还使用 **ChromaDB** 作为向量数据库，存储 RAG 知识库的 embedding。

**存储位置**：`backend/rag_data/chroma_db/`（本地持久化）

**Collection 结构**：

| Collection | 内容 | chunk 规模 |
|-----------|------|-----------|
| `merck_manual` | 《默克家庭诊疗手册》全量 chunks | 约 8000–12000 条 |
| `dept_cardiology` | 心血管专项 chunks | 约 1000–2000 条 |
| `dept_endocrinology` | 内分泌专项 chunks | 约 1000–2000 条 |
| `dept_dermatology` | 皮肤科专项 chunks | 约 500–1000 条 |
| `dept_general` | 通用健康 chunks | 约 3000–5000 条 |

**每条记录结构**：
```
{
  id:        "chunk_0001",
  document:  "文本内容（300-500字）",
  embedding: [0.023, -0.114, ...],   # 1024维 bge-m3 向量
  metadata:  {
    "source": "默克家庭诊疗手册",
    "chunk_index": 1,
    "department": "cardiology"
  }
}
```

**与 SQLite 的职责分工**：

| | SQLite | ChromaDB |
|--|--------|---------|
| 数据类型 | 结构化业务数据 | 非结构化文本 + 向量 |
| 查询方式 | 精确匹配、范围查询 | 语义相似度检索 |
| 更新频率 | 高频（每次用户操作） | 低频（知识库更新时重建） |
| 持久化 | 单文件 healthai.db | 目录 chroma_db/ |

---

## 七、数据库初始化

```python
# backend/database/models.py
def init_db():
    Base.metadata.create_all(bind=engine)

# 应用启动时自动调用（backend/app.py）
init_db()
```

`Base.metadata.create_all` 只创建不存在的表，对已有表无操作，安全幂等，每次启动自动补建新增的表。

测试数据填充：
```bash
python backend/database/seed.py
```
