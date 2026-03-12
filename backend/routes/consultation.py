"""
智能问诊路由
"""
import logging
from flask import Blueprint, jsonify, request, Response
from services.agent_service import AgentService
from utils import login_required, get_current_user_id

logger = logging.getLogger(__name__)

consultation_bp = Blueprint('consultation', __name__, url_prefix='/api/consultation')


@consultation_bp.route('/departments', methods=['GET'])
def get_departments():
    """获取科室列表（无需登录）"""
    return jsonify({"success": True, "data": AgentService.get_departments()})


@consultation_bp.route('/start', methods=['POST'])
@login_required
def start_consultation():
    """开始问诊会话"""
    user_id = get_current_user_id()
    department = (request.json or {}).get('department', 'general')
    session_id, messages = AgentService.start_consultation(user_id, department=department)
    return jsonify({
        "success": True,
        "data": {
            "conversation_id": session_id,
            "messages": messages
        }
    })


@consultation_bp.route('/message/stream', methods=['POST'])
@login_required
def send_message_stream():
    """发送问诊消息（流式模式，Agent ReAct 循环）"""
    data = request.json or {}
    session_id = data.get("conversation_id")
    user_message = data.get("message", "")
    user_id = get_current_user_id()

    if not session_id or not user_message:
        return jsonify({"success": False, "error": "缺少必要参数"}), 400

    image_base64 = data.get("image_base64")
    image_mime = data.get("image_mime")

    def generate():
        for chunk in AgentService.send_message_stream(
            session_id, user_message, user_id,
            image_base64=image_base64, image_mime=image_mime
        ):
            yield f"data: {chunk}\n\n"

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )


@consultation_bp.route('/history', methods=['GET'])
@login_required
def get_consultation_history():
    """获取问诊历史"""
    user_id = get_current_user_id()
    history = AgentService.get_history(user_id)
    return jsonify({"success": True, "data": history})


@consultation_bp.route('/<session_id>', methods=['GET'])
@login_required
def get_consultation_detail(session_id):
    """获取问诊详情"""
    user_id = get_current_user_id()
    detail = AgentService.get_detail(session_id, user_id)
    if not detail:
        return jsonify({"success": False, "error": "会话不存在"}), 404
    return jsonify({"success": True, "data": detail})


@consultation_bp.route('/<session_id>', methods=['PATCH'])
@login_required
def rename_consultation(session_id):
    """重命名会话"""
    user_id = get_current_user_id()
    summary = (request.json or {}).get('summary', '').strip()
    if not summary:
        return jsonify({"success": False, "error": "名称不能为空"}), 400
    ok = AgentService.rename_consultation(session_id, summary, user_id)
    if not ok:
        return jsonify({"success": False, "error": "会话不存在或无权限"}), 404
    return jsonify({"success": True})


@consultation_bp.route('/<session_id>', methods=['DELETE'])
@login_required
def delete_consultation(session_id):
    """删除会话"""
    user_id = get_current_user_id()
    ok = AgentService.delete_consultation(session_id, user_id)
    if not ok:
        return jsonify({"success": False, "error": "会话不存在或无权限"}), 404
    return jsonify({"success": True})
