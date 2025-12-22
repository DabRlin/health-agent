"""
智能问诊服务
"""
from datetime import datetime
from typing import Optional, List, Tuple, Generator
import random
import json
from database import SessionLocal, User, Consultation, ConsultationMessage
from sqlalchemy import desc
from config import config
from utils import get_dify_client


class ConsultationService:
    """智能问诊服务类"""
    
    # 本地回复模板（降级方案）
    LOCAL_RESPONSES = {
        "头痛": """根据您描述的头痛症状，我来为您分析一下：

**可能的原因：**
1. **紧张性头痛** - 最常见，通常与压力、疲劳有关
2. **偏头痛** - 如伴有恶心、畏光等症状
3. **颈椎问题** - 长期伏案工作可能导致
4. **睡眠不足** - 睡眠质量差也会引起头痛

**建议措施：**
• 保证充足睡眠（7-8小时）
• 适当休息，避免长时间用眼
• 保持正确坐姿，定时活动颈部
• 可尝试热敷或按摩太阳穴

**就医建议：**
如果头痛持续超过3天、频繁发作或伴有视力模糊、呕吐等症状，建议前往神经内科就诊。""",

        "血压": """关于血压偏高的问题，我来为您详细解答：

**血压分级标准：**
• 正常：收缩压 < 120 且 舒张压 < 80 mmHg
• 正常高值：120-139 / 80-89 mmHg
• 高血压：≥ 140 / 90 mmHg

**日常管理建议：**
1. **饮食调整** - 减少盐摄入（每日 < 6g），多吃蔬果
2. **生活方式** - 规律运动（每周150分钟），控制体重
3. **监测建议** - 每天固定时间测量，记录变化趋势

**就医建议：**
如血压持续 ≥ 140/90 mmHg，建议前往心内科就诊。""",

        "睡眠": """关于改善睡眠质量，我有以下建议：

**改善睡眠的方法：**
1. **建立规律作息** - 固定时间入睡和起床
2. **优化睡眠环境** - 保持卧室安静、黑暗、凉爽
3. **睡前习惯** - 睡前1小时避免使用手机
4. **日间习惯** - 白天适当运动，午睡不超过30分钟

**就医建议：**
如长期失眠（超过1个月），建议前往睡眠医学科就诊。""",

        "血糖": """关于血糖偏高的问题，我来为您解答：

**血糖参考标准：**
• 空腹血糖：3.9-6.1 mmol/L（正常）
• 餐后2小时：< 7.8 mmol/L（正常）

**血糖管理建议：**
1. **饮食控制** - 减少精制碳水，增加膳食纤维
2. **运动建议** - 每天30分钟有氧运动
3. **监测建议** - 定期监测空腹和餐后血糖

**就医建议：**
如空腹血糖持续 > 6.1 mmol/L，建议前往内分泌科就诊。""",

        "default": """感谢您的咨询。根据您描述的情况，我来为您分析：

**初步分析：**
您提到的症状可能与多种因素有关，建议从以下几个方面关注：
1. 保持规律作息和均衡饮食
2. 适量运动
3. 关注相关健康指标变化

**就医建议：**
如症状持续或加重，建议及时前往医院相关科室就诊。

⚠️ 以上建议仅供参考，不能替代专业医疗诊断。"""
    }
    
    @classmethod
    def start_consultation(cls, user_id: Optional[int] = None) -> Tuple[str, List[dict]]:
        """开始问诊会话"""
        db = SessionLocal()
        try:
            user = cls._get_user(db, user_id)
            if not user:
                # 返回默认会话
                session_id = cls._generate_session_id()
                return session_id, [cls._create_welcome_message()]
            
            session_id = cls._generate_session_id()
            
            consultation = Consultation(
                user_id=user.id,
                session_id=session_id,
                status="进行中"
            )
            db.add(consultation)
            db.flush()
            
            # 添加欢迎消息
            welcome_msg = ConsultationMessage(
                consultation_id=consultation.id,
                role="assistant",
                content=cls._get_welcome_content()
            )
            db.add(welcome_msg)
            db.commit()
            
            return session_id, [{
                "id": welcome_msg.id,
                "role": "assistant",
                "content": welcome_msg.content,
                "time": welcome_msg.created_at.strftime("%H:%M")
            }]
        finally:
            db.close()
    
    @classmethod
    def send_message(cls, session_id: str, user_message: str) -> Tuple[Optional[dict], Optional[dict], Optional[str]]:
        """
        发送问诊消息
        
        Returns:
            (user_msg, ai_msg, error)
        """
        db = SessionLocal()
        try:
            consultation = db.query(Consultation).filter(
                Consultation.session_id == session_id
            ).first()
            
            if not consultation:
                return None, None, "会话不存在"
            
            # 添加用户消息
            user_msg = ConsultationMessage(
                consultation_id=consultation.id,
                role="user",
                content=user_message
            )
            db.add(user_msg)
            
            # 生成 AI 回复
            ai_response = cls._get_ai_response(user_message, session_id)
            
            ai_msg = ConsultationMessage(
                consultation_id=consultation.id,
                role="assistant",
                content=ai_response
            )
            db.add(ai_msg)
            db.commit()
            
            return {
                "id": user_msg.id,
                "role": "user",
                "content": user_msg.content,
                "time": user_msg.created_at.strftime("%H:%M")
            }, {
                "id": ai_msg.id,
                "role": "assistant",
                "content": ai_msg.content,
                "time": ai_msg.created_at.strftime("%H:%M")
            }, None
        finally:
            db.close()
    
    @classmethod
    def get_history(cls, limit: int = 10, user_id: Optional[int] = None) -> List[dict]:
        """获取问诊历史"""
        db = SessionLocal()
        try:
            user = cls._get_user(db, user_id)
            if not user:
                return []
            
            consultations = db.query(Consultation).filter(
                Consultation.user_id == user.id
            ).order_by(desc(Consultation.started_at)).limit(limit).all()
            
            return [{
                "id": c.id,
                "session_id": c.session_id,
                "date": c.started_at.strftime("%Y-%m-%d"),
                "summary": c.summary or "健康咨询",
                "status": c.status
            } for c in consultations]
        finally:
            db.close()
    
    @classmethod
    def get_detail(cls, session_id: str) -> Optional[dict]:
        """获取问诊详情"""
        db = SessionLocal()
        try:
            consultation = db.query(Consultation).filter(
                Consultation.session_id == session_id
            ).first()
            
            if not consultation:
                return None
            
            messages = db.query(ConsultationMessage).filter(
                ConsultationMessage.consultation_id == consultation.id
            ).order_by(ConsultationMessage.created_at).all()
            
            return {
                "id": consultation.id,
                "session_id": consultation.session_id,
                "status": consultation.status,
                "messages": [{
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "time": m.created_at.strftime("%H:%M")
                } for m in messages]
            }
        finally:
            db.close()
    
    @classmethod
    def send_message_stream(cls, session_id: str, user_message: str) -> Generator[str, None, None]:
        """
        流式发送问诊消息
        
        Yields:
            JSON 字符串，包含 type 和 content
        """
        db = SessionLocal()
        try:
            consultation = db.query(Consultation).filter(
                Consultation.session_id == session_id
            ).first()
            
            if not consultation:
                yield json.dumps({"type": "error", "content": "会话不存在"})
                return
            
            # 添加用户消息
            user_msg = ConsultationMessage(
                consultation_id=consultation.id,
                role="user",
                content=user_message
            )
            db.add(user_msg)
            db.commit()
            
            # 发送用户消息确认
            yield json.dumps({
                "type": "user_message",
                "content": {
                    "id": user_msg.id,
                    "role": "user",
                    "content": user_msg.content,
                    "time": user_msg.created_at.strftime("%H:%M")
                }
            })
            
            # 流式获取 AI 回复
            full_response = ""
            
            if config.DIFY_ENABLED and config.DIFY_API_KEY:
                try:
                    client = get_dify_client()
                    
                    for chunk in client.chat_stream(
                        query=user_message,
                        user=f"user_{session_id}",
                        inputs={}
                    ):
                        if chunk.get("error"):
                            print(f"⚠️ Dify 流式错误: {chunk.get('message')}")
                            break
                        
                        text = chunk.get("text", "")
                        if text:
                            full_response += text
                            yield json.dumps({"type": "chunk", "content": text})
                    
                    if full_response:
                        yield json.dumps({"type": "done", "content": ""})
                except Exception as e:
                    print(f"⚠️ Dify 流式调用异常: {str(e)}")
            
            # 如果没有获取到流式回复，使用本地回复
            if not full_response:
                full_response = cls._get_local_response(user_message)
                # 模拟流式输出
                for char in full_response:
                    yield json.dumps({"type": "chunk", "content": char})
                yield json.dumps({"type": "done", "content": ""})
            
            # 保存 AI 回复到数据库
            ai_msg = ConsultationMessage(
                consultation_id=consultation.id,
                role="assistant",
                content=full_response
            )
            db.add(ai_msg)
            db.commit()
            
        finally:
            db.close()
    
    @classmethod
    def _get_ai_response(cls, user_message: str, session_id: str = None) -> str:
        """获取 AI 回复（阻塞模式）"""
        # 如果 Dify 已启用，尝试调用 Dify API
        if config.DIFY_ENABLED and config.DIFY_API_KEY:
            try:
                client = get_dify_client()
                
                response = client.chat(
                    query=user_message,
                    user=f"user_{session_id}" if session_id else "default_user",
                    conversation_id=None,
                    inputs={}
                )
                
                if response and not response.get("error"):
                    answer = response.get("answer", "")
                    if answer:
                        return answer
                
                print(f"⚠️ Dify API 返回错误: {response.get('message', 'Unknown error')}")
            except Exception as e:
                print(f"⚠️ Dify API 调用异常: {str(e)}")
        
        # 降级：使用本地关键字匹配
        return cls._get_local_response(user_message)
    
    @classmethod
    def _get_local_response(cls, user_message: str) -> str:
        """本地关键字匹配回复"""
        for keyword, response in cls.LOCAL_RESPONSES.items():
            if keyword != "default" and keyword in user_message:
                return response
        return cls.LOCAL_RESPONSES["default"]
    
    @classmethod
    def _get_user(cls, db, user_id: Optional[int] = None):
        """获取用户"""
        if user_id:
            return db.query(User).filter(User.id == user_id).first()
        return db.query(User).first()
    
    @staticmethod
    def _generate_session_id() -> str:
        """生成会话 ID"""
        return f"conv_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"
    
    @staticmethod
    def _get_welcome_content() -> str:
        """获取欢迎消息内容"""
        return """您好！我是 HealthAI 智能健康助手。请描述您的症状或健康问题，我会为您提供专业的健康建议。

您可以这样描述：
• 最近有什么不舒服的症状？
• 症状持续多长时间了？
• 有没有其他伴随症状？"""
    
    @classmethod
    def _create_welcome_message(cls) -> dict:
        """创建欢迎消息"""
        return {
            "id": 1,
            "role": "assistant",
            "content": cls._get_welcome_content(),
            "time": datetime.now().strftime("%H:%M")
        }
