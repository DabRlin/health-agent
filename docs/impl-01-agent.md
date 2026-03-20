# Agent 智能问诊——实现细节

> 对应源文件：`backend/services/agent_service.py`、`backend/services/agent_tools.py`、`backend/routes/consultation.py`
> 更新日期：2025-03

---

## 一、整体设计思路

智能问诊模块不是简单的"输入问题→输出答案"，而是一套完整的 **Agentic 系统**：LLM 作为推理引擎，配合工具调用（Function Calling）自主决定"是否需要查数据"、"查什么数据"、"如何利用数据给出回答"。

这套机制的核心价值在于：**AI 回答有真实数据支撑，而不是依靠模型记忆凭空编造**。例如用户问"我最近血压怎么样"，Agent 会先调用 `get_health_metrics` 工具获取数据库中的真实测量值，再基于数据给出专业分析。

---

## 二、科室系统设计

### 科室注册

四个科室在 `DEPARTMENTS` 字典中注册，每个科室有独立的 System Prompt（`SYSTEM_PROMPTS`）和工具集（`TOOLS_BY_DEPARTMENT`）。

```python
DEPARTMENTS = {
    "general":       { "name": "全科门诊",  ... },
    "cardiology":    { "name": "心血管科",  ... },
    "endocrinology": { "name": "内分泌科",  ... },
    "dermatology":   { "name": "皮肤科",   ... },
}
```

### System Prompt 架构

每个科室的 System Prompt 由两部分组成：

```
科室专属部分（_SYSTEM_PROMPTS[dept]）
  ├── 角色定位
  ├── 擅长领域
  └── 可用工具说明

+ 公共行为准则（_BASE_RULES）
  ├── 工具调用规则（8条）
  └── 免责声明
```

这种设计让科室特性和行为规范解耦，修改通用规则只需改一处。

`_BASE_RULES` 中的关键行为约束：

- **"优先调用工具"**：询问个人数据时必须先查工具，不得凭空编造
- **"录入确认"**：调用 `add_health_metric` 前必须先向用户确认，防止写入错误数据
- **"边界意识"**：明确告知 AI 建议不能替代专业诊断

### 工具集过滤

```python
TOOLS_BY_DEPARTMENT = {
    "general":       TOOLS_SCHEMA,           # 全量 7 个工具
    "cardiology":    TOOLS_SCHEMA,           # 全量 7 个工具
    "endocrinology": TOOLS_SCHEMA,           # 全量 7 个工具
    "dermatology":   [knowledge_tool_only],  # 仅知识库工具
}
```

皮肤科只暴露知识库工具：皮肤科医生不需要查心率/血压数据，限制工具集可以减少无效工具调用、降低 token 消耗，也避免模型在皮肤问题上产生跑题的体征分析。

---

## 三、会话管理

### 会话创建（`start_consultation`）

```python
consultation = Consultation(
    user_id=user.id,
    session_id=cls._generate_session_id(),  # UUID
    department=department,
    status="进行中"
)
```

会话创建时同步写入一条欢迎消息（`role=assistant`），前端加载时即可展示。

### 会话命名

首条用户消息发送后，自动截取前 20 字作为会话标题：

```python
if not consultation.summary:
    consultation.summary = user_message[:20] + ('…' if len(user_message) > 20 else '')
```

不在创建时命名，是因为用户在首次发消息之前会话实际上没有主题，延迟命名更准确。

---

## 四、ReAct 循环核心实现

### 入口：`send_message_stream`

```
接收 (session_id, user_message, user_id, image_base64, image_mime)
   ↓
1. 查询会话（验证会话存在）
2. 写入用户消息到数据库
3. yield user_message 确认事件给前端
4. 皮肤科且有图片 → 调 VL 分析，yield thinking 事件
5. 构建消息列表（_build_messages 滑动窗口）
6. 调用 _agent_loop，逐项 yield 事件
7. 循环结束后写入 AI 完整回复
8. yield done 事件
```

### 核心循环：`_agent_loop`

这是整个系统最关键的方法，最多运行 `MAX_TOOL_ROUNDS=5` 轮。

#### 第一轮（stream=True + tools）

第一轮使用流式模式 + tools，这是为了优化最常见场景（无工具调用时直接流式输出）的体验：

