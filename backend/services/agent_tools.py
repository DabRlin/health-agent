"""
Agent 工具链定义
包含工具函数实现和供 LLM Function Calling 使用的 schema 定义
"""
import json
from typing import Optional
from services.health_service import HealthService
from services.risk_service import RiskService
from services.trend_service import TrendService
from services.user_service import UserService


# ==================== 工具函数实现 ====================

def get_health_metrics(user_id: int, metric_type: Optional[str] = None) -> str:
    """
    查询用户最新健康指标
    
    Args:
        user_id: 用户ID
        metric_type: 指标类型，可选值：heart_rate, blood_pressure_sys,
                     blood_pressure_dia, blood_sugar, bmi, sleep。
                     不传则返回所有指标。
    Returns:
        JSON 字符串，包含指标数据
    """
    metrics = HealthService.get_metrics(user_id)
    if not metrics:
        return json.dumps({"error": "暂无健康指标数据，请先录入健康数据"}, ensure_ascii=False)
    
    if metric_type:
        type_name_map = {
            "heart_rate": "心率",
            "blood_pressure_sys": "收缩压",
            "blood_pressure_dia": "舒张压",
            "blood_sugar": "空腹血糖",
            "bmi": "BMI",
            "sleep": "睡眠时长",
        }
        name = type_name_map.get(metric_type)
        metrics = [m for m in metrics if m.get("name") == name]
        if not metrics:
            return json.dumps({"error": f"暂无 {metric_type} 数据"}, ensure_ascii=False)
    
    return json.dumps({"metrics": metrics}, ensure_ascii=False)


def get_health_trend(user_id: int, metric_type: str, days: int = 30) -> str:
    """
    分析指定健康指标的历史趋势和异常情况
    
    Args:
        user_id: 用户ID
        metric_type: 指标类型，可选值：heart_rate, blood_pressure_sys,
                     blood_pressure_dia, blood_sugar, bmi, sleep
        days: 分析天数，默认 30 天
    Returns:
        JSON 字符串，包含趋势分析、异常检测和统计信息
    """
    result = TrendService.get_metric_trend(user_id, metric_type, days)
    if not result or not result.get("data"):
        return json.dumps({"error": f"近 {days} 天内暂无 {metric_type} 数据"}, ensure_ascii=False)
    
    # 精简返回，避免数据过多占用 token
    summary = {
        "metric_type": metric_type,
        "days": days,
        "data_points": len(result.get("data", [])),
        "statistics": result.get("statistics", {}),
        "trend": result.get("trend", {}),
        "anomalies": {
            "count": len(result.get("anomalies", {}).get("anomaly_indices", [])),
            "details": result.get("anomalies", {}).get("anomaly_details", [])[:3],
        },
        "prediction": result.get("prediction", {}).get("values", [])[:3],
    }
    return json.dumps(summary, ensure_ascii=False)


def run_risk_assessment(user_id: int, assessment_type: str) -> str:
    """
    运行健康风险评估模型
    
    Args:
        user_id: 用户ID
        assessment_type: 评估类型，可选值：
                         cardiovascular（心血管，Framingham 模型），
                         diabetes（糖尿病，FINDRISC 模型），
                         metabolic（代谢综合征）
    Returns:
        JSON 字符串，包含风险等级、评分、风险因素和建议
    """
    valid_types = ["cardiovascular", "diabetes", "metabolic"]
    if assessment_type not in valid_types:
        return json.dumps(
            {"error": f"不支持的评估类型，请使用：{', '.join(valid_types)}"},
            ensure_ascii=False
        )
    
    result = RiskService.create_assessment(user_id, assessment_type)
    if not result:
        return json.dumps({"error": "评估失败，请确认用户健康档案已完善"}, ensure_ascii=False)
    
    return json.dumps(result, ensure_ascii=False)


def get_user_profile(user_id: int) -> str:
    """
    获取用户基本信息和健康档案
    
    Args:
        user_id: 用户ID
    Returns:
        JSON 字符串，包含用户基本信息和健康评分
    """
    user = UserService.get_user(user_id)
    if not user:
        return json.dumps({"error": "用户不存在"}, ensure_ascii=False)
    
    return json.dumps({"user": user}, ensure_ascii=False)


