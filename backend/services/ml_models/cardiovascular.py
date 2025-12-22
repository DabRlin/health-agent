"""
心血管疾病风险评估 - Framingham Risk Score
基于 Framingham Heart Study 的经典心血管风险评估公式

参考文献:
- D'Agostino RB Sr, et al. General cardiovascular risk profile for use in primary care.
  Circulation. 2008;117(6):743-753.
"""
import math
from typing import Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class CardiovascularRiskInput:
    """心血管风险评估输入参数"""
    age: int                      # 年龄 (30-79岁)
    gender: str                   # 性别 ('男' 或 '女')
    total_cholesterol: float      # 总胆固醇 (mg/dL)
    hdl_cholesterol: float        # HDL胆固醇 (mg/dL)
    systolic_bp: float            # 收缩压 (mmHg)
    on_bp_medication: bool        # 是否服用降压药
    is_smoker: bool               # 是否吸烟
    has_diabetes: bool            # 是否有糖尿病


class FraminghamRiskCalculator:
    """
    Framingham 心血管风险计算器
    
    计算 10 年内发生心血管事件（心肌梗死、冠心病死亡、中风等）的风险概率
    """
    
    # 男性系数
    MALE_COEFFICIENTS = {
        'ln_age': 3.06117,
        'ln_total_chol': 1.12370,
        'ln_hdl': -0.93263,
        'ln_sbp_untreated': 1.93303,
        'ln_sbp_treated': 1.99881,
        'smoker': 0.65451,
        'diabetes': 0.57367,
        'baseline_survival': 0.88936,
        'mean_coefficient_sum': 23.9802
    }
    
    # 女性系数
    FEMALE_COEFFICIENTS = {
        'ln_age': 2.32888,
        'ln_total_chol': 1.20904,
        'ln_hdl': -0.70833,
        'ln_sbp_untreated': 2.76157,
        'ln_sbp_treated': 2.82263,
        'smoker': 0.52873,
        'diabetes': 0.69154,
        'baseline_survival': 0.95012,
        'mean_coefficient_sum': 26.1931
    }
    
    @classmethod
    def calculate(cls, input_data: CardiovascularRiskInput) -> Dict:
        """
        计算心血管风险
        
        Returns:
            {
                'risk_percentage': float,  # 10年风险百分比
                'risk_level': str,         # 风险等级 (low/medium/high)
                'score': int,              # 风险评分 (0-100)
                'factors': list,           # 风险因素分析
                'recommendations': list,   # 健康建议
                'details': dict            # 详细计算数据
            }
        """
        # 验证输入
        if not cls._validate_input(input_data):
            return cls._get_default_result("输入数据不完整或超出范围")
        
        # 选择性别对应的系数
        is_male = input_data.gender == '男'
        coef = cls.MALE_COEFFICIENTS if is_male else cls.FEMALE_COEFFICIENTS
        
        # 计算各项得分
        ln_age = math.log(input_data.age)
        ln_total_chol = math.log(input_data.total_cholesterol)
        ln_hdl = math.log(input_data.hdl_cholesterol)
        ln_sbp = math.log(input_data.systolic_bp)
        
        # 计算系数和
        coefficient_sum = (
            coef['ln_age'] * ln_age +
            coef['ln_total_chol'] * ln_total_chol +
            coef['ln_hdl'] * ln_hdl +
            (coef['ln_sbp_treated'] if input_data.on_bp_medication else coef['ln_sbp_untreated']) * ln_sbp +
            (coef['smoker'] if input_data.is_smoker else 0) +
            (coef['diabetes'] if input_data.has_diabetes else 0)
        )
        
        # 计算10年风险
        risk = 1 - math.pow(coef['baseline_survival'], 
                           math.exp(coefficient_sum - coef['mean_coefficient_sum']))
        risk_percentage = round(risk * 100, 1)
        
        # 确定风险等级
        risk_level = cls._get_risk_level(risk_percentage)
        
        # 转换为0-100评分（风险越高分数越高）
        score = min(100, int(risk_percentage * 3))  # 大约33%风险对应100分
        
        # 分析风险因素
        factors = cls._analyze_factors(input_data)
        
        # 生成建议
        recommendations = cls._generate_recommendations(input_data, risk_level)
        
        return {
            'risk_percentage': risk_percentage,
            'risk_level': risk_level,
            'score': score,
            'factors': factors,
            'recommendations': recommendations,
            'details': {
                'age': input_data.age,
                'gender': input_data.gender,
                'total_cholesterol': input_data.total_cholesterol,
                'hdl_cholesterol': input_data.hdl_cholesterol,
                'systolic_bp': input_data.systolic_bp,
                'coefficient_sum': round(coefficient_sum, 4),
                'model': 'Framingham Risk Score (2008)'
            }
        }
    
    @classmethod
    def _validate_input(cls, data: CardiovascularRiskInput) -> bool:
        """验证输入数据"""
        if data.age < 30 or data.age > 79:
            return False
        if data.gender not in ['男', '女']:
            return False
        if data.total_cholesterol <= 0 or data.hdl_cholesterol <= 0:
            return False
        if data.systolic_bp <= 0:
            return False
        return True
    
    @classmethod
    def _get_risk_level(cls, risk_percentage: float) -> str:
        """根据风险百分比确定风险等级"""
        if risk_percentage < 10:
            return 'low'
        elif risk_percentage < 20:
            return 'medium'
        else:
            return 'high'
    
    @classmethod
    def _analyze_factors(cls, data: CardiovascularRiskInput) -> list:
        """分析风险因素"""
        factors = []
        
        # 年龄
        if data.age >= 55:
            factors.append({'name': '年龄偏大', 'positive': False, 'detail': f'{data.age}岁'})
        else:
            factors.append({'name': '年龄适中', 'positive': True, 'detail': f'{data.age}岁'})
        
        # 胆固醇
        if data.total_cholesterol >= 240:
            factors.append({'name': '总胆固醇偏高', 'positive': False, 
                          'detail': f'{data.total_cholesterol} mg/dL (建议<200)'})
        elif data.total_cholesterol >= 200:
            factors.append({'name': '总胆固醇临界', 'positive': False,
                          'detail': f'{data.total_cholesterol} mg/dL'})
        else:
            factors.append({'name': '总胆固醇正常', 'positive': True,
                          'detail': f'{data.total_cholesterol} mg/dL'})
        
        # HDL
        if data.hdl_cholesterol < 40:
            factors.append({'name': 'HDL胆固醇偏低', 'positive': False,
                          'detail': f'{data.hdl_cholesterol} mg/dL (建议>40)'})
        elif data.hdl_cholesterol >= 60:
            factors.append({'name': 'HDL胆固醇良好', 'positive': True,
                          'detail': f'{data.hdl_cholesterol} mg/dL'})
        else:
            factors.append({'name': 'HDL胆固醇正常', 'positive': True,
                          'detail': f'{data.hdl_cholesterol} mg/dL'})
        
        # 血压
        if data.systolic_bp >= 140:
            factors.append({'name': '血压偏高', 'positive': False,
                          'detail': f'{data.systolic_bp} mmHg (建议<140)'})
        elif data.systolic_bp >= 130:
            factors.append({'name': '血压临界', 'positive': False,
                          'detail': f'{data.systolic_bp} mmHg'})
        else:
            factors.append({'name': '血压正常', 'positive': True,
                          'detail': f'{data.systolic_bp} mmHg'})
        
        # 吸烟
        if data.is_smoker:
            factors.append({'name': '吸烟', 'positive': False, 'detail': '吸烟显著增加心血管风险'})
        else:
            factors.append({'name': '不吸烟', 'positive': True, 'detail': ''})
        
        # 糖尿病
        if data.has_diabetes:
            factors.append({'name': '患有糖尿病', 'positive': False, 'detail': '糖尿病增加心血管风险'})
        else:
            factors.append({'name': '无糖尿病', 'positive': True, 'detail': ''})
        
        # 降压药
        if data.on_bp_medication:
            factors.append({'name': '服用降压药', 'positive': False, 'detail': '表明存在高血压病史'})
        
        return factors
    
    @classmethod
    def _generate_recommendations(cls, data: CardiovascularRiskInput, risk_level: str) -> list:
        """生成健康建议"""
        recommendations = []
        
        # 基础建议
        if risk_level == 'high':
            recommendations.append('建议尽快就医，进行详细的心血管检查')
            recommendations.append('严格遵医嘱服药，定期复查')
        elif risk_level == 'medium':
            recommendations.append('建议每年进行心血管健康检查')
            recommendations.append('积极改善生活方式，预防风险升高')
        
        # 针对性建议
        if data.total_cholesterol >= 200:
            recommendations.append('控制饮食中的饱和脂肪和胆固醇摄入')
            recommendations.append('增加膳食纤维摄入，如燕麦、豆类')
        
        if data.hdl_cholesterol < 40:
            recommendations.append('增加有氧运动，每周至少150分钟')
            recommendations.append('适量摄入健康脂肪，如橄榄油、坚果')
        
        if data.systolic_bp >= 130:
            recommendations.append('减少钠盐摄入，每日不超过6克')
            recommendations.append('保持健康体重，避免肥胖')
        
        if data.is_smoker:
            recommendations.append('强烈建议戒烟，戒烟后心血管风险会逐渐降低')
        
        if data.has_diabetes:
            recommendations.append('严格控制血糖，定期监测糖化血红蛋白')
        
        # 通用建议
        recommendations.append('保持规律作息，保证充足睡眠')
        recommendations.append('保持积极乐观的心态，避免过度压力')
        
        return recommendations[:8]  # 最多返回8条建议
    
    @classmethod
    def _get_default_result(cls, error_msg: str) -> Dict:
        """返回默认结果（当输入无效时）"""
        return {
            'risk_percentage': 0,
            'risk_level': 'unknown',
            'score': 0,
            'factors': [],
            'recommendations': ['请提供完整的健康数据以进行评估'],
            'details': {'error': error_msg}
        }


def calculate_cardiovascular_risk(
    age: int,
    gender: str,
    total_cholesterol: float,
    hdl_cholesterol: float,
    systolic_bp: float,
    on_bp_medication: bool = False,
    is_smoker: bool = False,
    has_diabetes: bool = False
) -> Dict:
    """
    便捷函数：计算心血管风险
    
    Args:
        age: 年龄 (30-79)
        gender: 性别 ('男' 或 '女')
        total_cholesterol: 总胆固醇 (mg/dL)
        hdl_cholesterol: HDL胆固醇 (mg/dL)
        systolic_bp: 收缩压 (mmHg)
        on_bp_medication: 是否服用降压药
        is_smoker: 是否吸烟
        has_diabetes: 是否有糖尿病
    
    Returns:
        风险评估结果字典
    """
    input_data = CardiovascularRiskInput(
        age=age,
        gender=gender,
        total_cholesterol=total_cholesterol,
        hdl_cholesterol=hdl_cholesterol,
        systolic_bp=systolic_bp,
        on_bp_medication=on_bp_medication,
        is_smoker=is_smoker,
        has_diabetes=has_diabetes
    )
    return FraminghamRiskCalculator.calculate(input_data)
