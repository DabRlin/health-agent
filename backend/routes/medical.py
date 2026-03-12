"""
医疗资料路由（普通用户只读）
"""
from flask import Blueprint, request, jsonify
from utils import login_required
from services.admin_service import AdminService
from services.rag_service import RAGService

medical_bp = Blueprint('medical', __name__, url_prefix='/api/medical')


# ==================== 结构化知识库（只读） ====================

@medical_bp.route('/knowledge', methods=['GET'])
@login_required
def list_knowledge():
    """获取知识库列表（只读，普通用户可访问）"""
    category = request.args.get('category')
    items = AdminService.list_knowledge(category)
    return jsonify({"success": True, "data": items})


# ==================== RAG 检索（只读） ====================

@medical_bp.route('/rag/stats', methods=['GET'])
@login_required
def rag_stats():
    """RAG 索引统计"""
    if not RAGService.is_ready():
        return jsonify({"success": True, "data": {"ready": False, "chunk_count": 0}})
    try:
        collection = RAGService._get_collection()
        return jsonify({"success": True, "data": {
            "ready": True,
            "chunk_count": collection.count(),
        }})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@medical_bp.route('/rag/search', methods=['POST'])
@login_required
def rag_search():
    """RAG 语义检索"""
    if not RAGService.is_ready():
        return jsonify({"success": False, "error": "RAG 索引未就绪"}), 503
    data = request.json or {}
    query = (data.get('query') or '').strip()
    if not query:
        return jsonify({"success": False, "error": "查询词不能为空"}), 400
    try:
        top_n = min(10, max(1, int(data.get('top_n', 5))))
        results = RAGService.search(query, top_n=top_n)
        return jsonify({"success": True, "data": {"query": query, "results": results}})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
