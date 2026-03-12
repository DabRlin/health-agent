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
