"""
代谢综合征风险评估
基于 IDF (国际糖尿病联盟) 和 NCEP ATP III 诊断标准

参考文献:
- Alberti KG, et al. Harmonizing the metabolic syndrome. Circulation. 2009;120(16):1640-1645.
- NCEP ATP III Guidelines. JAMA. 2001;285(19):2486-2497.
"""
from typing import Dict, List
from dataclasses import dataclass


@dataclass
class MetabolicRiskInput:
    """代谢综合征风险评估输入参数"""
    waist: float                  # 腰围 (cm)
    gender: str                   # 性别 ('男' 或 '女')
    triglycerides: float          # 甘油三酯 (mg/dL)
    hdl_cholesterol: float        # HDL胆固醇 (mg/dL)
    systolic_bp: float            # 收缩压 (mmHg)
    diastolic_bp: float           # 舒张压 (mmHg)
    fasting_glucose: float        # 空腹血糖 (mmol/L)
    on_bp_medication: bool = False        # 是否服用降压药
    on_lipid_medication: bool = False     # 是否服用降脂药
    on_glucose_medication: bool = False   # 是否服用降糖药


class MetabolicSyndromeCalculator:
    """
    代谢综合征风险计算器
    
    诊断标准 (满足3项及以上即可诊断):
    1. 腹型肥胖: 男性腰围≥90cm，女性≥80cm (亚洲标准)
    2. 甘油三酯升高: ≥150 mg/dL 或正在接受治疗
    3. HDL降低: 男性<40 mg/dL，女性<50 mg/dL 或正在接受治疗
    4. 血压升高: ≥130/85 mmHg 或正在接受治疗
    5. 空腹血糖升高: ≥5.6 mmol/L (100 mg/dL) 或正在接受治疗
    """
    
    # 亚洲人群腰围标准
    WAIST_THRESHOLD = {'男': 90, '女': 80}
    
    # HDL标准
    HDL_THRESHOLD = {'男': 40, '女': 50}
    
    @classmethod
    def calculate(cls, input_data: MetabolicRiskInput) -> Dict:
        """
        计算代谢综合征风险
        
        Returns:
            {
                'has_metabolic_syndrome': bool,  # 是否患有代谢综合征
                'criteria_met': int,             # 满足的标准数量
                'risk_level': str,               # 风险等级
                'score': int,                    # 风险评分 (0-100)
                'criteria_details': list,        # 各项标准详情
                'factors': list,                 # 风险因素
                'recommendations': list,         # 健康建议
            }
        """
        criteria_details = []
        criteria_met = 0
        
        # 1. 腹型肥胖
        waist_threshold = cls.WAIST_THRESHOLD.get(input_data.gender, 90)
        waist_abnormal = input_data.waist >= waist_threshold
        criteria_details.append({
            'name': '腹型肥胖',
            'criterion': f'腰围≥{waist_threshold}cm',
            'value': f'{input_data.waist:.0f}cm',
            'abnormal': waist_abnormal,
            'met': waist_abnormal
        })
        if waist_abnormal:
            criteria_met += 1
        
        # 2. 甘油三酯升高
        tg_abnormal = input_data.triglycerides >= 150 or input_data.on_lipid_medication
        criteria_details.append({
            'name': '甘油三酯升高',
            'criterion': '≥150 mg/dL 或正在治疗',
            'value': f'{input_data.triglycerides:.0f} mg/dL',
            'abnormal': input_data.triglycerides >= 150,
            'on_treatment': input_data.on_lipid_medication,
            'met': tg_abnormal
        })
        if tg_abnormal:
            criteria_met += 1
        
        # 3. HDL降低
        hdl_threshold = cls.HDL_THRESHOLD.get(input_data.gender, 40)
        hdl_abnormal = input_data.hdl_cholesterol < hdl_threshold or input_data.on_lipid_medication
        criteria_details.append({
            'name': 'HDL胆固醇降低',
            'criterion': f'<{hdl_threshold} mg/dL 或正在治疗',
            'value': f'{input_data.hdl_cholesterol:.0f} mg/dL',
            'abnormal': input_data.hdl_cholesterol < hdl_threshold,
            'on_treatment': input_data.on_lipid_medication,
            'met': hdl_abnormal
        })
        if hdl_abnormal:
            criteria_met += 1
        
        # 4. 血压升高
        bp_abnormal = (input_data.systolic_bp >= 130 or 
                      input_data.diastolic_bp >= 85 or 
                      input_data.on_bp_medication)
        criteria_details.append({
            'name': '血压升高',
            'criterion': '≥130/85 mmHg 或正在治疗',
            'value': f'{input_data.systolic_bp:.0f}/{input_data.diastolic_bp:.0f} mmHg',
            'abnormal': input_data.systolic_bp >= 130 or input_data.diastolic_bp >= 85,
            'on_treatment': input_data.on_bp_medication,
            'met': bp_abnormal
        })
        if bp_abnormal:
            criteria_met += 1
        
        # 5. 空腹血糖升高
        glucose_abnormal = input_data.fasting_glucose >= 5.6 or input_data.on_glucose_medication
        criteria_details.append({
            'name': '空腹血糖升高',
            'criterion': '≥5.6 mmol/L 或正在治疗',
            'value': f'{input_data.fasting_glucose:.1f} mmol/L',
            'abnormal': input_data.fasting_glucose >= 5.6,
            'on_treatment': input_data.on_glucose_medication,
            'met': glucose_abnormal
        })
        if glucose_abnormal:
            criteria_met += 1
        
        # 判断是否患有代谢综合征
        has_metabolic_syndrome = criteria_met >= 3
        
        # 确定风险等级
        risk_level = cls._get_risk_level(criteria_met)
        
        # 计算风险评分 (0-100)
        score = criteria_met * 20  # 每满足一项20分
        
        # 分析风险因素
        factors = cls._analyze_factors(input_data, criteria_details)
        
        # 生成建议
        recommendations = cls._generate_recommendations(
            input_data, criteria_details, has_metabolic_syndrome
        )
        
        return {
            'has_metabolic_syndrome': has_metabolic_syndrome,
            'criteria_met': criteria_met,
            'total_criteria': 5,
            'risk_level': risk_level,
            'score': score,
            'criteria_details': criteria_details,
            'factors': factors,
            'recommendations': recommendations,
            'details': {
                'model': 'IDF/NCEP ATP III 代谢综合征诊断标准',
                'diagnosis_threshold': '满足5项中的3项及以上',
                'population': '亚洲人群标准'
            }
        }
    
    @classmethod
    def _get_risk_level(cls, criteria_met: int) -> str:
        """根据满足的标准数确定风险等级"""
        if criteria_met == 0:
            return 'low'
        elif criteria_met <= 2:
            return 'medium'
        else:
            return 'high'
    
    @classmethod
    def _analyze_factors(cls, data: MetabolicRiskInput, criteria: list) -> list:
        """分析风险因素"""
        factors = []
        
        for item in criteria:
            if item['met']:
                factors.append({
                    'name': item['name'],
                    'positive': False,
                    'detail': f"{item['value']} ({item['criterion']})"
                })
            else:
                factors.append({
                    'name': f"{item['name']}正常",
                    'positive': True,
                    'detail': item['value']
                })
        
        return factors
    
    @classmethod
    def _generate_recommendations(cls, data: MetabolicRiskInput, 
                                   criteria: list, has_syndrome: bool) -> list:
        """生成健康建议"""
        recommendations = []
        
        if has_syndrome:
            recommendations.append('您已符合代谢综合征诊断标准，建议尽快就医')
            recommendations.append('代谢综合征会显著增加心血管疾病和糖尿病风险')
            recommendations.append('需要在医生指导下进行综合治疗')
        
        # 针对各项异常的建议
        for item in criteria:
            if item['met']:
                if item['name'] == '腹型肥胖':
                    recommendations.append('减少腹部脂肪是改善代谢的关键')
                    recommendations.append('建议通过饮食控制和运动减轻体重')
                elif item['name'] == '甘油三酯升高':
                    recommendations.append('减少精制碳水化合物和酒精摄入')
                    recommendations.append('增加富含Omega-3的食物，如深海鱼')
                elif item['name'] == 'HDL胆固醇降低':
                    recommendations.append('增加有氧运动可提高HDL水平')
                    recommendations.append('戒烟有助于提高HDL胆固醇')
                elif item['name'] == '血压升高':
                    recommendations.append('限制钠盐摄入，每日不超过6克')
                    recommendations.append('增加钾的摄入，多吃蔬菜水果')
                elif item['name'] == '空腹血糖升高':
                    recommendations.append('控制碳水化合物摄入，选择低GI食物')
                    recommendations.append('餐后适当活动有助于控制血糖')
        
        # 通用建议
        if not has_syndrome:
            recommendations.append('保持健康生活方式，预防代谢综合征')
        
        recommendations.append('定期体检，监测各项代谢指标')
        
        return recommendations[:8]


