"""
骨质疏松骨折风险评估 - FRAX® (Fracture Risk Assessment Tool)
WHO 骨折风险评估工具，计算未来10年主要骨质疏松性骨折及髋部骨折概率

参考文献:
- Kanis JA, et al. FRAX and the assessment of fracture probability in men and women
  from the UK. Osteoporosis International. 2008;19(4):385-397.
- WHO Scientific Group. Assessment of osteoporosis at the primary health care level.
  WHO Technical Report. Geneva: WHO Press, 2008.

说明:
  完整 FRAX® 需要 DXA 骨密度数据，本实现采用无 BMD 版本（临床常用简化版），
  基于临床风险因子计算10年骨折概率，适用于初级保健筛查场景。
"""
import math
from typing import Dict, Optional
from dataclasses import dataclass, field


@dataclass
class OsteoporosisRiskInput:
    """骨质疏松风险评估输入参数（FRAX® 无 BMD 版本）"""
    age: int                          # 年龄 (40-90岁)
    gender: str                       # 性别 ('男' 或 '女')
    bmi: float                        # BMI (kg/m²)
    previous_fracture: bool           # 既往脆性骨折史
    parent_hip_fracture: bool         # 父母髋部骨折史
    is_smoker: bool                   # 当前吸烟
    glucocorticoids: bool             # 糖皮质激素使用（≥3个月）
    rheumatoid_arthritis: bool        # 类风湿关节炎
    secondary_osteoporosis: bool      # 继发性骨质疏松（糖尿病、甲亢等）
    alcohol_3_or_more: bool           # 每日饮酒≥3单位


