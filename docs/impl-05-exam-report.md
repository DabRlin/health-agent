# 体检报告解析——实现细节

> 对应源文件：`backend/services/exam_service.py`、`backend/routes/exam.py`、`backend/services/agent_tools.py`（`analyze_exam_report`）
> 更新日期：2025-03

---

## 一、设计思路

体检报告通常是医院打印的 PDF 或拍摄的图片，格式各异，无法用固定规则解析。系统采用**两步 AI 流水线**：

```
原始文件（PDF / 图片）
       ↓
① OCR（DeepSeek-OCR）
   → 提取全文文字（保留原始格式）
       ↓
② 结构化解析（GLM-4.7 JSON mode）
   → 提取指标列表、报告日期、医院、总结
       ↓
③ 存入数据库（ExamReport 表）
       ↓
④ Agent 工具调用（analyze_exam_report）
   → 返回解析结果供 AI 分析解读
```

---

## 二、文件上传与预处理

### 路由入口（`exam.py`）

```python
@exam_bp.route('/reports/upload', methods=['POST'])
@login_required
def upload_exam_report():
    file = request.files.get('file')
    if not file:
        return jsonify({"success": False, "error": "未上传文件"}), 400
    
    file_bytes = file.read()
    mime_type = file.content_type   # image/jpeg, image/png, application/pdf
    
    # 写入数据库（pending 状态）
    report = ExamReport(
        user_id=user_id,
        file_path=saved_path,
        status="pending"
    )
    db.add(report)
    db.commit()
    
    # 异步/同步处理（当前为同步）
    ExamService.process_report(report.id, file_bytes, mime_type)
    
    return jsonify({"success": True, "data": report_to_dict(report)})
```

### PDF 处理

PDF 文件使用 `pymupdf`（fitz）提取每页为图片，再分页 OCR：

```python
import fitz  # pymupdf

doc = fitz.open(stream=file_bytes, filetype="pdf")
page_texts = []
for page in doc:
    # 将 PDF 页面渲染为图片（300 DPI）
    mat = fitz.Matrix(300/72, 300/72)
    pix = page.get_pixmap(matrix=mat)
    img_bytes = pix.tobytes("jpeg")
    
    # OCR 提取文字
    text = ExamService.ocr_image(img_bytes, "image/jpeg")
    page_texts.append(text)

full_text = "\n".join(page_texts)
```

---

## 三、OCR 实现（DeepSeek-OCR）

```python
@classmethod
def ocr_image(cls, image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
    client = cls._get_client()
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    data_url = f"data:{mime_type};base64,{b64}"
    
    resp = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-OCR",
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": data_url}},
                {"type": "text", 
                 "text": "请识别图片中的所有文字，原样输出，不要添加任何解释。"}
            ]
        }],
        max_tokens=4096,   # 体检报告文字量大，需要较高 token 上限
        temperature=0.0    # OCR 任务要求零温度，不允许创造性输出
    )
    
    return resp.choices[0].message.content
```

**选择 DeepSeek-OCR 而非通用 VL 模型的原因**：DeepSeek-OCR 是专门为文字识别训练的模型，对印刷体、表格、密集数字的识别精度高于通用 VL 模型，且响应速度更快。

---

## 四、结构化解析（GLM-4.7 JSON mode）

OCR 得到的是原始文字流，还需要进行语义理解和结构化提取。这一步使用 GLM-4.7 配合精心设计的 prompt：

```python
PARSE_PROMPT = """你是一位专业的医疗报告解析助手。
请从以下体检报告文字中提取关键信息，以 JSON 格式输出，不要输出任何其他内容。

JSON 格式如下：
{
  "report_date": "YYYY-MM-DD 或 null",
  "hospital": "医院名称或 null",
  "items": [
    {
      "name": "指标名称",
      "value": 数值（数字类型）或 "字符串结果",
      "unit": "单位或空字符串",
      "reference_range": "参考范围或空字符串",
      "status": "正常 / 偏高 / 偏低 / 异常 / 未知"
    }
  ],
  "summary": "一句话总结报告整体情况"
}

体检报告文字：
"""

@classmethod
def parse_report_text(cls, ocr_text: str) -> Optional[dict]:
    client = cls._get_client()
    
    resp = client.chat.completions.create(
        model=config.LLM_MODEL,   # GLM-4.7
        messages=[{
            "role": "user",
            "content": PARSE_PROMPT + ocr_text
        }],
        max_tokens=3000,
        temperature=0.1,          # 低温度，严格按 JSON 格式输出
        response_format={"type": "json_object"}   # JSON mode
    )
    
    content = resp.choices[0].message.content
    return json.loads(content)
```

