"""
Agent 服务 - 基于 LLM Function Calling 的 ReAct 循环
支持流式输出
"""
import json
import logging
from datetime import datetime
from typing import Optional, List, Generator
from database import SessionLocal, User, Consultation, ConsultationMessage
from sqlalchemy import desc, func
from config import config
from utils.llm_client import get_llm_client
from services.agent_tools import TOOLS_SCHEMA, execute_tool, TOOLS_BY_DEPARTMENT

logger = logging.getLogger(__name__)


# ==================== 科室定义 ====================

DEPARTMENTS = {
    "general": {
        "name": "全科门诊",
        "icon": "🏥",
        "desc": "通用健康咨询、慢病管理、健康档案分析",
    },
    "cardiology": {
        "name": "心血管科",
        "icon": "❤️",
        "desc": "血压、心率、血脂、心血管风险评估",
    },
    "endocrinology": {
        "name": "内分泌科",
        "icon": "🩸",
        "desc": "血糖、糖尿病、甲状腺、代谢综合征",
    },
    "dermatology": {
        "name": "皮肤科",
        "icon": "🔬",
        "desc": "皮肤症状咨询，支持图片上传分析",
    },
}

# ==================== System Prompts ====================

_BASE_RULES = """## 行为准则
1. **优先调用工具**：当用户询问个人数据、趋势、风险时，必须先调用工具获取真实数据再作答
2. **知识性问题查库**：当用户询问疾病知识、指标正常范围、饮食/运动建议、药物副作用、症状原因等，优先调用 get_health_knowledge 检索知识库
3. **体检报告解读**：当用户询问体检结果时，调用 analyze_exam_report 获取解析数据，结合知识库给出专业解读
4. **数据驱动**：基于工具返回的真实数据和知识库内容给出分析，不要凭空编造数据
5. **专业但易懂**：用通俗语言解释医学概念，必要时结合用户实际数据举例
6. **温暖关怀**：关注用户情绪，给予鼓励和支持，对异常指标不过度渲染恐慌
7. **录入确认**：调用 add_health_metric 录入数据前，必须先向用户确认数值
8. **边界意识**：明确告知 AI 建议不能替代专业医疗诊断，严重症状应及时就医

## 免责声明
本系统提供的健康分析和建议仅供参考，不构成医疗诊断。如有健康问题，请及时前往正规医疗机构就诊。"""

SYSTEM_PROMPTS = {
    "general": """你是 HealthAI 全科智能助手，一个专业、温暖、负责任的 AI 健康顾问。

## 擅长领域
全科健康咨询、慢性病管理、健康档案解读、综合健康建议。

## 可用工具
- 查询/录入健康指标（心率、血压、血糖、BMI、睡眠等）
- 分析健康趋势与异常检测
- 运行心血管、糖尿病、代谢综合征、骨质疏松风险评估
- 查看用户健康档案
- 检索综合健康知识库
- 解读体检报告

""" + _BASE_RULES,

    "cardiology": """你是 HealthAI 心血管科智能助手，专注于心血管健康领域的专业 AI 顾问。

## 擅长领域
高血压管理、心率异常、血脂异常、心血管风险评估、冠心病预防、动脉粥样硬化。

## 可用工具
- 查询血压、心率、血脂等心血管相关指标
- 分析血压/心率变化趋势
- 运行 Framingham 心血管风险评估
- 检索心血管专项知识库
- 解读涉及心血管的体检报告

## 专科说明
本门诊专注心血管相关问题。其他科室问题（如皮肤、内分泌）建议前往对应门诊咨询。

""" + _BASE_RULES,

    "endocrinology": """你是 HealthAI 内分泌科智能助手，专注于代谢与内分泌健康领域的专业 AI 顾问。

## 擅长领域
糖尿病管理与预防、血糖监测、胰岛素抵抗、甲状腺疾病、血脂代谢、代谢综合征、肥胖管理。

## 可用工具
- 查询血糖、HbA1c、BMI、血脂等内分泌相关指标
- 分析血糖趋势与波动规律
- 运行 FINDRISC 糖尿病风险评估、代谢综合征评估
- 检索内分泌专项知识库
- 解读涉及血糖/甲状腺的体检报告

## 专科说明
本门诊专注内分泌与代谢相关问题。其他科室问题建议前往对应门诊咨询。

""" + _BASE_RULES,

    "dermatology": """你是 HealthAI 皮肤科智能助手，专注于皮肤健康领域的专业 AI 顾问。

## 擅长领域
常见皮疹、痤疮、湿疹、荨麻疹、皮肤感染、皮肤肿物初步判断、皮肤护理建议。

## 可用工具
- 检索皮肤科专项知识库（皮肤病症状、治疗、护理）
- 图像分析（用户上传皮肤图片后，结合视觉模型辅助描述）

## 图像分析说明
用户可上传皮肤图片，我将结合图像内容与知识库提供参考意见。
**AI 图像分析仅供参考，不能替代皮肤科医生的专业诊断，建议线下就诊确认。**

## 专科说明
本门诊专注皮肤相关问题。其他科室问题建议前往对应门诊咨询。

""" + _BASE_RULES,
}