def add_health_metric(user_id: int, metric_type: str, value: float) -> str:
    """
    录入新的健康指标数据
    
    Args:
        user_id: 用户ID
        metric_type: 指标类型，可选值：heart_rate, blood_pressure_sys,
                     blood_pressure_dia, blood_sugar, bmi, sleep
        value: 指标数值
    Returns:
        JSON 字符串，包含录入结果
    """
    result = HealthService.add_metric(user_id, metric_type, value)
    if not result:
        return json.dumps(
            {"error": f"录入失败，不支持的指标类型：{metric_type}"},
            ensure_ascii=False
        )
    
    return json.dumps({"success": True, "metric": result}, ensure_ascii=False)


# ==================== 工具执行调度 ====================

TOOL_FUNCTIONS = {
    "get_health_metrics": get_health_metrics,
    "get_health_trend": get_health_trend,
    "run_risk_assessment": run_risk_assessment,
    "get_user_profile": get_user_profile,
    "add_health_metric": add_health_metric,
}


def execute_tool(tool_name: str, tool_args: dict, user_id: int) -> str:
    """执行工具调用，自动注入 user_id"""
    func = TOOL_FUNCTIONS.get(tool_name)
    if not func:
        return json.dumps({"error": f"未知工具：{tool_name}"}, ensure_ascii=False)
    
    try:
        return func(user_id=user_id, **tool_args)
    except Exception as e:
        return json.dumps({"error": f"工具执行失败：{str(e)}"}, ensure_ascii=False)


# ==================== LLM Function Calling Schema ====================

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_health_metrics",
            "description": "查询用户最新的健康指标数据，包括心率、血压、血糖、BMI、睡眠时长等。当用户询问自己的健康数据或某项指标时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "metric_type": {
                        "type": "string",
                        "description": "指标类型。不传则返回所有指标。",
                        "enum": [
                            "heart_rate",
                            "blood_pressure_sys",
                            "blood_pressure_dia",
                            "blood_sugar",
                            "bmi",
                            "sleep"
                        ]
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_health_trend",
            "description": "分析用户某项健康指标的历史趋势、异常检测和预测。当用户询问某指标的变化趋势、是否有异常、近期走势时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "metric_type": {
                        "type": "string",
                        "description": "要分析的指标类型",
                        "enum": [
                            "heart_rate",
                            "blood_pressure_sys",
                            "blood_pressure_dia",
                            "blood_sugar",
                            "bmi",
                            "sleep"
                        ]
                    },
                    "days": {
                        "type": "integer",
                        "description": "分析最近多少天的数据，默认 30 天",
                        "default": 30
                    }
                },
                "required": ["metric_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_risk_assessment",
            "description": "运行医学风险评估模型，评估用户的心血管疾病风险、糖尿病风险或代谢综合征风险。当用户询问健康风险、是否有患病风险时调用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "assessment_type": {
                        "type": "string",
                        "description": "评估类型：cardiovascular（心血管，Framingham 模型），diabetes（糖尿病，FINDRISC 模型），metabolic（代谢综合征）",
                        "enum": ["cardiovascular", "diabetes", "metabolic"]
                    }
                },
                "required": ["assessment_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_profile",
            "description": "获取用户的基本信息，包括姓名、年龄、性别、健康评分等。当需要了解用户基本情况时调用。",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_health_metric",
            "description": "录入用户的健康指标数据。当用户明确表示要记录某项健康数据时调用，调用前需向用户确认数值。",
            "parameters": {
                "type": "object",
                "properties": {
                    "metric_type": {
                        "type": "string",
                        "description": "指标类型",
                        "enum": [
                            "heart_rate",
                            "blood_pressure_sys",
                            "blood_pressure_dia",
                            "blood_sugar",
                            "bmi",
                            "sleep"
                        ]
                    },
                    "value": {
                        "type": "number",
                        "description": "指标数值"
                    }
                },
                "required": ["metric_type", "value"]
            }
        }
    }
]
