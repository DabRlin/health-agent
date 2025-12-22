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
    
    # Dify API 配置
    DIFY_ENABLED = os.getenv("DIFY_ENABLED", "false").lower() == "true"
    DIFY_API_KEY = os.getenv("DIFY_API_KEY", "")
    DIFY_BASE_URL = os.getenv("DIFY_BASE_URL", "http://localhost/v1")
    
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