# ==================== Agent Service ====================

class AgentService:
    """Agent 服务类 - ReAct 循环实现"""

    MAX_TOOL_ROUNDS = 5  # 最大工具调用轮次，防止死循环

    @classmethod
    def start_consultation(cls, user_id: Optional[int] = None, department: str = "general"):
        """开始问诊会话"""
        department = department if department in DEPARTMENTS else "general"
        db = SessionLocal()
        try:
            user = cls._get_user(db, user_id)
            if not user:
                session_id = cls._generate_session_id()
                return session_id, [cls._welcome_message(department=department)]

            session_id = cls._generate_session_id()
            consultation = Consultation(
                user_id=user.id,
                session_id=session_id,
                department=department,
                status="进行中"
            )
            db.add(consultation)
            db.flush()

            welcome_content = cls._get_welcome_content(user.name, department)
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
        cls, session_id: str, user_message: str, user_id: Optional[int] = None,
        image_base64: Optional[str] = None, image_mime: Optional[str] = None
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

            # 首条用户消息自动命名会话
            if not consultation.summary:
                consultation.summary = user_message[:20] + ('…' if len(user_message) > 20 else '')
                db.commit()

            # 皮肤科 + 有图片：先调 VL 分析，结果注入对话
            department = consultation.department or "general"
            vl_analysis = None
            if department == "dermatology" and image_base64 and image_mime:
                yield json.dumps({"type": "thinking", "content": "正在分析皮肤图片..."})
                try:
                    from services.vl_service import VLService
                    # 保存图片到服务器
                    effective_user_id = user_id or consultation.user_id
                    VLService.save_image(image_base64, image_mime, effective_user_id)
                    # 调用 VL 模型分析
                    vl_analysis = VLService.analyze_skin_image(
                        image_base64, image_mime, user_message
                    )
                    if vl_analysis:
                        logger.info("VL 分析完成，注入对话上下文")
                except Exception:
                    logger.exception("VL 分析失败，跳过继续")

            # 构建历史消息（滑动窗口）
            messages = cls._build_messages(
                db, consultation.id, user_message,
                department=department,
                vl_analysis=vl_analysis,
            )

            # ReAct 循环
            full_response = ""
            effective_user_id = user_id or consultation.user_id

            for item in cls._agent_loop(messages, effective_user_id, department=department):
                if isinstance(item, dict):
                    # thinking 事件，直接透传
                    yield json.dumps(item)
                else:
                    # 文本 chunk
                    full_response += item
                    yield json.dumps({"type": "chunk", "content": item})

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
            logger.exception("AgentService 流式处理失败")
            yield json.dumps({"type": "error", "content": "服务暂时不可用，请稍后重试"})
        finally:
            db.close()

    @classmethod
    def _agent_loop(cls, messages: list, user_id: int, department: str = "general") -> Generator[str, None, None]:
        """
        ReAct 循环核心：LLM 推理 → 工具调用 → 观察 → 继续推理
        最终流式 yield 文本片段

        优化策略：
        - 第一轮：stream=True + tools，直接流式输出；若检测到 tool_calls 则收集完整响应再执行工具
        - 工具调用后续轮：stream=False 判断是否还需工具，最终再 stream=True 输出
        """
        client = get_llm_client()
        loop_messages = list(messages)
        tools_schema = TOOLS_BY_DEPARTMENT.get(department, TOOLS_SCHEMA)

        for round_num in range(cls.MAX_TOOL_ROUNDS):
            is_first_round = (round_num == 0)

            if is_first_round:
                # 第一轮：流式 + tools
                # 工具调用和文本输出互斥：有 tool_calls 时 content 为空，因此可以安全地实时 yield
                stream = client.chat.completions.create(
                    model=config.LLM_MODEL,
                    messages=loop_messages,
                    tools=tools_schema,
                    tool_choice="auto",
                    stream=True,
                    temperature=0.7,
                    max_tokens=2048,
                )

                collected_content = ""
                collected_tool_calls = {}  # index -> {id, name, arguments}

                for chunk in stream:
                    delta = chunk.choices[0].delta if chunk.choices else None
                    if not delta:
                        continue

                    # 文本：立即 yield（真正流式）
                    if delta.content:
                        collected_content += delta.content
                        yield delta.content

                    # 收集 tool_calls（流式下按 index 分块拼接）
                    if delta.tool_calls:
                        for tc_delta in delta.tool_calls:
                            idx = tc_delta.index
                            if idx not in collected_tool_calls:
                                collected_tool_calls[idx] = {
                                    "id": tc_delta.id or "",
                                    "name": "",
                                    "arguments": ""
                                }
                            if tc_delta.id:
                                collected_tool_calls[idx]["id"] = tc_delta.id
                            if tc_delta.function:
                                if tc_delta.function.name:
                                    collected_tool_calls[idx]["name"] += tc_delta.function.name
                                if tc_delta.function.arguments:
                                    collected_tool_calls[idx]["arguments"] += tc_delta.function.arguments

                # 没有工具调用 → 文本已实时流出，直接返回
                if not collected_tool_calls:
                    return

                # 有工具调用（此时 collected_content 应为空）→ 转入工具执行阶段
                # 按 index 排序，保证多工具并发时顺序正确
                tool_calls_list = [
                    {
                        "id": v["id"],
                        "type": "function",
                        "function": {"name": v["name"], "arguments": v["arguments"]}
                    }
                    for _, v in sorted(collected_tool_calls.items())
                ]
                loop_messages.append({
                    "role": "assistant",
                    "content": collected_content or None,
                    "tool_calls": tool_calls_list
                })

                for tc in tool_calls_list:
                    tool_name = tc["function"]["name"]
                    try:
                        tool_args = json.loads(tc["function"]["arguments"])
                    except (json.JSONDecodeError, TypeError):
                        tool_args = {}

                    yield {"type": "thinking", "content": cls._tool_thinking_text(tool_name)}
                    logger.info("🔧 Agent 调用工具: %s(%s)", tool_name, tool_args)
                    tool_result = execute_tool(tool_name, tool_args, user_id, department=department)
                    logger.debug("   工具结果: %s", tool_result[:200])

                    loop_messages.append({
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": tool_result
                    })

            else:
                # 后续轮：stream=False 判断是否还需工具
                response = client.chat.completions.create(
                    model=config.LLM_MODEL,
                    messages=loop_messages,
                    tools=tools_schema,
                    tool_choice="auto",
                    stream=False,
                    temperature=0.7,
                    max_tokens=2048,
                )

                message = response.choices[0].message
                tool_calls = message.tool_calls

                if not tool_calls:
                    yield from cls._stream_final_response(client, loop_messages)
                    return

                loop_messages.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": tc.function.name, "arguments": tc.function.arguments}
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

                    yield {"type": "thinking", "content": cls._tool_thinking_text(tool_name)}
                    logger.info("🔧 Agent 调用工具: %s(%s)", tool_name, tool_args)
                    tool_result = execute_tool(tool_name, tool_args, user_id, department=department)
                    logger.debug("   工具结果: %s", tool_result[:200])

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
                yield delta.content  # 只 yield 原始文本，由 send_message_stream 包装

    @classmethod
    def _build_messages(
        cls, db, consultation_id: int, current_user_message: str,
        department: str = "general",
        vl_analysis: Optional[str] = None,
    ) -> list:
        """
        构建发送给 LLM 的消息列表（滑动窗口）
        包含 system prompt + 最近 N 条历史 + [VL分析结果] + 当前用户消息
        """
        window = config.LLM_MAX_HISTORY
        history = db.query(ConsultationMessage).filter(
            ConsultationMessage.consultation_id == consultation_id,
            ConsultationMessage.role.in_(["user", "assistant"])
        ).order_by(desc(ConsultationMessage.created_at)).limit(window).all()

        history = list(reversed(history))

        system_prompt = SYSTEM_PROMPTS.get(department, SYSTEM_PROMPTS["general"])
        messages = [{"role": "system", "content": system_prompt}]

        for msg in history:
            if msg.role == "user" and msg.content == current_user_message:
                continue
            messages.append({"role": msg.role, "content": msg.content})

        # 皮肤科有 VL 分析结果时，先注入为 assistant 消息，再附用户问题
        if vl_analysis:
            messages.append({
                "role": "assistant",
                "content": f"【图像分析结果】\n{vl_analysis}"
            })

        messages.append({"role": "user", "content": current_user_message})

        return messages

    @classmethod
    def get_history(cls, user_id: Optional[int] = None, limit: int = 20) -> list:
        """获取问诊历史列表（按最新消息时间倒序）"""
        db = SessionLocal()
        try:
            user = cls._get_user(db, user_id)
            if not user:
                return []

            # 子查询：每个会话的最新消息时间
            last_msg_time = (
                db.query(func.max(ConsultationMessage.created_at))
                .filter(ConsultationMessage.consultation_id == Consultation.id)
                .correlate(Consultation)
                .scalar_subquery()
            )

            consultations = db.query(Consultation).filter(
                Consultation.user_id == user.id
            ).order_by(desc(func.coalesce(last_msg_time, Consultation.started_at))).limit(limit).all()

            results = []
            for c in consultations:
                last_time = db.query(func.max(ConsultationMessage.created_at)).filter(
                    ConsultationMessage.consultation_id == c.id
                ).scalar()
                display_date = (last_time or c.started_at).strftime("%Y-%m-%d")
                results.append({
                    "id": c.id,
                    "session_id": c.session_id,
                    "date": display_date,
                    "summary": c.summary or "健康咨询",
                    "status": c.status,
                    "department": c.department or "general",
                    "department_name": DEPARTMENTS.get(c.department or "general", DEPARTMENTS["general"])["name"],
                })
            return results
        finally:
            db.close()

    @classmethod
    def get_detail(cls, session_id: str, user_id: Optional[int] = None) -> Optional[dict]:
        """获取问诊详情"""
        db = SessionLocal()
        try:
            q = db.query(Consultation).filter(
                Consultation.session_id == session_id
            )
            if user_id:
                q = q.filter(Consultation.user_id == user_id)
            consultation = q.first()

            if not consultation:
                return None

            messages = db.query(ConsultationMessage).filter(
                ConsultationMessage.consultation_id == consultation.id
            ).order_by(ConsultationMessage.created_at).all()

            return {
                "id": consultation.id,
                "session_id": consultation.session_id,
                "status": consultation.status,
                "department": consultation.department or "general",
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
    def rename_consultation(cls, session_id: str, summary: str, user_id: Optional[int] = None) -> bool:
        """重命名会话"""
        db = SessionLocal()
        try:
            user = cls._get_user(db, user_id)
            q = db.query(Consultation).filter(Consultation.session_id == session_id)
            if user:
                q = q.filter(Consultation.user_id == user.id)
            consultation = q.first()
            if not consultation:
                return False
            consultation.summary = summary.strip()[:30]
            db.commit()
            return True
        finally:
            db.close()

    @classmethod
    def delete_consultation(cls, session_id: str, user_id: Optional[int] = None) -> bool:
        """删除会话及其所有消息"""
        db = SessionLocal()
        try:
            user = cls._get_user(db, user_id)
            q = db.query(Consultation).filter(Consultation.session_id == session_id)
            if user:
                q = q.filter(Consultation.user_id == user.id)
            consultation = q.first()
            if not consultation:
                return False
            db.query(ConsultationMessage).filter(
                ConsultationMessage.consultation_id == consultation.id
            ).delete()
            db.delete(consultation)
            db.commit()
            return True
        finally:
            db.close()

    @classmethod
    def _get_user(cls, db, user_id: Optional[int] = None):
        if user_id:
            return db.query(User).filter(User.id == user_id).first()
        return db.query(User).first()

    @staticmethod
    def _tool_thinking_text(tool_name: str) -> str:
        """工具名 → 前端显示的思考中提示文字"""
        mapping = {
            "get_health_metrics": "正在查询您的健康指标...",
            "get_health_trend": "正在分析健康趋势数据...",
            "run_risk_assessment": "正在运行风险评估模型...",
            "get_user_profile": "正在获取您的健康档案...",
            "add_health_metric": "正在录入健康数据...",
            "get_health_knowledge": "正在检索健康知识库...",
            "analyze_exam_report": "正在读取并解析体检报告...",
        }
        return mapping.get(tool_name, "正在处理中...")

    @staticmethod
    def _generate_session_id() -> str:
        import random
        return f"conv_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"

    @staticmethod
    def _get_welcome_content(name: str = "", department: str = "general") -> str:
        greeting = f"您好，{name}！" if name else "您好！"
        dept = DEPARTMENTS.get(department, DEPARTMENTS["general"])
        dept_name = dept["name"]
        dept_desc = dept["desc"]

        specific_tips = {
            "general": "• 查看和分析您的健康指标（血压、血糖、心率等）\n• 分析健康数据的变化趋势和异常情况\n• 运行心血管、糖尿病等健康风险评估\n• 解答健康相关问题，提供个性化建议",
            "cardiology": "• 查询和分析您的血压、心率、血脂数据\n• 评估心血管疾病风险（Framingham 模型）\n• 解答高血压、心脏病预防等相关问题\n• 解读涉及心血管的体检指标",
            "endocrinology": "• 查询和分析您的血糖、BMI、血脂数据\n• 评估糖尿病风险（FINDRISC 模型）\n• 解答糖尿病、甲状腺、代谢综合征等问题\n• 提供血糖管理和饮食控制建议",
            "dermatology": "• 解答常见皮肤问题（皮疹、痤疮、湿疹等）\n• 支持上传皮肤图片进行 AI 辅助分析\n• 提供皮肤护理和用药参考建议\n• 检索皮肤科专业知识库",
        }

        tips = specific_tips.get(department, specific_tips["general"])
        return f"""{greeting}我是 HealthAI **{dept_name}**智能助手。

我可以帮您：
{tips}

请问有什么可以帮您的？"""

    @staticmethod
    def _welcome_message(department: str = "general") -> dict:
        return {
            "id": 1,
            "role": "assistant",
            "content": AgentService._get_welcome_content(department=department),
            "time": datetime.now().strftime("%H:%M")
        }

    @staticmethod
    def get_departments() -> list:
        """获取所有科室信息列表"""
        return [
            {"id": k, **v}
            for k, v in DEPARTMENTS.items()
        ]
