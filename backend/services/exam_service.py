"""
体检报告服务
流程：上传文件 → DeepSeek-OCR 提取文字 → GLM JSON mode 结构化解析 → 存入 ExamReport 表
"""
import os
import base64
import json
from datetime import datetime
from typing import Optional

from openai import OpenAI

from config import config
from database.models import SessionLocal, ExamReport

# 上传文件保存目录
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), '..', 'uploads', 'exam_reports')
os.makedirs(UPLOAD_DIR, exist_ok=True)

# OCR 模型
OCR_MODEL = "deepseek-ai/DeepSeek-OCR"

# 解析 prompt
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


class ExamService:

    @classmethod
    def _get_client(cls) -> OpenAI:
        return OpenAI(
            api_key=config.LLM_API_KEY,
            base_url=config.LLM_BASE_URL,
        )

    # ------------------------------------------------------------------
    # OCR：图片 base64 → 原始文字
    # ------------------------------------------------------------------
    @classmethod
    def ocr_image(cls, image_bytes: bytes, mime_type: str = "image/jpeg") -> str:
        """调用 DeepSeek-OCR 提取图片文字"""
        client = cls._get_client()
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:{mime_type};base64,{b64}"

        resp = client.chat.completions.create(
            model=OCR_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": data_url}},
                        {"type": "text", "text": "请识别图片中的所有文字，原样输出，不要添加任何解释。"},
                    ],
                }
            ],
            max_tokens=4096,
        )
        return resp.choices[0].message.content or ""

    # ------------------------------------------------------------------
    # LLM 解析：原始文字 → 结构化 JSON
    # ------------------------------------------------------------------
    @classmethod
    def parse_report_text(cls, raw_text: str) -> dict:
        """用 GLM JSON mode 将 OCR 文字解析为结构化数据"""
        client = cls._get_client()
        resp = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": "你是专业的医疗报告解析助手，只输出合法 JSON，不输出其他内容。"},
                {"role": "user", "content": PARSE_PROMPT + raw_text},
            ],
            response_format={"type": "json_object"},
            max_tokens=2048,
            temperature=0.1,
        )
        text = resp.choices[0].message.content or "{}"
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"error": "解析失败", "raw": text}

    # ------------------------------------------------------------------
    # 主流程：保存文件 → OCR → LLM 解析 → 存库
    # ------------------------------------------------------------------
    @classmethod
    def upload_and_process(
        cls,
        user_id: int,
        filename: str,
        file_bytes: bytes,
        mime_type: str,
    ) -> dict:
        """
        完整处理流程，返回 ExamReport 字典。
        对于 PDF，先将每页转为图片再 OCR（需要 pymupdf）；
        图片直接 OCR。
        """
        db = SessionLocal()
        try:
            # 1. 保存原始文件
            safe_name = f"{user_id}_{int(datetime.now().timestamp())}_{filename}"
            file_path = os.path.join(UPLOAD_DIR, safe_name)
            with open(file_path, "wb") as f:
                f.write(file_bytes)

            # 2. 创建数据库记录（status=processing）
            report = ExamReport(
                user_id=user_id,
                filename=filename,
                file_path=file_path,
                status="processing",
            )
            db.add(report)
            db.commit()
            db.refresh(report)
            report_id = report.id

            # 3. OCR
            raw_text = ""
            try:
                if mime_type == "application/pdf":
                    raw_text = cls._ocr_pdf(file_bytes)
                else:
                    raw_text = cls.ocr_image(file_bytes, mime_type)
            except Exception as e:
                raw_text = f"[OCR 失败: {e}]"

            # 4. LLM 解析
            parsed_data = {}
            if raw_text and not raw_text.startswith("[OCR 失败"):
                try:
                    parsed_data = cls.parse_report_text(raw_text)
                except Exception as e:
                    parsed_data = {"error": str(e)}

            # 5. 更新记录
            report = db.query(ExamReport).filter(ExamReport.id == report_id).first()
            report.raw_text = raw_text
            report.parsed_data = parsed_data
            report.report_date = parsed_data.get("report_date")
            report.hospital = parsed_data.get("hospital")
            report.status = "done" if parsed_data and "error" not in parsed_data else "failed"
            db.commit()
            db.refresh(report)

            return cls._to_dict(report)

        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    # ------------------------------------------------------------------
    # PDF OCR：用 pymupdf 逐页转图 → OCR 拼接
    # ------------------------------------------------------------------
    @classmethod
    def _ocr_pdf(cls, pdf_bytes: bytes) -> str:
        try:
            import fitz  # pymupdf
        except ImportError:
            return "[PDF 解析需要安装 pymupdf: pip install pymupdf]"

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        texts = []
        for page in doc:
            pix = page.get_pixmap(dpi=200)
            img_bytes = pix.tobytes("jpeg")
            texts.append(cls.ocr_image(img_bytes, "image/jpeg"))
        doc.close()
        return "\n\n--- 第{}页 ---\n\n".join(texts) if len(texts) > 1 else (texts[0] if texts else "")

    # ------------------------------------------------------------------
    # 查询列表
    # ------------------------------------------------------------------
    @classmethod
    def get_reports(cls, user_id: int, limit: int = 20) -> list:
        db = SessionLocal()
        try:
            reports = (
                db.query(ExamReport)
                .filter(ExamReport.user_id == user_id)
                .order_by(ExamReport.uploaded_at.desc())
                .limit(limit)
                .all()
            )
            return [cls._to_dict(r) for r in reports]
        finally:
            db.close()

    # ------------------------------------------------------------------
    # 查询单条
    # ------------------------------------------------------------------
    @classmethod
    def get_report(cls, user_id: int, report_id: int) -> Optional[dict]:
        db = SessionLocal()
        try:
            r = (
                db.query(ExamReport)
                .filter(ExamReport.id == report_id, ExamReport.user_id == user_id)
                .first()
            )
            return cls._to_dict(r) if r else None
        finally:
            db.close()

    # ------------------------------------------------------------------
    # 删除
    # ------------------------------------------------------------------
    @classmethod
    def delete_report(cls, user_id: int, report_id: int) -> bool:
        db = SessionLocal()
        try:
            r = (
                db.query(ExamReport)
                .filter(ExamReport.id == report_id, ExamReport.user_id == user_id)
                .first()
            )
            if not r:
                return False
            # 删除文件
            if r.file_path and os.path.exists(r.file_path):
                os.remove(r.file_path)
            db.delete(r)
            db.commit()
            return True
        except Exception:
            db.rollback()
            return False
        finally:
            db.close()

    # ------------------------------------------------------------------
    # 序列化
    # ------------------------------------------------------------------
    @staticmethod
    def _to_dict(r: ExamReport) -> dict:
        return {
            "id": r.id,
            "filename": r.filename,
            "report_date": r.report_date,
            "hospital": r.hospital,
            "status": r.status,
            "parsed_data": r.parsed_data,
            "raw_text": r.raw_text,
            "uploaded_at": r.uploaded_at.strftime("%Y-%m-%d %H:%M"),
        }
