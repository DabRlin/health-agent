"""
HealthAI MVP - 配置管理
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """应用配置"""
    
    # Flask 配置
    DEBUG = os.getenv("DEBUG", "true").lower() == "true"
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "5000"))
    
    # LLM 配置（硅基流动，兼容 OpenAI 格式）
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.siliconflow.cn/v1")
    LLM_MODEL = os.getenv("LLM_MODEL", "Pro/zai-org/GLM-4.7")
    LLM_MAX_HISTORY = int(os.getenv("LLM_MAX_HISTORY", "10"))  # 滑动窗口：保留最近 N 条消息

    # VL 视觉模型配置（皮肤科图像分析）
    VL_MODEL = os.getenv("VL_MODEL", "Qwen/Qwen2.5-VL-72B-Instruct")
    VL_MAX_TOKENS = int(os.getenv("VL_MAX_TOKENS", "1024"))

    # OCR/说明书提取专用 VL 模型（轻量，速度优先）
    VL_OCR_MODEL = os.getenv("VL_OCR_MODEL", "Qwen/Qwen2.5-VL-72B-Instruct")

    
    # 健康指标配置
    METRIC_CONFIG = {
        'heart_rate': {
            'name': '心率',
            'unit': 'bpm',
            'icon': 'Heart',
            'color': '#FA383E',
            'normal_range': '60-100',
            'min': 60,
            'max': 100
        },
        'blood_pressure_sys': {
            'name': '收缩压',
            'unit': 'mmHg',
            'icon': 'Gauge',
            'color': '#0866FF',
            'normal_range': '90-140',
            'min': 90,
            'max': 140
        },
        'blood_pressure_dia': {
            'name': '舒张压',
            'unit': 'mmHg',
            'icon': 'Gauge',
            'color': '#0866FF',
            'normal_range': '60-90',
            'min': 60,
            'max': 90
        },
        'blood_sugar': {
            'name': '空腹血糖',
            'unit': 'mmol/L',
            'icon': 'Droplets',
            'color': '#F7B928',
            'normal_range': '3.9-6.1',
            'min': 3.9,
            'max': 6.1
        },
        'bmi': {
            'name': 'BMI',
            'unit': 'kg/m²',
            'icon': 'Activity',
            'color': '#31A24C',
            'normal_range': '18.5-24.9',
            'min': 18.5,
            'max': 24.9
        },
        'sleep': {
            'name': '睡眠时长',
            'unit': '小时',
            'icon': 'Moon',
            'color': '#8B5CF6',
            'normal_range': '7-9',
            'min': 7,
            'max': 9
        },
    }
    
    # 风险评估类型
    RISK_TYPES = {
        'cardiovascular': '心血管疾病风险',
        'diabetes': '糖尿病风险',
        'metabolic': '代谢综合征风险',
        'osteoporosis': '骨质疏松风险'
    }


config = Config()
