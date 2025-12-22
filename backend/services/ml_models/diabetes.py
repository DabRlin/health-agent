"""
糖尿病风险评估 - FINDRISC (Finnish Diabetes Risk Score)
芬兰糖尿病风险评分，用于评估未来10年内发生2型糖尿病的风险

参考文献:
- Lindström J, Tuomilehto J. The diabetes risk score: a practical tool to predict 
  type 2 diabetes risk. Diabetes Care. 2003;26(3):725-731.
"""
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class DiabetesRiskInput:
    """糖尿病风险评估输入参数"""
    age: int                          # 年龄
    bmi: float                        # BMI (kg/m²)
    waist: float                      # 腰围 (cm)
    gender: str                       # 性别 ('男' 或 '女')
    on_bp_medication: bool            # 是否服用降压药
    history_high_glucose: bool        # 是否有高血糖史
    daily_physical_activity: bool     # 是否每天运动至少30分钟
    daily_fruit_vegetable: bool       # 是否每天吃蔬果
    family_diabetes: str              # 家族糖尿病史 ('none'/'second_degree'/'first_degree')


class FINDRISCCalculator:
    """
    FINDRISC 糖尿病风险计算器
    
    评估未来10年内发生2型糖尿病的风险
    总分范围: 0-26分
    """
    
    @classmethod
    def calculate(cls, input_data: DiabetesRiskInput) -> Dict:
        """
        计算糖尿病风险
        
        Returns:
            {
                'total_score': int,        # 总分 (0-26)
                'risk_percentage': float,  # 10年风险百分比
                'risk_level': str,         # 风险等级
                'score': int,              # 标准化评分 (0-100)
                'factors': list,           # 风险因素分析
                'recommendations': list,   # 健康建议
                'score_breakdown': dict    # 各项得分明细
            }
        """
        score_breakdown = {}
        total_score = 0
        
        # 1. 年龄评分 (0-4分)
        age_score = cls._score_age(input_data.age)
        score_breakdown['age'] = {'value': input_data.age, 'score': age_score, 'label': '年龄'}
        total_score += age_score
        
        # 2. BMI评分 (0-3分)
        bmi_score = cls._score_bmi(input_data.bmi)
        score_breakdown['bmi'] = {'value': round(input_data.bmi, 1), 'score': bmi_score, 'label': 'BMI'}
        total_score += bmi_score
        
        # 3. 腰围评分 (0-4分)
        waist_score = cls._score_waist(input_data.waist, input_data.gender)
        score_breakdown['waist'] = {'value': round(input_data.waist, 1), 'score': waist_score, 'label': '腰围'}
        total_score += waist_score
        
        # 4. 运动评分 (0-2分)
        activity_score = 0 if input_data.daily_physical_activity else 2
        score_breakdown['activity'] = {
            'value': '是' if input_data.daily_physical_activity else '否',
            'score': activity_score,
            'label': '每日运动'
        }
        total_score += activity_score
        
        # 5. 蔬果摄入评分 (0-1分)
        diet_score = 0 if input_data.daily_fruit_vegetable else 1
        score_breakdown['diet'] = {
            'value': '是' if input_data.daily_fruit_vegetable else '否',
            'score': diet_score,
            'label': '每日蔬果'
        }
        total_score += diet_score
        
        # 6. 降压药评分 (0-2分)
        bp_med_score = 2 if input_data.on_bp_medication else 0
        score_breakdown['bp_medication'] = {
            'value': '是' if input_data.on_bp_medication else '否',
            'score': bp_med_score,
            'label': '服用降压药'
        }
        total_score += bp_med_score
        
        # 7. 高血糖史评分 (0-5分)
        glucose_score = 5 if input_data.history_high_glucose else 0
        score_breakdown['high_glucose'] = {
            'value': '是' if input_data.history_high_glucose else '否',
            'score': glucose_score,
            'label': '高血糖史'
        }
        total_score += glucose_score
        
        # 8. 家族史评分 (0-5分)
        family_score = cls._score_family_history(input_data.family_diabetes)
        score_breakdown['family'] = {
            'value': cls._get_family_label(input_data.family_diabetes),
            'score': family_score,
            'label': '家族史'
        }
        total_score += family_score
        
        # 计算风险等级和百分比
        risk_level, risk_percentage = cls._get_risk_level(total_score)
        
        # 标准化为0-100分
        normalized_score = min(100, int(total_score * 100 / 26))
        
        # 分析因素
        factors = cls._analyze_factors(input_data, score_breakdown)
        
        # 生成建议
        recommendations = cls._generate_recommendations(input_data, risk_level, score_breakdown)
        
        return {
            'total_score': total_score,
            'risk_percentage': risk_percentage,
            'risk_level': risk_level,
            'score': normalized_score,
            'factors': factors,
            'recommendations': recommendations,
            'score_breakdown': score_breakdown,
            'details': {
                'model': 'FINDRISC (Finnish Diabetes Risk Score)',
                'max_score': 26,
                'assessment_period': '10年'
            }
        }
    
    @classmethod
    def _score_age(cls, age: int) -> int:
        """年龄评分"""
        if age < 45:
            return 0
        elif age < 55:
            return 2
        elif age < 65:
            return 3
        else:
            return 4
    
    @classmethod
    def _score_bmi(cls, bmi: float) -> int:
        """BMI评分"""
        if bmi < 25:
            return 0
        elif bmi < 30:
            return 1
        else:
            return 3
    
    @classmethod
    def _score_waist(cls, waist: float, gender: str) -> int:
        """腰围评分（男女标准不同）"""
        if gender == '男':
            if waist < 94:
                return 0
            elif waist < 102:
                return 3
            else:
                return 4
        else:  # 女性
            if waist < 80:
                return 0
            elif waist < 88:
                return 3
            else:
                return 4
    
    @classmethod
    def _score_family_history(cls, family: str) -> int:
        """家族史评分"""
        if family == 'first_degree':  # 一级亲属（父母、兄弟姐妹）
            return 5
        elif family == 'second_degree':  # 二级亲属（祖父母、叔伯等）
            return 3
        else:
            return 0
    
    @classmethod
    def _get_family_label(cls, family: str) -> str:
        """获取家族史标签"""
        labels = {
            'none': '无',
            'second_degree': '二级亲属',
            'first_degree': '一级亲属'
        }
        return labels.get(family, '无')
    
    @classmethod
    def _get_risk_level(cls, score: int) -> tuple:
        """根据总分确定风险等级和概率"""
        if score < 7:
            return 'low', 1.0  # 约1%
        elif score < 12:
            return 'low', 4.0  # 约4%
        elif score < 15:
            return 'medium', 17.0  # 约17%
        elif score < 21:
            return 'high', 33.0  # 约33%
        else:
            return 'high', 50.0  # 约50%
    
    @classmethod
    def _analyze_factors(cls, data: DiabetesRiskInput, breakdown: dict) -> list:
        """分析风险因素"""
        factors = []
        
        # 年龄
        if breakdown['age']['score'] >= 3:
            factors.append({'name': '年龄偏大', 'positive': False, 'detail': f"{data.age}岁"})
        else:
            factors.append({'name': '年龄适中', 'positive': True, 'detail': f"{data.age}岁"})
        
        # BMI
        if data.bmi >= 30:
            factors.append({'name': 'BMI偏高(肥胖)', 'positive': False, 
                          'detail': f"BMI {data.bmi:.1f} (建议<25)"})
        elif data.bmi >= 25:
            factors.append({'name': 'BMI偏高(超重)', 'positive': False,
                          'detail': f"BMI {data.bmi:.1f} (建议<25)"})
        else:
            factors.append({'name': 'BMI正常', 'positive': True,
                          'detail': f"BMI {data.bmi:.1f}"})
        
        # 腰围
        threshold = 94 if data.gender == '男' else 80
        if data.waist >= threshold:
            factors.append({'name': '腰围偏大', 'positive': False,
                          'detail': f"{data.waist:.0f}cm (建议<{threshold}cm)"})
        else:
            factors.append({'name': '腰围正常', 'positive': True,
                          'detail': f"{data.waist:.0f}cm"})
        
        # 运动
        if data.daily_physical_activity:
            factors.append({'name': '运动习惯良好', 'positive': True, 'detail': '每日运动≥30分钟'})
        else:
            factors.append({'name': '运动量不足', 'positive': False, 'detail': '建议每日运动≥30分钟'})
        
        # 饮食
        if data.daily_fruit_vegetable:
            factors.append({'name': '饮食习惯良好', 'positive': True, 'detail': '每日摄入蔬果'})
        else:
            factors.append({'name': '蔬果摄入不足', 'positive': False, 'detail': '建议每日摄入蔬果'})
        
        # 高血糖史
        if data.history_high_glucose:
            factors.append({'name': '有高血糖史', 'positive': False, 'detail': '曾检出血糖偏高'})
        else:
            factors.append({'name': '无高血糖史', 'positive': True, 'detail': ''})
        
        # 家族史
        if data.family_diabetes == 'first_degree':
            factors.append({'name': '一级亲属有糖尿病', 'positive': False, 'detail': '父母或兄弟姐妹'})
        elif data.family_diabetes == 'second_degree':
            factors.append({'name': '二级亲属有糖尿病', 'positive': False, 'detail': '祖父母或叔伯'})
        else:
            factors.append({'name': '无家族糖尿病史', 'positive': True, 'detail': ''})
        
        # 降压药
        if data.on_bp_medication:
            factors.append({'name': '服用降压药', 'positive': False, 'detail': '高血压与糖尿病风险相关'})
        
        return factors
    
    @classmethod
    def _generate_recommendations(cls, data: DiabetesRiskInput, risk_level: str, 
                                   breakdown: dict) -> list:
        """生成健康建议"""
        recommendations = []
        
        # 基于风险等级的建议
        if risk_level == 'high':
            recommendations.append('建议尽快就医，进行口服葡萄糖耐量试验(OGTT)')
            recommendations.append('定期监测空腹血糖和糖化血红蛋白(HbA1c)')
        elif risk_level == 'medium':
            recommendations.append('建议每年检测空腹血糖')
            recommendations.append('积极改善生活方式，预防糖尿病发生')
        
        # 针对性建议
        if data.bmi >= 25:
            recommendations.append('建议减轻体重，目标BMI<25')
            recommendations.append('每减轻5%体重，糖尿病风险可降低50%以上')
        
        if breakdown['waist']['score'] > 0:
            recommendations.append('注意减少腹部脂肪，控制腰围')
        
        if not data.daily_physical_activity:
            recommendations.append('增加运动量，每天至少30分钟中等强度运动')
            recommendations.append('可选择快走、游泳、骑车等有氧运动')
        
        if not data.daily_fruit_vegetable:
            recommendations.append('增加蔬菜水果摄入，每日至少500克')
        
        if data.history_high_glucose:
            recommendations.append('已有高血糖史，需更加重视血糖监测')
        
        # 通用建议
        recommendations.append('减少精制碳水化合物和含糖饮料摄入')
        recommendations.append('保持规律作息，保证充足睡眠')
        
        return recommendations[:8]