class FRAXCalculator:
    """
    FRAX® 骨折风险计算器（无 BMD 简化版）

    基于 WHO FRAX® 中国人群参数，计算10年内：
    - 主要骨质疏松性骨折概率（髋部、脊柱、前臂、肱骨）
    - 髋部骨折概率

    风险等级划分（参考 NOF/IOF 指南）：
    - 低风险：主要骨折概率 < 10%
    - 中风险：10% ≤ 主要骨折概率 < 20%
    - 高风险：主要骨折概率 ≥ 20% 或髋部骨折概率 ≥ 3%
    """

    # FRAX® 中国人群基线生存率参数（无 BMD 版本近似值）
    # 基于 Kanis et al. 2010 中国人群校正系数
    BASELINE_MAJOR = {
        '男': {'S0': 0.9941, 'mean_cov': 0.8736},
        '女': {'S0': 0.9872, 'mean_cov': 1.0613},
    }
    BASELINE_HIP = {
        '男': {'S0': 0.9985, 'mean_cov': 0.5836},
        '女': {'S0': 0.9964, 'mean_cov': 0.8684},
    }

    # 各风险因子的 beta 系数（对数风险比，基于 FRAX® 文献）
    BETA_MAJOR = {
        'ln_age':               2.4,    # 年龄（对数）
        'ln_bmi':              -1.0,    # BMI（对数，BMI 越高骨折风险越低）
        'previous_fracture':    0.84,
        'parent_hip_fracture':  0.29,
        'is_smoker':            0.29,
        'glucocorticoids':      0.57,
        'rheumatoid_arthritis': 0.36,
        'secondary_osteoporosis': 0.42,
        'alcohol_3_or_more':    0.19,
    }
    BETA_HIP = {
        'ln_age':               3.24,
        'ln_bmi':              -1.44,
        'previous_fracture':    0.82,
        'parent_hip_fracture':  0.75,
        'is_smoker':            0.47,
        'glucocorticoids':      0.57,
        'rheumatoid_arthritis': 0.36,
        'secondary_osteoporosis': 0.0,
        'alcohol_3_or_more':    0.07,
    }

    @classmethod
    def calculate(cls, input_data: OsteoporosisRiskInput) -> Dict:
        """
        计算骨质疏松骨折风险

        Returns:
            {
                'major_fracture_prob': float,  # 10年主要骨折概率 (%)
                'hip_fracture_prob': float,    # 10年髋部骨折概率 (%)
                'risk_level': str,             # 风险等级
                'score': int,                  # 标准化评分 (0-100)
                'factors': list,               # 风险因素分析
                'recommendations': list,       # 健康建议
                'details': dict                # 详细信息
            }
        """
        age = max(40, min(90, input_data.age))
        bmi = max(15.0, min(40.0, input_data.bmi))
        gender = input_data.gender if input_data.gender in ('男', '女') else '男'

        # 计算协变量线性组合
        cov_major = cls._calc_covariate(age, bmi, input_data, cls.BETA_MAJOR)
        cov_hip   = cls._calc_covariate(age, bmi, input_data, cls.BETA_HIP)

        # 计算10年骨折概率
        major_prob = cls._calc_probability(
            cov_major,
            cls.BASELINE_MAJOR[gender]['S0'],
            cls.BASELINE_MAJOR[gender]['mean_cov']
        )
        hip_prob = cls._calc_probability(
            cov_hip,
            cls.BASELINE_HIP[gender]['S0'],
            cls.BASELINE_HIP[gender]['mean_cov']
        )

        # 风险等级
        risk_level = cls._determine_risk_level(major_prob, hip_prob)

        # 标准化评分（0-100，以主要骨折概率30%为满分参考）
        score = min(100, int(major_prob / 30.0 * 100))

        factors = cls._build_factors(input_data, major_prob, hip_prob, bmi)
        recommendations = cls._build_recommendations(risk_level, input_data)

        return {
            'major_fracture_prob': round(major_prob, 1),
            'hip_fracture_prob': round(hip_prob, 1),
            'risk_level': risk_level,
            'score': score,
            'factors': factors,
            'recommendations': recommendations,
            'details': {
                'model': 'FRAX® (No BMD)',
                'reference': 'Kanis JA et al. Osteoporosis International, 2008',
                'major_fracture_10yr': f'{major_prob:.1f}%',
                'hip_fracture_10yr': f'{hip_prob:.1f}%',
                'note': '基于临床风险因子，无骨密度数据版本'
            }
        }

    @classmethod
    def _calc_covariate(cls, age: float, bmi: float,
                        inp: OsteoporosisRiskInput, beta: dict) -> float:
        cov = (
            beta['ln_age']               * math.log(age)
            + beta['ln_bmi']             * math.log(bmi)
            + beta['previous_fracture']  * int(inp.previous_fracture)
            + beta['parent_hip_fracture']* int(inp.parent_hip_fracture)
            + beta['is_smoker']          * int(inp.is_smoker)
            + beta['glucocorticoids']    * int(inp.glucocorticoids)
            + beta['rheumatoid_arthritis'] * int(inp.rheumatoid_arthritis)
            + beta['secondary_osteoporosis'] * int(inp.secondary_osteoporosis)
            + beta['alcohol_3_or_more']  * int(inp.alcohol_3_or_more)
        )
        return cov

    @classmethod
    def _calc_probability(cls, cov: float, s0: float, mean_cov: float) -> float:
        """基于 FRAX® 生存分析公式计算10年骨折概率"""
        prob = 1.0 - math.pow(s0, math.exp(cov - mean_cov))
        return prob * 100.0

    @classmethod
    def _determine_risk_level(cls, major_prob: float, hip_prob: float) -> str:
        if major_prob >= 20.0 or hip_prob >= 3.0:
            return 'high'
        elif major_prob >= 10.0:
            return 'medium'
        else:
            return 'low'

    @classmethod
    def _build_factors(cls, inp: OsteoporosisRiskInput,
                       major_prob: float, hip_prob: float, bmi: float) -> list:
        factors = []

        # 年龄
        if inp.age >= 70:
            factors.append({'name': '高龄', 'positive': False,
                            'detail': f'{inp.age}岁，骨折风险随年龄显著增加'})
        elif inp.age >= 55:
            factors.append({'name': '中老年', 'positive': False,
                            'detail': f'{inp.age}岁，需关注骨密度变化'})
        else:
            factors.append({'name': '年龄适中', 'positive': True,
                            'detail': f'{inp.age}岁'})

        # BMI
        if bmi < 18.5:
            factors.append({'name': 'BMI 偏低', 'positive': False,
                            'detail': f'BMI {bmi:.1f}，低体重是骨质疏松重要危险因素'})
        elif bmi >= 25:
            factors.append({'name': 'BMI 正常偏高', 'positive': True,
                            'detail': f'BMI {bmi:.1f}，对骨骼有一定保护作用'})
        else:
            factors.append({'name': 'BMI 正常', 'positive': True,
                            'detail': f'BMI {bmi:.1f}'})

        # 既往骨折
        if inp.previous_fracture:
            factors.append({'name': '既往脆性骨折史', 'positive': False,
                            'detail': '显著增加再次骨折风险'})

        # 父母髋部骨折
        if inp.parent_hip_fracture:
            factors.append({'name': '父母髋部骨折史', 'positive': False,
                            'detail': '家族遗传因素增加骨折风险'})

        # 吸烟
        if inp.is_smoker:
            factors.append({'name': '吸烟', 'positive': False,
                            'detail': '吸烟加速骨量流失'})
        else:
            factors.append({'name': '不吸烟', 'positive': True, 'detail': ''})

        # 糖皮质激素
        if inp.glucocorticoids:
            factors.append({'name': '长期使用糖皮质激素', 'positive': False,
                            'detail': '激素类药物显著降低骨密度'})

        # 类风湿关节炎
        if inp.rheumatoid_arthritis:
            factors.append({'name': '类风湿关节炎', 'positive': False,
                            'detail': '炎症及相关治疗增加骨折风险'})

        # 继发性骨质疏松
        if inp.secondary_osteoporosis:
            factors.append({'name': '继发性骨质疏松相关疾病', 'positive': False,
                            'detail': '糖尿病、甲状腺疾病等增加骨质疏松风险'})

        # 饮酒
        if inp.alcohol_3_or_more:
            factors.append({'name': '大量饮酒', 'positive': False,
                            'detail': '每日≥3单位酒精影响骨代谢'})

        return factors

    @classmethod
    def _build_recommendations(cls, risk_level: str,
                                inp: OsteoporosisRiskInput) -> list:
        recs = []

        if risk_level == 'high':
            recs.append('建议尽快就医，进行 DXA 骨密度检测，评估是否需要药物治疗')
            recs.append('在医生指导下考虑抗骨质疏松药物治疗（双膦酸盐等）')
        elif risk_level == 'medium':
            recs.append('建议进行 DXA 骨密度检测以明确骨质疏松程度')
            recs.append('与医生讨论是否需要预防性干预措施')

        recs.append('每日补充钙质 1000-1200mg（饮食+补充剂）')
        recs.append('每日补充维生素 D 800-1000 IU，促进钙吸收')
        recs.append('进行负重运动和抗阻训练，如步行、太极拳、哑铃练习')
        recs.append('预防跌倒：改善家居环境，穿防滑鞋，必要时使用助行器')

        if inp.is_smoker:
            recs.append('戒烟可显著降低骨量流失速度')
        if inp.alcohol_3_or_more:
            recs.append('减少饮酒，每日不超过1-2单位酒精')

        return recs
