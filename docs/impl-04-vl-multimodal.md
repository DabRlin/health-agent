# VL 多模态服务——实现细节

> 对应源文件：`backend/services/vl_service.py`、`backend/services/exam_service.py`（OCR 部分）、`backend/routes/medication.py`
> 更新日期：2025-03

---

## 一、多模态能力概览

系统集成了两个视觉相关模型，分别负责不同场景：

| 模型 | 用途 | 调用场景 |
|------|------|---------|
| `Qwen/Qwen2.5-VL-72B-Instruct` | 图像理解与结构化提取 | 皮肤图像分析、药品说明书识别 |
| `deepseek-ai/DeepSeek-OCR` | 文字提取（OCR） | 体检报告图片/PDF 的文字识别 |

所有模型均通过硅基流动 OpenAI 兼容 API 调用，使用 base64 编码传输图像。

---

## 二、VLService 架构（`vl_service.py`）

```python
class VLService:
    _client: Optional[OpenAI] = None

    @classmethod
    def _get_client(cls) -> OpenAI:
        if cls._client is None:
            cls._client = OpenAI(
                api_key=config.LLM_API_KEY,
                base_url=config.LLM_BASE_URL,
            )
        return cls._client
```

使用类变量缓存 OpenAI 客户端，避免每次调用重新初始化。

---

## 三、皮肤图像分析（`analyze_skin_image`）

### 调用时机

用户在皮肤科门诊上传图片时触发，由 `AgentService.send_message_stream` 在构建消息前调用。

### 实现细节

```python
@classmethod
def analyze_skin_image(cls, image_base64: str, mime_type: str, 
                        user_description: str = "") -> Optional[str]:
    client = cls._get_client()
    data_url = f"data:{mime_type};base64,{image_base64}"
    
    prompt = """请分析这张皮肤图片，从以下几个方面给出专业描述：

1. **外观描述**：皮损的形态、颜色、大小、分布情况
2. **可能的皮肤状况**：根据外观，列举2-3种可能的皮肤状况（仅供参考）
3. **护理建议**：初步的护理和注意事项
4. **就医建议**：是否需要就医，以及就医的紧迫程度

**重要提示**：以上分析仅供参考，不能替代皮肤科医生的专业诊断。"""

    if user_description:
        prompt += f"\n\n用户描述：{user_description}"
    
    response = client.chat.completions.create(
        model=config.VL_MODEL,   # Qwen/Qwen2.5-VL-72B-Instruct
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": data_url}
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }],
        max_tokens=config.VL_MAX_TOKENS,  # 默认 1024
        temperature=0.3,   # 低温度，输出更确定、更保守
    )
    
    return response.choices[0].message.content
```

### 与 Agent 的集成方式

VL 分析结果以**前置 assistant 消息**注入对话上下文：

```python
# _build_messages 中
if vl_analysis:
    messages.append({
        "role": "assistant",
        "content": f"[图像分析结果]\n{vl_analysis}"
    })
# 紧接着追加当前用户消息
messages.append({"role": "user", "content": user_message})
```

**为什么用 assistant 角色而不是 system 角色**：将图像分析作为"AI 已经观察到的内容"注入，比放在 system prompt 中语义更自然——相当于 AI 先自己看了图，再和用户对话。

**不写入数据库**：VL 分析结果仅作为当次请求的临时 context，不写入 `ConsultationMessage` 表，历史对话中不展示，保持对话记录整洁。

---

## 四、药品说明书结构化提取（`extract_medication_info`）

### 设计目标

用户拍摄药品说明书图片后，系统自动提取结构化用药信息，减少手动录入成本，同时保证用户在确认后才入库。

### 实现细节

