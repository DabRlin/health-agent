"""
穿戴设备数据模拟器
生成符合真实规律的健康数据
"""
import random
import math
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from models import SessionLocal, DeviceReading, DailyHealthSummary, UserHealthProfile, User


class DeviceSimulator:
    """模拟智能穿戴设备数据生成"""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.db = SessionLocal()
        
    def __del__(self):
        if hasattr(self, 'db'):
            self.db.close()
    
    # ==================== 心率模拟 ====================
    
    def generate_heart_rate(self, timestamp: datetime) -> float:
        """
        生成符合生理规律的心率数据
        - 睡眠时: 50-65 bpm
        - 静息时: 60-80 bpm
        - 轻度活动: 80-100 bpm
        - 运动时: 100-150 bpm
        """
        hour = timestamp.hour
        
        # 基础心率（因人而异）
        base_hr = random.uniform(65, 75)
        
        # 根据时间段调整
        if 0 <= hour < 6:  # 深夜睡眠
            hr = base_hr - random.uniform(10, 20)
        elif 6 <= hour < 8:  # 起床
            hr = base_hr + random.uniform(-5, 10)
        elif 8 <= hour < 12:  # 上午活动
            hr = base_hr + random.uniform(0, 20)
        elif 12 <= hour < 14:  # 午餐后
            hr = base_hr + random.uniform(5, 15)
        elif 14 <= hour < 18:  # 下午
            hr = base_hr + random.uniform(0, 15)
        elif 18 <= hour < 20:  # 晚餐/运动时间
            # 30% 概率在运动
            if random.random() < 0.3:
                hr = base_hr + random.uniform(30, 60)
            else:
                hr = base_hr + random.uniform(5, 15)
        elif 20 <= hour < 23:  # 晚间放松
            hr = base_hr + random.uniform(-5, 10)
        else:  # 准备睡觉
            hr = base_hr - random.uniform(5, 15)
        
        # 添加随机波动
        hr += random.gauss(0, 3)
        
        return max(45, min(180, round(hr, 1)))
    
    # ==================== 步数模拟 ====================
    
    def generate_daily_steps(self, date: datetime) -> Dict:
        """
        生成一天的步数数据
        返回每小时步数和总步数
        """
        hourly_steps = {}
        
        # 不同时段的步数分布
        step_patterns = {
            (0, 6): (0, 50),       # 睡眠
            (6, 8): (200, 800),    # 起床活动
            (8, 9): (500, 2000),   # 通勤
            (9, 12): (100, 500),   # 上午工作
            (12, 14): (300, 1000), # 午餐
            (14, 18): (100, 500),  # 下午工作
            (18, 19): (500, 2000), # 下班通勤
            (19, 21): (200, 1500), # 晚间活动/运动
            (21, 24): (50, 300),   # 晚间休息
        }
        
        total = 0
        for (start, end), (min_steps, max_steps) in step_patterns.items():
            for hour in range(start, end):
                steps = random.randint(min_steps, max_steps)
                hourly_steps[hour] = steps
                total += steps
        
        # 周末可能更多户外活动
        if date.weekday() >= 5:
            total = int(total * random.uniform(1.1, 1.4))
        
        return {
            'hourly': hourly_steps,
            'total': total,
            'distance': round(total * 0.0007, 2),  # 约 0.7m/步
            'calories': round(total * 0.04, 1)     # 约 0.04 kcal/步
        }
    
    # ==================== 睡眠模拟 ====================
    
    def generate_sleep_data(self, date: datetime) -> Dict:
        """
        生成睡眠数据
        - 入睡时间: 22:00 - 01:00
        - 睡眠时长: 5-9 小时
        - 睡眠周期: 浅睡 -> 深睡 -> REM -> 浅睡 (约90分钟一个周期)
        """
        # 入睡时间（前一天晚上）
        sleep_hour = random.randint(22, 25) % 24
        sleep_minute = random.randint(0, 59)
        
        # 睡眠时长（小时）
        duration = random.uniform(5.5, 8.5)
        
        # 计算起床时间
        wake_hour = (sleep_hour + int(duration)) % 24
        wake_minute = (sleep_minute + int((duration % 1) * 60)) % 60
        
        # 睡眠阶段分布（占比）
        deep_ratio = random.uniform(0.15, 0.25)   # 深睡 15-25%
        rem_ratio = random.uniform(0.20, 0.25)    # REM 20-25%
        light_ratio = 1 - deep_ratio - rem_ratio  # 浅睡 剩余
        
        deep_duration = round(duration * deep_ratio, 2)
        rem_duration = round(duration * rem_ratio, 2)
        light_duration = round(duration * light_ratio, 2)
        
        # 觉醒次数
        awake_count = random.randint(0, 3)
        
        # 睡眠质量评分 (0-100)
        quality_score = self._calculate_sleep_quality(
            duration, deep_duration, awake_count
        )
        
        return {
            'sleep_start': f"{sleep_hour:02d}:{sleep_minute:02d}",
            'sleep_end': f"{wake_hour:02d}:{wake_minute:02d}",
            'duration': round(duration, 2),
            'deep_sleep': deep_duration,
            'light_sleep': light_duration,
            'rem_sleep': rem_duration,
            'awake_count': awake_count,
            'quality_score': quality_score
        }
    
    def _calculate_sleep_quality(self, duration: float, deep: float, awake: int) -> int:
        """计算睡眠质量评分"""
        score = 50
        
        # 时长评分 (7-8小时最佳)
        if 7 <= duration <= 8:
            score += 20
        elif 6 <= duration < 7 or 8 < duration <= 9:
            score += 10
        elif duration < 6:
            score -= 10
        
        # 深睡比例评分
        deep_ratio = deep / duration if duration > 0 else 0
        if deep_ratio >= 0.2:
            score += 20
        elif deep_ratio >= 0.15:
            score += 10
        else:
            score -= 5
        
        # 觉醒次数评分
        score -= awake * 5
        
        return max(0, min(100, score))
    
    # ==================== 血氧模拟 ====================
    
    def generate_spo2(self, timestamp: datetime) -> float:
        """
        生成血氧饱和度数据
        正常范围: 95-100%
        睡眠时可能略低: 93-98%
        """
        hour = timestamp.hour
        
        if 0 <= hour < 6:  # 睡眠时
            spo2 = random.uniform(94, 98)
        else:
            spo2 = random.uniform(96, 100)
        
        return round(spo2, 1)
    
    # ==================== 血压模拟 ====================
    
    def generate_blood_pressure(self, timestamp: datetime, 
                                 has_hypertension: bool = False) -> Dict:
        """
        生成血压数据
        正常: 收缩压 90-120, 舒张压 60-80
        高血压: 收缩压 130-160, 舒张压 85-100
        """
        hour = timestamp.hour
        
        if has_hypertension:
            base_sys = random.uniform(135, 155)
            base_dia = random.uniform(85, 95)
        else:
            base_sys = random.uniform(105, 125)
            base_dia = random.uniform(65, 80)
        
        # 早晨血压略高
        if 6 <= hour < 10:
            base_sys += random.uniform(5, 15)
            base_dia += random.uniform(3, 8)
        # 下午略低
        elif 14 <= hour < 18:
            base_sys -= random.uniform(0, 5)
            base_dia -= random.uniform(0, 3)
        
        return {
            'systolic': round(base_sys),
            'diastolic': round(base_dia)
        }
    
    # ==================== 批量生成数据 ====================
    
    def generate_day_readings(self, date: datetime, 
                               interval_minutes: int = 5) -> List[DeviceReading]:
        """
        生成一天的设备读数
        
        Args:
            date: 日期
            interval_minutes: 采样间隔（分钟）
        """
        readings = []
        current = datetime(date.year, date.month, date.day, 0, 0, 0)
        end = current + timedelta(days=1)
        
        while current < end:
            # 心率（每次都记录）
            readings.append(DeviceReading(
                user_id=self.user_id,
                device_type='smartwatch',
                metric_type='heart_rate',
                value=self.generate_heart_rate(current),
                unit='bpm',
                recorded_at=current
            ))
            
            # 血氧（每30分钟记录一次）
            if current.minute % 30 == 0:
                readings.append(DeviceReading(
                    user_id=self.user_id,
                    device_type='smartwatch',
                    metric_type='spo2',
                    value=self.generate_spo2(current),
                    unit='%',
                    recorded_at=current
                ))
            
            current += timedelta(minutes=interval_minutes)
        
        return readings
    
    def generate_daily_summary(self, date: datetime) -> DailyHealthSummary:
        """生成每日健康汇总"""
        date_str = date.strftime('%Y-%m-%d')
        
        # 获取当天的心率数据
        hr_readings = self.db.query(DeviceReading).filter(
            DeviceReading.user_id == self.user_id,
            DeviceReading.metric_type == 'heart_rate',
            DeviceReading.recorded_at >= date,
            DeviceReading.recorded_at < date + timedelta(days=1)
        ).all()
        
        hr_values = [r.value for r in hr_readings] if hr_readings else [70]
        
        # 获取血氧数据
        spo2_readings = self.db.query(DeviceReading).filter(
            DeviceReading.user_id == self.user_id,
            DeviceReading.metric_type == 'spo2',
            DeviceReading.recorded_at >= date,
            DeviceReading.recorded_at < date + timedelta(days=1)
        ).all()
        
        spo2_values = [r.value for r in spo2_readings] if spo2_readings else [97]
        
        # 生成步数和睡眠数据
        steps_data = self.generate_daily_steps(date)
        sleep_data = self.generate_sleep_data(date)
        bp_data = self.generate_blood_pressure(date.replace(hour=8))
        
        # 计算静息心率（取最低的10%的平均值）
        sorted_hr = sorted(hr_values)
        resting_count = max(1, len(sorted_hr) // 10)
        resting_hr = sum(sorted_hr[:resting_count]) / resting_count
        
        summary = DailyHealthSummary(
            user_id=self.user_id,
            date=date_str,
            
            # 心率
            avg_heart_rate=round(sum(hr_values) / len(hr_values), 1),
            min_heart_rate=min(hr_values),
            max_heart_rate=max(hr_values),
            resting_heart_rate=round(resting_hr, 1),
            
            # 活动
            total_steps=steps_data['total'],
            active_minutes=random.randint(30, 90),
            calories_burned=steps_data['calories'],
            distance=steps_data['distance'],
            
            # 睡眠
            sleep_start_time=sleep_data['sleep_start'],
            sleep_end_time=sleep_data['sleep_end'],
            sleep_duration=sleep_data['duration'],
            deep_sleep_duration=sleep_data['deep_sleep'],
            light_sleep_duration=sleep_data['light_sleep'],
            rem_duration=sleep_data['rem_sleep'],
            awake_count=sleep_data['awake_count'],
            sleep_quality_score=sleep_data['quality_score'],
            
            # 血氧
            avg_spo2=round(sum(spo2_values) / len(spo2_values), 1),
            min_spo2=min(spo2_values),
            
            # 血压
            morning_systolic=bp_data['systolic'],
            morning_diastolic=bp_data['diastolic']
        )
        
        return summary
    
    def generate_historical_data(self, days: int = 30):
        """
        生成历史数据
        
        Args:
            days: 生成多少天的数据
        """
        print(f"🔄 开始为用户 {self.user_id} 生成 {days} 天的模拟数据...")
        
        end_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = end_date - timedelta(days=days)
        
        current = start_date
        total_readings = 0
        
        while current < end_date:
            date_str = current.strftime('%Y-%m-%d')
            
            # 检查是否已有数据
            existing = self.db.query(DailyHealthSummary).filter(
                DailyHealthSummary.user_id == self.user_id,
                DailyHealthSummary.date == date_str
            ).first()
            
            if not existing:
                # 生成设备读数（每5分钟一条）
                readings = self.generate_day_readings(current, interval_minutes=5)
                self.db.bulk_save_objects(readings)
                total_readings += len(readings)
                
                # 生成每日汇总
                summary = self.generate_daily_summary(current)
                self.db.add(summary)
                
                if current.day == 1 or (end_date - current).days % 7 == 0:
                    print(f"  📅 {date_str} - 已生成 {len(readings)} 条读数")
            
            current += timedelta(days=1)
        
        self.db.commit()
        print(f"✅ 数据生成完成！共生成 {total_readings} 条设备读数")


def generate_sample_health_profile(user_id: int) -> UserHealthProfile:
    """生成示例健康档案"""
    db = SessionLocal()
    
    try:
        # 检查是否已存在
        existing = db.query(UserHealthProfile).filter(
            UserHealthProfile.user_id == user_id
        ).first()
        
        if existing:
            print(f"用户 {user_id} 已有健康档案")
            return existing
        
        # 获取用户信息
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            print(f"用户 {user_id} 不存在")
            return None
        
        # 根据性别生成合理数据
        is_male = user.gender == '男'
        age = user.age or 35
        
        # 身高体重
        if is_male:
            height = random.uniform(165, 185)
            weight = random.uniform(60, 90)
        else:
            height = random.uniform(155, 170)
            weight = random.uniform(45, 70)
        
        bmi = round(weight / ((height / 100) ** 2), 1)
        
        # 腰围
        if is_male:
            waist = random.uniform(75, 95)
        else:
            waist = random.uniform(65, 85)
        
        profile = UserHealthProfile(
            user_id=user_id,
            height=round(height, 1),
            weight=round(weight, 1),
            bmi=bmi,
            waist=round(waist, 1),
            
            # 血压（正常偏高）
            systolic_bp=random.randint(110, 135),
            diastolic_bp=random.randint(70, 88),
            on_bp_medication=random.random() < 0.1,
            
            # 血液指标
            total_cholesterol=random.uniform(150, 220),
            hdl_cholesterol=random.uniform(40, 70),
            ldl_cholesterol=random.uniform(80, 150),
            triglycerides=random.uniform(80, 180),
            fasting_glucose=random.uniform(4.5, 6.5),
            hba1c=random.uniform(4.5, 6.2),
            
            # 生活习惯
            is_smoker=random.random() < 0.2,
            smoking_years=random.randint(0, 20) if random.random() < 0.2 else 0,
            alcohol_frequency=random.choice(['never', 'occasional', 'regular']),
            exercise_frequency=random.choice(['never', '1-2/week', '3-4/week', 'daily']),
            exercise_minutes_per_week=random.randint(0, 300),
            
            # 病史
            has_diabetes=random.random() < 0.05,
            has_hypertension=random.random() < 0.15,
            has_heart_disease=random.random() < 0.03,
            family_diabetes=random.random() < 0.2,
            family_heart_disease=random.random() < 0.15,
            family_hypertension=random.random() < 0.25,
            
            # 饮食
            daily_fruit_vegetable=random.random() > 0.3,
            high_salt_diet=random.random() < 0.3
        )
        
        db.add(profile)
        db.commit()
        db.refresh(profile)
        
        print(f"✅ 已为用户 {user_id} 创建健康档案")
        return profile
        
    finally:
        db.close()


def seed_device_data(user_id: int = 1, days: int = 30):
    """种子数据入口函数"""
    # 生成健康档案
    generate_sample_health_profile(user_id)
    
    # 生成设备数据
    simulator = DeviceSimulator(user_id)
    simulator.generate_historical_data(days)


if __name__ == '__main__':
    # 为用户1生成30天数据
    seed_device_data(user_id=1, days=30)
