"""
用户服务
"""
from datetime import datetime
from typing import Optional, List
from database import SessionLocal, User, HealthRecord, Consultation, RiskAssessment, HealthTag, HealthReport, UserHealthProfile
from sqlalchemy import desc


class UserService:
    """用户服务类"""
    
    @classmethod
    def get_user(cls, user_id: Optional[int] = None) -> Optional[dict]:
        """获取用户信息"""
        db = SessionLocal()
        try:
            if user_id:
                user = db.query(User).filter(User.id == user_id).first()
            else:
                user = db.query(User).first()
            
            if not user:
                return None
            
            health_days = (datetime.now() - user.created_at).days
            
            return {
                "id": user.id,
                "name": user.name,
                "gender": user.gender,
                "age": user.age,
                "birthday": user.birthday,
                "phone": user.phone,
                "email": user.email,
                "location": user.location,
                "avatar": user.avatar,
                "health_score": user.health_score,
                "health_days": health_days,
                "created_at": user.created_at.strftime("%Y-%m-%d")
            }
        finally:
            db.close()
    
    @classmethod
    def get_user_stats(cls, user_id: Optional[int] = None) -> List[dict]:
        """获取用户健康统计"""
        db = SessionLocal()
        try:
            if user_id:
                user = db.query(User).filter(User.id == user_id).first()
            else:
                user = db.query(User).first()
            
            if not user:
                return []
            
            record_count = db.query(HealthRecord).filter(HealthRecord.user_id == user.id).count()
            consultation_count = db.query(Consultation).filter(Consultation.user_id == user.id).count()
            assessment_count = db.query(RiskAssessment).filter(RiskAssessment.user_id == user.id).count()
            
            return [
                {"label": "健康评分", "value": str(user.health_score), "unit": "分", "icon": "Heart", "color": "#FA383E"},
                {"label": "体检次数", "value": str(record_count), "unit": "次", "icon": "FileText", "color": "#0866FF"},
                {"label": "问诊记录", "value": str(consultation_count), "unit": "次", "icon": "Activity", "color": "#31A24C"},
                {"label": "风险评估", "value": str(assessment_count), "unit": "次", "icon": "Shield", "color": "#F7B928"},
            ]
        finally:
            db.close()
    
    @classmethod
    def get_user_tags(cls, user_id: Optional[int] = None) -> List[dict]:
        """获取用户健康标签"""
        db = SessionLocal()
        try:
            if user_id:
                user = db.query(User).filter(User.id == user_id).first()
            else:
                user = db.query(User).first()
            
            if not user:
                return []
            
            tags = db.query(HealthTag).filter(HealthTag.user_id == user.id).all()
            return [{"name": t.name, "type": t.tag_type} for t in tags]
        finally:
            db.close()
    
    @classmethod
    def get_user_reports(cls, user_id: Optional[int] = None) -> List[dict]:
        """获取用户健康报告"""
        db = SessionLocal()
        try:
            if user_id:
                user = db.query(User).filter(User.id == user_id).first()
            else:
                user = db.query(User).first()
            
            if not user:
                return []
            
            reports = db.query(HealthReport).filter(
                HealthReport.user_id == user.id
            ).order_by(desc(HealthReport.created_at)).all()
            
            return [{
                "id": r.id,
                "name": r.name,
                "type": r.report_type,
                "date": r.created_at.strftime("%Y-%m-%d")
            } for r in reports]
        finally:
            db.close()
    
    @classmethod
    def update_user(cls, user_id: int, data: dict) -> tuple[bool, Optional[dict], Optional[str]]:
        """
        更新用户信息
        
        Args:
            user_id: 用户ID
            data: 要更新的字段
            
        Returns:
            (success, user_data, error_message)
        """
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False, None, "用户不存在"
            
            # 允许更新的字段
            allowed_fields = ['name', 'gender', 'age', 'birthday', 'phone', 'email', 'location', 'avatar']
            
            for field in allowed_fields:
                if field in data and data[field] is not None:
                    setattr(user, field, data[field])
            
            db.commit()
            
            # 返回更新后的用户信息
            health_days = (datetime.now() - user.created_at).days
            
            return True, {
                "id": user.id,
                "name": user.name,
                "gender": user.gender,
                "age": user.age,
                "birthday": user.birthday,
                "phone": user.phone,
                "email": user.email,
                "location": user.location,
                "avatar": user.avatar,
                "health_score": user.health_score,
                "health_days": health_days,
                "created_at": user.created_at.strftime("%Y-%m-%d")
            }, None
            
        except Exception as e:
            db.rollback()
            print(f"更新用户信息错误: {e}")
            return False, None, "更新失败，请稍后重试"
        finally:
            db.close()

    @classmethod
    def get_health_profile(cls, user_id: int) -> Optional[dict]:
        """获取用户健康档案（用于 ML 模型的基础数据）"""
        db = SessionLocal()
        try:
            profile = db.query(UserHealthProfile).filter(
                UserHealthProfile.user_id == user_id
            ).first()
            if not profile:
                return None
            return {
                "height": profile.height,
                "weight": profile.weight,
                "bmi": profile.bmi,
                "waist": profile.waist,
                "systolic_bp": profile.systolic_bp,
                "diastolic_bp": profile.diastolic_bp,
                "on_bp_medication": profile.on_bp_medication,
                "total_cholesterol": profile.total_cholesterol,
                "hdl_cholesterol": profile.hdl_cholesterol,
                "ldl_cholesterol": profile.ldl_cholesterol,
                "triglycerides": profile.triglycerides,
                "fasting_glucose": profile.fasting_glucose,
                "hba1c": profile.hba1c,
                "is_smoker": profile.is_smoker,
                "smoking_years": profile.smoking_years,
                "alcohol_frequency": profile.alcohol_frequency,
                "exercise_frequency": profile.exercise_frequency,
                "exercise_minutes_per_week": profile.exercise_minutes_per_week,
                "has_diabetes": profile.has_diabetes,
                "has_hypertension": profile.has_hypertension,
                "has_heart_disease": profile.has_heart_disease,
                "family_diabetes": profile.family_diabetes,
                "family_heart_disease": profile.family_heart_disease,
                "family_hypertension": profile.family_hypertension,
                "daily_fruit_vegetable": profile.daily_fruit_vegetable,
                "high_salt_diet": profile.high_salt_diet,
                "updated_at": profile.updated_at.strftime("%Y-%m-%d") if profile.updated_at else None,
            }
        finally:
            db.close()

    @classmethod
    def update_health_profile(cls, user_id: int, data: dict) -> tuple[bool, Optional[dict], Optional[str]]:
        """更新用户健康档案，不存在则创建"""
        db = SessionLocal()
        try:
            profile = db.query(UserHealthProfile).filter(
                UserHealthProfile.user_id == user_id
            ).first()
            if not profile:
                profile = UserHealthProfile(user_id=user_id)
                db.add(profile)

            allowed_fields = [
                "height", "weight", "bmi", "waist",
                "systolic_bp", "diastolic_bp", "on_bp_medication",
                "total_cholesterol", "hdl_cholesterol", "ldl_cholesterol",
                "triglycerides", "fasting_glucose", "hba1c",
                "is_smoker", "smoking_years", "alcohol_frequency",
                "exercise_frequency", "exercise_minutes_per_week",
                "has_diabetes", "has_hypertension", "has_heart_disease",
                "family_diabetes", "family_heart_disease", "family_hypertension",
                "daily_fruit_vegetable", "high_salt_diet",
            ]
            for field in allowed_fields:
                if field in data and data[field] is not None:
                    setattr(profile, field, data[field])

            # 自动计算 BMI（如果传入了身高和体重）
            h = data.get("height") or profile.height
            w = data.get("weight") or profile.weight
            if h and w and h > 0:
                profile.bmi = round(w / ((h / 100) ** 2), 1)

            db.commit()
            return True, cls.get_health_profile(user_id), None
        except Exception as e:
            db.rollback()
            print(f"更新健康档案错误: {e}")
            return False, None, "更新失败，请稍后重试"
        finally:
            db.close()