def calculate_diabetes_risk(
    age: int,
    bmi: float,
    waist: float,
    gender: str,
    on_bp_medication: bool = False,
    history_high_glucose: bool = False,
    daily_physical_activity: bool = True,
    daily_fruit_vegetable: bool = True,
    family_diabetes: str = 'none'
) -> Dict:
    """
    便捷函数：计算糖尿病风险
    
    Args:
        age: 年龄
        bmi: BMI (kg/m²)
        waist: 腰围 (cm)
        gender: 性别 ('男' 或 '女')
        on_bp_medication: 是否服用降压药
        history_high_glucose: 是否有高血糖史
        daily_physical_activity: 是否每天运动≥30分钟
        daily_fruit_vegetable: 是否每天吃蔬果
        family_diabetes: 家族史 ('none'/'second_degree'/'first_degree')
    
    Returns:
        风险评估结果字典
    """
    input_data = DiabetesRiskInput(
        age=age,
        bmi=bmi,
        waist=waist,
        gender=gender,
        on_bp_medication=on_bp_medication,
        history_high_glucose=history_high_glucose,
        daily_physical_activity=daily_physical_activity,
        daily_fruit_vegetable=daily_fruit_vegetable,
        family_diabetes=family_diabetes
    )
    return FINDRISCCalculator.calculate(input_data)
