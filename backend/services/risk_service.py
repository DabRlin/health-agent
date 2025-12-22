"""
风险评估服务
使用真实的医学评估模型进行风险预测
"""
from datetime import datetime
from typing import Optional, List
from database import SessionLocal, User, RiskAssessment, UserHealthProfile
from sqlalchemy import desc
from config import config

# 导入 ML 模型
from services.ml_models import (
    FraminghamRiskCalculator,
    FINDRISCCalculator,
    MetabolicSyndromeCalculator
)
from services.ml_models.cardiovascular import CardiovascularRiskInput
from services.ml_models.diabetes import DiabetesRiskInput
from services.ml_models.metabolic import MetabolicRiskInput


class RiskService:
    """风险评估服务类 - 使用真实 ML 模型"""
    
    @classmethod
    def get_assessments(cls, user_id: Optional[int] = None) -> List[dict]:
        """获取风险评估列表"""
        db = SessionLocal()
        try:
            user = cls._get_user(db, user_id)
            if not user:
                return []
            
            assessments = db.query(RiskAssessment).filter(
                RiskAssessment.user_id == user.id
            ).order_by(desc(RiskAssessment.assessed_at)).all()
            
            return [{
                "id": a.id,
                "type": a.assessment_type,
                "name": a.name,
                "date": a.assessed_at.strftime("%Y-%m-%d"),
                "risk_level": a.risk_level,
                "score": a.score,
                "factors": a.factors,
                "recommendations": a.recommendations
            } for a in assessments]
        finally:
            db.close()
    
    @classmethod
    def create_assessment(cls, user_id: Optional[int], assessment_type: str) -> Optional[dict]:
        """
        创建风险评估 - 使用真实 ML 模型
        
        支持的评估类型:
        - cardiovascular: 心血管疾病风险 (Framingham)
        - diabetes: 糖尿病风险 (FINDRISC)
        - metabolic: 代谢综合征风险
        """
        db = SessionLocal()
        try:
            user = cls._get_user(db, user_id)
            if not user:
                return None
            
            # 获取用户健康档案
            profile = db.query(UserHealthProfile).filter(
                UserHealthProfile.user_id == user.id
            ).first()
            
            # 根据评估类型调用对应的 ML 模型
            if assessment_type == 'cardiovascular':
                result = cls._assess_cardiovascular(user, profile)
            elif assessment_type == 'diabetes':
                result = cls._assess_diabetes(user, profile)
            elif assessment_type == 'metabolic':
                result = cls._assess_metabolic(user, profile)
            else:
                # 其他类型使用通用评估
                result = cls._assess_generic(user, profile, assessment_type)
            
            # 保存评估结果
            assessment = RiskAssessment(
                user_id=user.id,
                assessment_type=assessment_type,
                name=config.RISK_TYPES.get(assessment_type, "健康风险"),
                risk_level=result['risk_level'],
                score=result['score'],
                factors=result['factors'],
                recommendations=result['recommendations']
            )
            db.add(assessment)
            db.commit()
            
            return {
                "id": assessment.id,
                "type": assessment.assessment_type,
                "name": assessment.name,
                "date": assessment.assessed_at.strftime("%Y-%m-%d"),
                "risk_level": assessment.risk_level,
                "score": assessment.score,
                "factors": assessment.factors,
                "recommendations": assessment.recommendations,
                "details": result.get('details', {})
            }
        finally:
            db.close()
    
    @classmethod
    def _assess_cardiovascular(cls, user, profile: Optional[UserHealthProfile]) -> dict:
        """心血管疾病风险评估 - Framingham Risk Score"""
        if not profile:
            return cls._get_incomplete_data_result('cardiovascular')
        
        # 构建输入数据
        input_data = CardiovascularRiskInput(
            age=user.age or 40,
            gender=user.gender or '男',
            total_cholesterol=profile.total_cholesterol or 200,
            hdl_cholesterol=profile.hdl_cholesterol or 50,
            systolic_bp=profile.systolic_bp or 120,
            on_bp_medication=profile.on_bp_medication or False,
            is_smoker=profile.is_smoker or False,
            has_diabetes=profile.has_diabetes or False
        )
        
        # 调用 Framingham 模型
        result = FraminghamRiskCalculator.calculate(input_data)
        
        return {
            'risk_level': result['risk_level'],
            'score': result['score'],
            'factors': result['factors'],
            'recommendations': result['recommendations'],
            'details': result['details']
        }
    
    @classmethod
    def _assess_diabetes(cls, user, profile: Optional[UserHealthProfile]) -> dict:
        """糖尿病风险评估 - FINDRISC"""
        if not profile:
            return cls._get_incomplete_data_result('diabetes')
        
        # 确定家族史类型
        family_diabetes = 'none'
        if profile.family_diabetes:
            family_diabetes = 'first_degree'
        
        # 构建输入数据
        input_data = DiabetesRiskInput(
            age=user.age or 40,
            bmi=profile.bmi or 24,
            waist=profile.waist or 85,
            gender=user.gender or '男',
            on_bp_medication=profile.on_bp_medication or False,
            history_high_glucose=profile.fasting_glucose and profile.fasting_glucose >= 5.6,
            daily_physical_activity=profile.exercise_frequency in ['3-4/week', 'daily'],
            daily_fruit_vegetable=profile.daily_fruit_vegetable if profile.daily_fruit_vegetable is not None else True,
            family_diabetes=family_diabetes
        )
        
        # 调用 FINDRISC 模型
        result = FINDRISCCalculator.calculate(input_data)
        
        return {
            'risk_level': result['risk_level'],
            'score': result['score'],
            'factors': result['factors'],
            'recommendations': result['recommendations'],
            'details': result['details']
        }
    
    @classmethod
    def _assess_metabolic(cls, user, profile: Optional[UserHealthProfile]) -> dict:
        """代谢综合征风险评估"""
        if not profile:
            return cls._get_incomplete_data_result('metabolic')
        
        # 构建输入数据
        input_data = MetabolicRiskInput(
            waist=profile.waist or 85,
            gender=user.gender or '男',
            triglycerides=profile.triglycerides or 120,
            hdl_cholesterol=profile.hdl_cholesterol or 50,
            systolic_bp=profile.systolic_bp or 120,
            diastolic_bp=profile.diastolic_bp or 80,
            fasting_glucose=profile.fasting_glucose or 5.0,
            on_bp_medication=profile.on_bp_medication or False,
            on_lipid_medication=False,
            on_glucose_medication=profile.has_diabetes or False
        )
        
        # 调用代谢综合征模型
        result = MetabolicSyndromeCalculator.calculate(input_data)
        
        return {
            'risk_level': result['risk_level'],
            'score': result['score'],
            'factors': result['factors'],
            'recommendations': result['recommendations'],
            'details': result['details']
        }
    
    @classmethod
    def _assess_generic(cls, user, profile: Optional[UserHealthProfile], 
                        assessment_type: str) -> dict:
        """通用风险评估（用于暂未实现专门模型的类型）"""
        # 基于已有数据进行简单评估
        factors = []
        score = 30  # 基础分
        
        if user.age:
            if user.age >= 60:
                factors.append({'name': '年龄偏大', 'positive': False, 'detail': f'{user.age}岁'})
                score += 15
            elif user.age >= 45:
                factors.append({'name': '年龄中等', 'positive': False, 'detail': f'{user.age}岁'})
                score += 5
            else:
                factors.append({'name': '年龄适中', 'positive': True, 'detail': f'{user.age}岁'})
        
        if profile:
            if profile.bmi and profile.bmi >= 25:
                factors.append({'name': 'BMI偏高', 'positive': False, 'detail': f'BMI {profile.bmi:.1f}'})
                score += 10
            elif profile.bmi:
                factors.append({'name': 'BMI正常', 'positive': True, 'detail': f'BMI {profile.bmi:.1f}'})
            
            if profile.is_smoker:
                factors.append({'name': '吸烟', 'positive': False, 'detail': ''})
                score += 15
            else:
                factors.append({'name': '不吸烟', 'positive': True, 'detail': ''})
            
            if profile.exercise_frequency in ['3-4/week', 'daily']:
                factors.append({'name': '运动习惯良好', 'positive': True, 'detail': ''})
                score -= 10
            else:
                factors.append({'name': '运动量不足', 'positive': False, 'detail': ''})
                score += 5
        
        score = max(0, min(100, score))
        
        if score < 30:
            risk_level = 'low'
        elif score < 60:
            risk_level = 'medium'
        else:
            risk_level = 'high'
        
        recommendations = [
            '保持健康的生活方式',
            '定期进行健康检查',
            '注意饮食均衡',
            '保持适量运动'
        ]
        
        if risk_level == 'high':
            recommendations.insert(0, '建议就医进行专业检查')
        
        return {
            'risk_level': risk_level,
            'score': score,
            'factors': factors,
            'recommendations': recommendations,
            'details': {'model': 'generic', 'note': '基于基础健康数据的简单评估'}
        }
    
    @classmethod
    def _get_incomplete_data_result(cls, assessment_type: str) -> dict:
        """当健康档案数据不完整时返回的结果"""
        return {
            'risk_level': 'unknown',
            'score': 0,
            'factors': [
                {'name': '健康档案不完整', 'positive': False, 
                 'detail': '请先完善健康档案以获得准确评估'}
            ],
            'recommendations': [
                '请完善您的健康档案信息',
                '建议录入身高、体重、血压等基础数据',
                '如有近期体检报告，请上传相关指标',
                '完善数据后可获得更准确的风险评估'
            ],
            'details': {'error': 'incomplete_profile', 'assessment_type': assessment_type}
        }
    
    @classmethod
    def _get_user(cls, db, user_id: Optional[int] = None):
        """获取用户"""
        if user_id:
            return db.query(User).filter(User.id == user_id).first()
        return db.query(User).first()
