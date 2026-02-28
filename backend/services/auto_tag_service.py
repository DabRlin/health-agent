"""
自动健康标签评估服务
根据用户健康档案和指标数据，自动生成系统标签
"""
from database import SessionLocal, HealthTag, UserHealthProfile, HealthMetric
from sqlalchemy import desc


# 评估规则：每条规则 (name, tag_type, check_fn)
# check_fn(profile: UserHealthProfile) -> bool
_PROFILE_RULES = [
    # -------- 体重/BMI --------
    ("BMI偏低",    "warning",  lambda p: p.bmi is not None and p.bmi < 18.5),
    ("体重正常",   "positive", lambda p: p.bmi is not None and 18.5 <= p.bmi <= 24.9),
    ("超重",       "warning",  lambda p: p.bmi is not None and 25.0 <= p.bmi <= 27.9),
    ("肥胖",       "warning",  lambda p: p.bmi is not None and p.bmi >= 28.0),

    # -------- 血压 --------
    ("血压正常",   "positive", lambda p: _bp_normal(p)),
    ("血压偏高",   "warning",  lambda p: p.systolic_bp is not None and (p.systolic_bp >= 130 or (p.diastolic_bp or 0) >= 85)),
    ("高血压风险", "warning",  lambda p: p.systolic_bp is not None and (p.systolic_bp >= 140 or (p.diastolic_bp or 0) >= 90)),

    # -------- 血糖 --------
    ("血糖正常",   "positive", lambda p: p.fasting_glucose is not None and p.fasting_glucose < 6.1),
    ("血糖偏高",   "warning",  lambda p: p.fasting_glucose is not None and 6.1 <= p.fasting_glucose < 7.0),
    ("糖尿病风险", "warning",  lambda p: p.fasting_glucose is not None and p.fasting_glucose >= 7.0),

    # -------- 糖化血红蛋白 --------
    ("HbA1c偏高",  "warning",  lambda p: p.hba1c is not None and p.hba1c >= 6.5),

    # -------- 血脂 --------
    ("总胆固醇偏高", "warning", lambda p: p.total_cholesterol is not None and p.total_cholesterol > 200),
    ("LDL偏高",    "warning",  lambda p: p.ldl_cholesterol is not None and p.ldl_cholesterol > 130),
    ("甘油三酯偏高","warning", lambda p: p.triglycerides is not None and p.triglycerides > 150),

    # -------- 生活习惯 --------
    ("吸烟者",     "warning",  lambda p: p.is_smoker is True),
    ("规律运动",   "positive", lambda p: p.exercise_frequency in ("3-4/week", "daily")),
    ("运动不足",   "warning",  lambda p: p.exercise_frequency in ("never", "1-2/week")),
    ("高盐饮食",   "warning",  lambda p: p.high_salt_diet is True),
    ("饮食均衡",   "positive", lambda p: p.daily_fruit_vegetable is True and p.high_salt_diet is not True),

    # -------- 病史 --------
    ("糖尿病史",   "warning",  lambda p: p.has_diabetes is True),
    ("高血压史",   "warning",  lambda p: p.has_hypertension is True),
    ("心脏病史",   "warning",  lambda p: p.has_heart_disease is True),
    ("家族糖尿病史","warning", lambda p: p.family_diabetes is True),
    ("家族心脏病史","warning", lambda p: p.family_heart_disease is True),
    ("家族高血压史","warning", lambda p: p.family_hypertension is True),
]


def _bp_normal(p: UserHealthProfile) -> bool:
    if p.systolic_bp is None or p.diastolic_bp is None:
        return False
    return p.systolic_bp < 130 and p.diastolic_bp < 85


class AutoTagService:

    @classmethod
    def evaluate_and_sync(cls, user_id: int) -> list[dict]:
        """
        根据健康档案评估系统标签，并与数据库同步（删除过期 + 新增触发）。
        返回当前所有标签列表（系统 + 用户）。
        """
        db = SessionLocal()
        try:
            profile = db.query(UserHealthProfile).filter(
                UserHealthProfile.user_id == user_id
            ).first()

            # 计算应生成的系统标签集合
            should_have: set[str] = set()
            if profile:
                for name, tag_type, check_fn in _PROFILE_RULES:
                    try:
                        if check_fn(profile):
                            should_have.add(name)
                    except Exception:
                        pass

            # 当前数据库里的系统标签
            existing_sys = db.query(HealthTag).filter(
                HealthTag.user_id == user_id,
                HealthTag.source == 'system'
            ).all()
            existing_names = {t.name: t for t in existing_sys}

            # 删除已不满足条件的系统标签
            for name, tag in existing_names.items():
                if name not in should_have:
                    db.delete(tag)

            # 新增满足条件但尚未存在的系统标签
            for name in should_have:
                if name not in existing_names:
                    tag_type = next(
                        (t for n, t, _ in _PROFILE_RULES if n == name), 'neutral'
                    )
                    db.add(HealthTag(
                        user_id=user_id,
                        name=name,
                        tag_type=tag_type,
                        source='system'
                    ))

            db.commit()

            # 返回全部标签
            all_tags = db.query(HealthTag).filter(
                HealthTag.user_id == user_id
            ).order_by(HealthTag.source.desc(), HealthTag.created_at).all()

            return [{"id": t.id, "name": t.name, "type": t.tag_type, "source": t.source}
                    for t in all_tags]
        finally:
            db.close()
