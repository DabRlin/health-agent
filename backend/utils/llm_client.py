"""
LLM 客户端封装 - 硅基流动（兼容 OpenAI 格式）
"""
from openai import OpenAI
from config import config


def get_llm_client() -> OpenAI:
    """获取 LLM 客户端"""
    return OpenAI(
        api_key=config.LLM_API_KEY,
        base_url=config.LLM_BASE_URL,
    )
