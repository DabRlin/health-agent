"""
智能问诊路由
"""
from flask import Blueprint, jsonify, request, Response
from services import ConsultationService
from utils import login_required, get_current_user_id

consultation_bp = Blueprint('consultation', __name__, url_prefix='/api/consultation')


@consultation_bp.route('/start', methods=['POST'])
@login_required
def start_consultation():
    """开始问诊会话"""
    user_id = get_current_user_id()
    session_id, messages = ConsultationService.start_consultation(user_id)
    return jsonify({
        "success": True,
        "data": {
            "conversation_id": session_id,
            "messages": messages
        }
    })


@consultation_bp.route('/message', methods=['POST'])
@login_required
def send_message():
    """发送问诊消息（阻塞模式）"""
    data = request.json or {}
    session_id = data.get("conversation_id")
    user_message = data.get("message", "")
    
    if not session_id or not user_message:
        return jsonify({"success": False, "error": "缺少必要参数"}), 400
    
    user_msg, ai_msg, error = ConsultationService.send_message(session_id, user_message)
    
    if error:
        return jsonify({"success": False, "error": error}), 404
    
    return jsonify({
        "success": True,
        "data": {
            "user_message": user_msg,
            "ai_message": ai_msg
        }
    })


@consultation_bp.route('/message/stream', methods=['POST'])
@login_required
def send_message_stream():
    """发送问诊消息（流式模式）"""
    data = request.json or {}
    session_id = data.get("conversation_id")
    user_message = data.get("message", "")
    
    if not session_id or not user_message:
        return jsonify({"success": False, "error": "缺少必要参数"}), 400
    
    def generate():
        for chunk in ConsultationService.send_message_stream(session_id, user_message):
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
    history = ConsultationService.get_history(user_id)
    return jsonify({"success": True, "data": history})


@consultation_bp.route('/<session_id>', methods=['GET'])
@login_required
def get_consultation_detail(session_id):
    """获取问诊详情"""
    detail = ConsultationService.get_detail(session_id)
    if not detail:
        return jsonify({"success": False, "error": "会话不存在"}), 404
    return jsonify({"success": True, "data": detail})