### 异常指标自动标注

解析完成后，系统自动从 `items` 中筛选出非正常状态的指标写入 `abnormal_items`：

```python
parsed_data = cls.parse_report_text(ocr_text)
if parsed_data and "items" in parsed_data:
    abnormal = [
        item for item in parsed_data["items"]
        if item.get("status") not in ("正常", "未知", "")
    ]
    parsed_data["abnormal_items"] = abnormal
```

`abnormal_items` 在前端直接渲染为红色警告，帮助用户快速定位问题指标。

---

## 五、数据库模型

```python
class ExamReport(Base):
    id           = Column(Integer, primary_key=True)
    user_id      = Column(Integer, ForeignKey("users.id"))
    file_path    = Column(String)         # 原始文件保存路径
    ocr_text     = Column(Text)           # OCR 提取的全文
    parsed_data  = Column(JSON)           # 结构化解析结果（JSON 存储）
    status       = Column(String)         # pending / processing / done / failed
    report_date  = Column(String)         # 从 parsed_data 提取，用于排序显示
    hospital     = Column(String)         # 医院名称
    created_at   = Column(DateTime)
```

`parsed_data` 以 JSON 类型存储，既保留灵活性（各医院报告指标不同），又可通过 JSON 路径查询。

### 状态流转

```
pending → processing → done
                     ↘ failed
```

| 状态 | 说明 |
|------|------|
| `pending` | 文件已保存，等待处理 |
| `processing` | OCR/解析进行中 |
| `done` | 解析完成，`parsed_data` 有效 |
| `failed` | 处理失败（OCR 错误/API 失败） |

前端轮询或刷新时根据 `status` 字段决定是否展示解析结果。

---

## 六、Agent 工具集成（`analyze_exam_report`）

```python
def analyze_exam_report(user_id, **kwargs) -> str:
    db = SessionLocal()
    try:
        # 获取最近一份已解析的报告
        report = db.query(ExamReport).filter(
            ExamReport.user_id == user_id,
            ExamReport.status == "done"
        ).order_by(ExamReport.created_at.desc()).first()
        
        if not report:
            return json.dumps({"success": False, "error": "暂无已解析的体检报告"})
        
        parsed = report.parsed_data or {}
        
        # 格式化为 Agent 友好的结构
        result = {
            "success": True,
            "report_date": report.report_date,
            "hospital": report.hospital,
            "item_count": len(parsed.get("items", [])),
            "abnormal_items": parsed.get("abnormal_items", []),
            "summary": parsed.get("summary", ""),
            "all_items": parsed.get("items", [])
        }
        return json.dumps(result, ensure_ascii=False)
    finally:
        db.close()
```

Agent 拿到工具结果后，通常会：
1. 先概述报告整体情况（`summary` 字段）
2. 重点解读 `abnormal_items` 中的异常指标
3. 调用 `get_health_knowledge` 检索相关医学知识
4. 给出个性化改善建议

---

## 七、工程细节

### 并发安全

当前实现为同步处理（上传时阻塞等待解析完成）。对于大文件或多页 PDF，处理时间可能较长（10–60 秒）。生产环境应改为**异步任务队列**（如 Celery），上传后立即返回 `pending`，前端轮询状态。

### 文件存储路径

```python
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), '..', 'uploads', 'exam_reports')
os.makedirs(UPLOAD_DIR, exist_ok=True)
```

文件以 `{user_id}_{timestamp}_{original_filename}` 命名存储，路径保存在 `ExamReport.file_path`，OCR 失败时可重新处理。

### Token 估算

一份典型体检报告（A4 单页）OCR 后约 1000–2000 字，GLM-4.7 结构化解析需要约 2000–4000 output tokens。`max_tokens=3000` 基本覆盖常见报告规模。