```python
stream = client.chat.completions.create(
    model=config.LLM_MODEL,
    messages=loop_messages,
    tools=tools_schema,
    tool_choice="auto",
    stream=True,          # 关键：流式
    temperature=0.7,
    max_tokens=2048,
)

collected_content = ""
collected_tool_calls = {}  # index -> {id, name, arguments}

for chunk in stream:
    delta = chunk.choices[0].delta
    if delta.content:
        collected_content += delta.content
        yield delta.content          # 直接 yield 文本，真正逐字流式
    if delta.tool_calls:
        # 按 index 收集并拼接 tool_calls 的 JSON arguments
        for tc_delta in delta.tool_calls:
            idx = tc_delta.index
            collected_tool_calls.setdefault(idx, {"id":"","name":"","arguments":""})
            if tc_delta.id: collected_tool_calls[idx]["id"] = tc_delta.id
            if tc_delta.function.name: ...
            if tc_delta.function.arguments: ...  # 分块拼接

# 无工具调用 → 文本已全部 yield，直接 return
if not collected_tool_calls:
    return
```

**为什么文本和工具调用是互斥的**：OpenAI Function Calling 协议规定，当 LLM 决定调用工具时，`delta.content` 为空，所有内容在 `delta.tool_calls` 中；当 LLM 决定直接回答时，`delta.tool_calls` 为空，内容在 `delta.content` 中。因此可以安全地在第一轮同时流式输出文本和收集工具调用。

#### 工具执行阶段

有工具调用时，按 index 排序（支持并发多工具调用）执行：

```python
for tc in tool_calls_list:
    tool_name = tc["function"]["name"]
    tool_args = json.loads(tc["function"]["arguments"])
    
    yield {"type": "thinking", "content": cls._tool_thinking_text(tool_name)}
    # 前端收到 thinking 事件后显示"思考气泡"
    
    tool_result = execute_tool(tool_name, tool_args, user_id, department=department)
    
    loop_messages.append({
        "role": "tool",
        "tool_call_id": tc["id"],
        "content": tool_result    # 工具结果以 tool 角色注入对话
    })
```

#### 后续轮（stream=False）

工具执行完毕后，切换为非流式调用判断是否需要继续调用工具：

```python
response = client.chat.completions.create(
    model=config.LLM_MODEL,
    messages=loop_messages,
    tools=tools_schema,
    tool_choice="auto",
    stream=False,         # 后续轮 non-stream
)

message = response.choices[0].message
if not message.tool_calls:
    # 不需要更多工具 → 切回 stream=True 输出最终回复
    yield from cls._stream_final_response(client, loop_messages)
    return
```

`_stream_final_response` 方法：向 LLM 发最终请求（不带 tools），纯流式输出最终回复。

#### 超出最大轮次兜底

```python
# round_num >= MAX_TOOL_ROUNDS 时
yield from cls._stream_final_response(client, loop_messages)
```

防止 LLM 陷入无限工具调用死循环，保证请求必然结束。

### 消息构建：`_build_messages`（滑动窗口）

```python
# System Prompt
messages = [{"role": "system", "content": SYSTEM_PROMPTS[department]}]

# 历史消息（滑动窗口，取最近 LLM_MAX_HISTORY 条）
history = db.query(ConsultationMessage)\
    .filter(...)\
    .order_by(desc(...))\
    .limit(config.LLM_MAX_HISTORY)\
    .all()
for msg in reversed(history):
    messages.append({"role": msg.role, "content": msg.content})

# VL 分析注入（皮肤科）
if vl_analysis:
    messages.append({
        "role": "assistant",
        "content": f"[图像分析结果]\n{vl_analysis}"
    })

# 当前用户消息
messages.append({"role": "user", "content": user_message})
```

滑动窗口的意义：LLM 的 context window 有限，保留最近 N 条历史既保证了对话连贯性，也控制了每次 API 调用的 token 成本。

---

## 五、工具链设计（7个工具）

所有工具在 `agent_tools.py` 中定义，分为两部分：**实现函数** 和 **OpenAI Function Calling Schema**。

### Function Calling Schema 结构

```python
{
    "type": "function",
    "function": {
        "name": "get_health_metrics",
        "description": "...",
        "parameters": {
            "type": "object",
            "properties": {
                "metric_type": {
                    "type": "string",
                    "enum": ["heart_rate", "blood_pressure", ...],
                    "description": "..."
                }
            },
            "required": []
        }
    }
}
```

Schema 中的 `description` 字段至关重要——这是 LLM 决定调用哪个工具的依据。每个工具的描述都经过精心设计，明确说明"什么情况下调用"。

### 工具分发：`execute_tool`

