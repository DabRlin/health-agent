"""
Agent 服务 - 基于 LLM Function Calling 的 ReAct 循环
支持流式输出
"""
import json
from datetime import datetime
from typing import Optional, List, Generator
from database import SessionLocal, User, Consultation, ConsultationMessage
from sqlalchemy import desc
from config import config
from utils.llm_client import get_llm_client
from services.agent_tools import TOOLS_SCHEMA, execute_tool


# ==================== System Prompt ====================

SYSTEM_PROMPT = """你是 HealthAI 智能健康助手，一个专业、温暖、负责任的 AI 健康顾问。

## 你的能力
你可以调用以下工具来获取用户的真实健康数据：
- **查询健康指标**：获取用户最新的心率、血压、血糖、BMI、睡眠等数据
- **分析健康趋势**：分析某项指标的历史变化趋势、异常检测和预测
- **运行风险评估**：使用 Framingham、FINDRISC 等医学模型评估心血管、糖尿病、代谢综合征风险
- **查看用户档案**：了解用户基本信息和健康评分
- **录入健康数据**：帮助用户记录新的健康指标

## 行为准则
1. **主动调用工具**：当用户询问健康数据、趋势或风险时，优先调用工具获取真实数据，而不是凭空回答
2. **数据驱动回答**：基于工具返回的真实数据给出分析和建议，不要编造数据
3. **专业但易懂**：用通俗易懂的语言解释医学概念，避免过度使用专业术语
4. **温暖关怀**：关注用户情绪，给予鼓励和支持
5. **录入确认**：在调用 add_health_metric 录入数据前，必须先向用户确认数值是否正确
6. **边界意识**：明确告知用户 AI 建议不能替代专业医疗诊断，严重症状应及时就医

## 免责声明
本系统提供的健康分析和建议仅供参考，不构成医疗诊断。如有健康问题，请及时前往正规医疗机构就诊。"""


# ==================== Agent Service ====================

