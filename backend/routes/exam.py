"""
体检报告路由
"""
import logging
from flask import Blueprint, jsonify, request, send_file
from services.exam_service import ExamService
from utils import login_required, get_current_user_id

logger = logging.getLogger(__name__)

exam_bp = Blueprint('exam', __name__, url_prefix='/api/exam')


@exam_bp.route('/reports', methods=['GET'])
@login_required
def list_reports():
    """获取体检报告列表"""
    user_id = get_current_user_id()
    limit = request.args.get('limit', 20, type=int)
    reports = ExamService.get_reports(user_id, limit)
    return jsonify({"success": True, "data": reports})


@exam_bp.route('/reports/<int:report_id>', methods=['GET'])
@login_required
def get_report(report_id):
    """获取单份体检报告详情"""
    user_id = get_current_user_id()
    report = ExamService.get_report(user_id, report_id)
    if not report:
        return jsonify({"success": False, "error": "报告不存在"}), 404
    return jsonify({"success": True, "data": report})


@exam_bp.route('/reports/upload', methods=['POST'])
@login_required
def upload_report():
    """上传体检报告（图片或 PDF）"""
    user_id = get_current_user_id()

    if 'file' not in request.files:
        return jsonify({"success": False, "error": "未收到文件"}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({"success": False, "error": "文件名为空"}), 400

    allowed_types = {
        'image/jpeg', 'image/jpg', 'image/png', 'image/webp',
        'application/pdf',
    }
    mime_type = file.content_type or 'image/jpeg'
    if mime_type not in allowed_types:
        return jsonify({"success": False, "error": f"不支持的文件类型: {mime_type}"}), 400

    file_bytes = file.read()
    # 限制 10MB
    if len(file_bytes) > 10 * 1024 * 1024:
        return jsonify({"success": False, "error": "文件大小不能超过 10MB"}), 400

    try:
        result = ExamService.upload_and_process(
            user_id=user_id,
            filename=file.filename,
            file_bytes=file_bytes,
            mime_type=mime_type,
        )
        return jsonify({"success": True, "data": result})
    except Exception as e:
        logger.exception("体检报告上传处理失败")
        return jsonify({"success": False, "error": "报告处理失败，请稍后重试"}), 500


@exam_bp.route('/reports/<int:report_id>', methods=['DELETE'])
@login_required
def delete_report(report_id):
    """删除体检报告"""
    user_id = get_current_user_id()
    ok = ExamService.delete_report(user_id, report_id)
    if not ok:
        return jsonify({"success": False, "error": "报告不存在"}), 404
    return jsonify({"success": True})