```python
@classmethod
def extract_medication_info(cls, image_base64: str, mime_type: str) -> Optional[dict]:
    client = cls._get_client()
    data_url = f"data:{mime_type};base64,{image_base64}"
    
    prompt = """请从这张药品说明书图片中提取用药信息，以 JSON 格式输出。

JSON 格式如下：
{
    "name": "药品名称",
    "med_type": "oral（口服）/ injection（注射）/ topical（外用）/ patch（贴敷）/ lotion（洗剂）",
    "reminders": [
        {
            "time": "08:00",
            "relation": "after_meal（饭后）/ before_meal（饭前）/ with_meal（随餐）/ empty_stomach（空腹）/ any_time（任意时间）",
            "dose": "剂量描述，如'1片'、'5ml'"
        }
    ],
    "duration_days": 用药天数（整数或null）,
    "raw_instructions": "用法用量原文",
    "contraindications": "禁忌症原文",
    "side_effects": "不良反应原文",
    "storage": "储存条件原文",
    "ocr_raw_text": "识别到的关键文字摘要"
}

只输出 JSON，不要输出其他内容。"""

    response = client.chat.completions.create(
        model=config.VL_MODEL,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": data_url}},
                {"type": "text", "text": prompt}
            ]
        }],
        max_tokens=config.VL_MAX_TOKENS,
        temperature=0.1,   # 极低温度，强制结构化输出
    )
    
    content = response.choices[0].message.content.strip()
    
    # 提取 JSON（模型有时会在 JSON 前后加说明文字）
    import re
    json_match = re.search(r'\{.*\}', content, re.DOTALL)
    if json_match:
        return json.loads(json_match.group())
    return None
```

### 用户确认流程

VL 提取结果**先返回前端展示**，不直接写库：

```
POST /medications/extract
    → VLService.extract_medication_info()
    → 返回 { success: true, data: {...} }  ← 前端展示供用户审查

用户确认/修改后：
POST /medications
    → 写入 Medication 表
```

这套"提取→确认→入库"的两步流程是防止 VL 识别错误写入脏数据的关键保障。

### reminders 数据结构设计

`reminders` 字段是 JSON 数组，存储在 `Medication.reminders` 列（SQLite JSON 类型）：

```json
[
    { "time": "08:00", "relation": "after_meal", "dose": "1片" },
    { "time": "20:00", "relation": "after_meal", "dose": "1片" }
]
```

结构化的时间提醒便于前端展示，也为未来接入系统推送通知预留了接口。

---

## 五、DeepSeek-OCR 体检报告提取（`exam_service.py`）

体检报告处理使用的是专用 OCR 模型 `deepseek-ai/DeepSeek-OCR`，与 Qwen2.5-VL 分工不同：

| 模型 | 擅长 | 用于 |
|------|------|------|
| DeepSeek-OCR | 文字提取，高精度识别印刷体 | 体检报告文字原文提取 |
| Qwen2.5-VL | 图像理解 + 结构化抽取 | 皮肤分析、说明书结构化 |

体检报告的处理是**两步串联**：OCR → LLM 结构化解析，而不是一步到位。原因是体检报告的指标解读逻辑较复杂（需要判断正常范围、给出状态），用专门的 JSON mode 提示让 GLM-4.7 做结构化分析效果比直接让 VL 模型一步完成更稳定。

```python
# 步骤一：OCR 提取文字
ocr_text = ExamService.ocr_image(image_bytes, mime_type)

# 步骤二：GLM-4.7 结构化解析
parsed_data = ExamService.parse_report(ocr_text)
```

详细实现见 `impl-05-exam-report.md`。

---

## 六、图像传输机制

所有图像均以 **base64 Data URL** 格式传输：

```
data:{mime_type};base64,{base64_encoded_bytes}
```

前端上传流程（以说明书识别为例）：

```javascript
// Medication.vue / ExamReport.vue
const file = event.target.files[0]
const reader = new FileReader()
reader.onload = (e) => {
    const dataUrl = e.target.result
    // dataUrl = "data:image/jpeg;base64,/9j/4AAQ..."
    const [header, base64] = dataUrl.split(',')
    const mime = header.match(/:(.*?);/)[1]
    
    await api.medicationExtract(base64, mime)
}
reader.readAsDataURL(file)
```

**不上传到服务器文件系统**（除体检报告外），图像数据在请求体中传输，处理完成后不保留，保护用户隐私。体检报告会保存原文件路径到 `ExamReport.file_path`，供后续重新解析使用。

---

## 七、错误处理策略

VL 服务的调用可能因网络、模型负载、图像质量等原因失败，系统采用以下策略：

| 场景 | 处理方式 |
|------|---------|
| 皮肤图像分析失败 | 静默忽略，降级为纯文字问诊，不向用户展示错误 |
| 说明书识别失败 | 返回 500 错误，前端提示"识别失败，请确认图片清晰" |
| JSON 解析失败 | 正则提取 JSON 片段；全部失败时返回 `None`，触发上层错误处理 |
| 体检 OCR 失败 | `ExamReport.status` 标记为 `failed`，前端展示失败状态 |