class AgentService:
    """Agent 服务类 - ReAct 循环实现"""

    MAX_TOOL_ROUNDS = 5  # 最大工具调用轮次，防止死循环

    @classmethod
    def start_consultation(cls, user_id: Optional[int] = None):
        """开始问诊会话"""
        db = SessionLocal()
        try:
            user = cls._get_user(db, user_id)
            if not user:
                session_id = cls._generate_session_id()
                return session_id, [cls._welcome_message()]

            session_id = cls._generate_session_id()
            consultation = Consultation(
                user_id=user.id,
                session_id=session_id,
                status="进行中"
            )
            db.add(consultation)
            db.flush()

            welcome_content = cls._get_welcome_content(user.name)
            welcome_msg = ConsultationMessage(
                consultation_id=consultation.id,
                role="assistant",
                content=welcome_content
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
    def send_message_stream(
        cls, session_id: str, user_message: str, user_id: Optional[int] = None
    ) -> Generator[str, None, None]:
        """
        流式发送消息，执行 Agent ReAct 循环

        Yields:
            JSON 字符串，type 为：
            - user_message: 用户消息确认
            - tool_call: 工具调用通知（可选，用于前端展示思考过程）
            - chunk: AI 回复文本片段
            - done: 完成信号
            - error: 错误信息
        """
        db = SessionLocal()
        try:
            consultation = db.query(Consultation).filter(
                Consultation.session_id == session_id
            ).first()

            if not consultation:
                yield json.dumps({"type": "error", "content": "会话不存在"})
                return

            # 保存用户消息
            user_msg = ConsultationMessage(
                consultation_id=consultation.id,
                role="user",
                content=user_message
            )
            db.add(user_msg)
            db.commit()

            yield json.dumps({
                "type": "user_message",
                "content": {
                    "id": user_msg.id,
                    "role": "user",
                    "content": user_msg.content,
                    "time": user_msg.created_at.strftime("%H:%M")
                }
            })

            # 构建历史消息（滑动窗口）
            messages = cls._build_messages(db, consultation.id, user_message)

            # ReAct 循环
            full_response = ""
            effective_user_id = user_id or consultation.user_id

            for chunk in cls._agent_loop(messages, effective_user_id):
                full_response += chunk
                yield json.dumps({"type": "chunk", "content": chunk})

            yield json.dumps({"type": "done", "content": ""})

            # 保存 AI 回复
            ai_msg = ConsultationMessage(
                consultation_id=consultation.id,
                role="assistant",
                content=full_response
            )
            db.add(ai_msg)
            db.commit()

        except Exception as e:
            print(f"AgentService error: {e}")
            yield json.dumps({"type": "error", "content": "服务暂时不可用，请稍后重试"})
        finally:
            db.close()

    @classmethod
    def _agent_loop(cls, messages: list, user_id: int) -> Generator[str, None, None]:
        """
        ReAct 循环核心：LLM 推理 → 工具调用 → 观察 → 继续推理
        最终流式 yield 文本片段
        """
        client = get_llm_client()
        loop_messages = list(messages)

        for round_num in range(cls.MAX_TOOL_ROUNDS):
            response = client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=loop_messages,
                tools=TOOLS_SCHEMA,
                tool_choice="auto",
                stream=False,  # 工具调用阶段不流式，最终回复再流式
                temperature=0.7,
                max_tokens=2048,
            )

            message = response.choices[0].message
            tool_calls = message.tool_calls

            # 没有工具调用 → 真正的流式输出最终回复
            if not tool_calls:
                yield from cls._stream_final_response(client, loop_messages)
                return

            # 有工具调用 → 执行工具，将结果追加到 messages
            loop_messages.append({
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in tool_calls
                ]
            })

            for tc in tool_calls:
                tool_name = tc.function.name
                try:
                    tool_args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    tool_args = {}

                print(f"🔧 Agent 调用工具: {tool_name}({tool_args})")
                tool_result = execute_tool(tool_name, tool_args, user_id)
                print(f"   工具结果: {tool_result[:100]}...")

                loop_messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": tool_result
                })

        # 超过最大轮次，强制流式生成回复
        yield from cls._stream_final_response(client, loop_messages)

    @classmethod
    def _stream_final_response(cls, client, messages: list) -> Generator[str, None, None]:
        """使用 stream=True 真正流式输出最终回复"""
        stream = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=messages,
            stream=True,
            temperature=0.7,
            max_tokens=2048,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content

    @classmethod
    def _build_messages(cls, db, consultation_id: int, current_user_message: str) -> list:
        """
        构建发送给 LLM 的消息列表（滑动窗口）
        包含 system prompt + 最近 N 条历史 + 当前用户消息
        """
        # 获取历史消息（不含当前刚保存的用户消息，按时间倒序取 N 条再反转）
        window = config.LLM_MAX_HISTORY
        history = db.query(ConsultationMessage).filter(
            ConsultationMessage.consultation_id == consultation_id,
            ConsultationMessage.role.in_(["user", "assistant"])
        ).order_by(desc(ConsultationMessage.created_at)).limit(window).all()

        history = list(reversed(history))

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        for msg in history:
            # 跳过当前刚录入的用户消息（避免重复）
            if msg.role == "user" and msg.content == current_user_message:
                continue
            messages.append({"role": msg.role, "content": msg.content})

        # 追加当前用户消息
        messages.append({"role": "user", "content": current_user_message})

        return messages

    @classmethod
    def get_history(cls, user_id: Optional[int] = None, limit: int = 10) -> list:
        """获取问诊历史列表"""
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
    def _get_user(cls, db, user_id: Optional[int] = None):
        if user_id:
            return db.query(User).filter(User.id == user_id).first()
        return db.query(User).first()

    @staticmethod
    def _generate_session_id() -> str:
        import random
        return f"conv_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"

    @staticmethod
    def _get_welcome_content(name: str = "") -> str:
        greeting = f"您好，{name}！" if name else "您好！"
        return f"""{greeting}我是 HealthAI 智能健康助手。

我可以帮您：
• 查看和分析您的健康指标（血压、血糖、心率等）
• 分析健康数据的变化趋势和异常情况
• 运行心血管、糖尿病等健康风险评估
• 解答健康相关问题，提供个性化建议

请问有什么可以帮您的？"""

    @staticmethod
    def _welcome_message() -> dict:
        return {
            "id": 1,
            "role": "assistant",
            "content": AgentService._get_welcome_content.__func__(AgentService),
            "time": datetime.now().strftime("%H:%M")
        }