def calculate_metabolic_risk(
    waist: float,
    gender: str,
    triglycerides: float,
    hdl_cholesterol: float,
    systolic_bp: float,
    diastolic_bp: float,
    fasting_glucose: float,
    on_bp_medication: bool = False,
    on_lipid_medication: bool = False,
    on_glucose_medication: bool = False
) -> Dict:
    """
    便捷函数：计算代谢综合征风险
    
    Args:
        waist: 腰围 (cm)
        gender: 性别 ('男' 或 '女')
        triglycerides: 甘油三酯 (mg/dL)
        hdl_cholesterol: HDL胆固醇 (mg/dL)
        systolic_bp: 收缩压 (mmHg)
        diastolic_bp: 舒张压 (mmHg)
        fasting_glucose: 空腹血糖 (mmol/L)
        on_bp_medication: 是否服用降压药
        on_lipid_medication: 是否服用降脂药
        on_glucose_medication: 是否服用降糖药
    
    Returns:
        风险评估结果字典
    """
    input_data = MetabolicRiskInput(
        waist=waist,
        gender=gender,
        triglycerides=triglycerides,
        hdl_cholesterol=hdl_cholesterol,
        systolic_bp=systolic_bp,
        diastolic_bp=diastolic_bp,
        fasting_glucose=fasting_glucose,
        on_bp_medication=on_bp_medication,
        on_lipid_medication=on_lipid_medication,
        on_glucose_medication=on_glucose_medication
    )
    return MetabolicSyndromeCalculator.calculate(input_data)