```python
def execute_tool(tool_name: str, tool_args: dict, user_id: int, department: str = "general") -> str:
    """根据工具名分发到对应实现函数"""
    tool_map = {
        "get_health_metrics":   get_health_metrics,
        "get_health_trend":     get_health_trend,
        "run_risk_assessment":  run_risk_assessment,
        "get_user_profile":     get_user_profile,
        "add_health_metric":    add_health_metric,
        "get_health_knowledge": get_health_knowledge,
        "analyze_exam_report":  analyze_exam_report,
    }
    fn = tool_map.get(tool_name)
    if not fn:
        return json.dumps({"error": f"未知工具: {tool_name}"})
    return fn(user_id=user_id, department=department, **tool_args)
```

每个工具函数都返回 JSON 字符串，由 LLM 在后续推理中解析使用。

### 各工具实现要点

**`get_health_metrics`**：从 `HealthMetric` 表查询最近 N 条指标记录，按类型分组，附带 status 判断（normal/warning/danger）。

**`get_health_trend`**：调用 `TrendService.get_metric_trend()`，内部使用 ML 模型计算趋势方向、异常检测、7 天预测。

**`run_risk_assessment`**：调用 `RiskService.run_assessment()`，拉取用户健康档案，选择对应 ML 模型（Framingham/FINDRISC/代谢综合征/FRAX）计算，将结果存入 `risk_assessments` 表并返回摘要。

**`get_user_profile`**：查询 `User` + `UserHealthProfile` 表，返回基本信息和健康档案的结构化 JSON。

**`add_health_metric`**：向 `HealthMetric` 表插入新记录，自动计算 status，触发 `AutoTagService` 更新健康标签。

**`get_health_knowledge`**：先尝试 RAG 检索（ChromaDB），失败则降级到 SQLite `health_knowledge` 表模糊查询，返回 title + content 格式的知识片段。

**`analyze_exam_report`**：查询 `ExamReport` 表中最近一份已解析（`status=done`）的报告，返回解析结果的 JSON，包含各项指标、异常标记、总结。

### thinking 文字映射

```python
_TOOL_THINKING_MAP = {
    "get_health_metrics":   "正在获取健康指标数据...",
    "get_health_trend":     "正在分析健康趋势数据...",
    "run_risk_assessment":  "正在运行健康风险评估...",
    "get_user_profile":     "正在读取健康档案...",
    "add_health_metric":    "正在记录健康数据...",
    "get_health_knowledge": "正在检索健康知识库...",
    "analyze_exam_report":  "正在解读体检报告...",
}
```

前端收到 `thinking` 事件后展示对应文字，让用户知道 AI 在做什么，而不是一片空白等待。

---

## 六、皮肤科多模态流程

皮肤科特殊之处在于支持图片输入。流程实现：

```python
# send_message_stream 中
if department == "dermatology" and image_base64 and image_mime:
    yield json.dumps({"type": "thinking", "content": "正在分析皮肤图片..."})
    vl_analysis = VLService.analyze_skin_image(image_base64, image_mime, user_message)
    # vl_analysis 是字符串，包含皮损描述、可能方向、建议
```

VL 分析结果以 **"前置 assistant 消息"** 的方式注入对话历史（`_build_messages` 中），使当前轮的 Agent 能感知图像内容，但不会对前端可见（不写入 `ConsultationMessage` 表），保持对话记录的整洁。

VL 失败时静默忽略（`except Exception: logger.exception(...)`），降级为纯文本问诊，保证功能可用性。

---

## 七、SSE 流式协议实现

后端路由（`consultation.py`）使用 Flask 的 `Response` + Generator 实现 SSE：

```python
@consultation_bp.route('/message/stream', methods=['POST'])
@login_required
def send_message_stream():
    ...
    def generate():
        for event_json in AgentService.send_message_stream(...):
            yield f"data: {event_json}\n\n"  # SSE 格式
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',  # 禁止 Nginx 缓冲，确保实时推送
        }
    )
```

前端通过 `fetch` + `ReadableStream` 接收，按 `\n\n` 分割 SSE 事件，逐事件解析 JSON（`api/index.js` 的 `sendMessageStream` 方法）。

---

## 八、数据持久化

| 时机 | 操作 |
|------|------|
| 会话创建 | 写入 `Consultation` 记录 + 欢迎消息 |
| 用户发送消息 | 写入 `ConsultationMessage(role=user)` |
| 首条消息 | 更新 `Consultation.summary` 为消息前 20 字 |
| AI 回复完成 | 写入 `ConsultationMessage(role=assistant)` + 完整拼接文本 |
| 工具录入数据 | `add_health_metric` 工具写入 `HealthMetric` 表 |

注意：VL 分析结果**不写入** `ConsultationMessage`，仅作为当前轮次的 context 临时使用。
