"""
视觉语言模型服务
使用 Qwen3-VL 对皮肤科图片进行初步分析
"""
import base64
import logging
import os
import uuid
from typing import Optional

logger = logging.getLogger(__name__)

VL_SYSTEM_PROMPT = """你是一位专业的皮肤科 AI 助手，正在辅助分析用户上传的皮肤图片。

请对图片进行客观描述和初步分析，包括：
1. **外观描述**：皮损的形态、颜色、分布、大小（如可估计）
2. **可能方向**：结合外观描述，列举 2-3 种可能的皮肤状况（注意：仅供参考）
3. **建议**：是否需要就医，日常护理注意事项

**重要声明**：本分析为 AI 辅助参考，不构成医学诊断。如有疑虑请及时就诊皮肤科医生。"""


class VLService:
    """视觉语言模型服务"""

    @classmethod
    def analyze_skin_image(cls, image_base64: str, image_mime: str,
                           user_question: str = "") -> Optional[str]:
        """
        调用 Qwen3-VL 分析皮肤图片

        Args:
            image_base64: base64 编码的图片数据
            image_mime: 图片 MIME 类型，如 image/jpeg
            user_question: 用户的描述/问题（可选）

        Returns:
            分析结果文本，失败返回 None
        """
        try:
            from openai import OpenAI
            from config import config

            client = OpenAI(
                api_key=config.LLM_API_KEY,
                base_url=config.LLM_BASE_URL,
            )

            user_content = [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{image_mime};base64,{image_base64}"
                    }
                },
                {
                    "type": "text",
                    "text": user_question if user_question else "请分析这张皮肤图片。"
                }
            ]

            response = client.chat.completions.create(
                model=config.VL_MODEL,
                messages=[
                    {"role": "system", "content": VL_SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
                max_tokens=config.VL_MAX_TOKENS,
                temperature=0.3,
            )

            result = response.choices[0].message.content
            logger.info("VL 分析完成，结果长度: %d 字符", len(result) if result else 0)
            return result

        except Exception as e:
            logger.exception("VL 模型调用失败")
            return None

    @classmethod
    def extract_medication_info(cls, image_base64: str, image_mime: str) -> Optional[dict]:
        """
        从药品说明书图片中提取结构化用药信息

        Returns:
            dict with keys: name, med_type, reminders, duration_days,
            raw_instructions, contraindications, side_effects, storage, ocr_raw_text
            失败返回 None
        """
        import json
        import re

        system_prompt = """你是一个专业的药品说明书信息提取助手。
请仔细阅读图片中的药品说明书，提取关键信息并以 JSON 格式返回。

返回格式（严格 JSON，不要包含任何其他文字）：
{
  "name": "药品名称",
  "med_type": "oral",
  "reminders": [
    {"time": "08:00", "relation": "after_meal", "dose": "1片"}
  ],
  "duration_days": null,
  "raw_instructions": "用法用量原文",
  "contraindications": "禁忌原文",
  "side_effects": "不良反应原文",
  "storage": "储存条件原文",
  "ocr_raw_text": "说明书识别全文摘要"
}

med_type 枚举值：oral（口服）/ injection（注射）/ topical（外用涂抹）/ patch（贴敷）/ wash（洗剂）
reminders.relation 枚举值：before_meal（饭前）/ after_meal（饭后）/ with_meal（随餐）/ before_sleep（睡前）/ anytime（不限）
time 字段：根据 relation 合理推断，早餐后→08:00，午餐后→12:00，晚餐后→18:00，睡前→21:00，一日三次则生成三条
duration_days：如说明书中有明确疗程天数则填写，否则填 null"""

        try:
            from openai import OpenAI
            from config import config

            client = OpenAI(
                api_key=config.LLM_API_KEY,
                base_url=config.LLM_BASE_URL,
            )

            response = client.chat.completions.create(
                model=config.VL_OCR_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": [
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{image_mime};base64,{image_base64}"}
                        },
                        {"type": "text", "text": "请提取这份药品说明书的关键信息，返回 JSON。"}
                    ]},
                ],
                max_tokens=2048,
                temperature=0.1,
                timeout=60,
            )

            raw = response.choices[0].message.content or ""
            logger.info("VL 说明书提取完成，原始响应长度: %d", len(raw))

            # 从响应中提取 JSON（处理可能的 markdown 代码块包裹）
            json_match = re.search(r'\{[\s\S]+\}', raw)
            if json_match:
                data = json.loads(json_match.group())
                # 补全缺失字段默认值
                data.setdefault('name', '未知药品')
                data.setdefault('med_type', 'oral')
                data.setdefault('reminders', [])
                data.setdefault('duration_days', None)
                data.setdefault('raw_instructions', '')
                data.setdefault('contraindications', '')
                data.setdefault('side_effects', '')
                data.setdefault('storage', '')
                data.setdefault('ocr_raw_text', raw[:1000])
                return data

            logger.warning("VL 响应中未找到有效 JSON")
            return None

        except Exception as e:
            logger.exception("说明书信息提取失败")
            return None

    @classmethod
    def save_image(cls, image_base64: str, image_mime: str,
                   user_id: Optional[int] = None) -> Optional[str]:
        """
        将 base64 图片保存到服务器

        Args:
            image_base64: base64 编码的图片数据
            image_mime: 图片 MIME 类型
            user_id: 用户 ID（用于组织目录）

        Returns:
            相对路径（如 uploads/images/123/abc.jpg），失败返回 None
        """
        try:
            from config import config

            ext_map = {
                "image/jpeg": "jpg",
                "image/png": "png",
                "image/webp": "webp",
                "image/gif": "gif",
            }
            ext = ext_map.get(image_mime, "jpg")

            # 按用户 ID 分目录
            subdir = str(user_id) if user_id else "anonymous"
            save_dir = os.path.join(config.UPLOAD_DIR, subdir)
            os.makedirs(save_dir, exist_ok=True)

            filename = f"{uuid.uuid4().hex}.{ext}"
            filepath = os.path.join(save_dir, filename)

            img_bytes = base64.b64decode(image_base64)
            with open(filepath, "wb") as f:
                f.write(img_bytes)

            rel_path = os.path.join("uploads", "images", subdir, filename)
            logger.info("图片已保存: %s (%d bytes)", rel_path, len(img_bytes))
            return rel_path

        except Exception as e:
            logger.exception("图片保存失败")
            return None
