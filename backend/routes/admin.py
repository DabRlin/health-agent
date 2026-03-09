"""
管理员 API 路由
"""
from flask import Blueprint, request, jsonify
from utils import admin_required
from services.admin_service import AdminService
from services.rag_service import RAGService

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


# ==================== 统计概览 ====================

@admin_bp.route('/stats', methods=['GET'])
@admin_required
def get_stats():
    """管理后台统计数据"""
    data = AdminService.get_stats()
    return jsonify({"success": True, "data": data})


# ==================== 用户管理 ====================

@admin_bp.route('/users', methods=['GET'])
@admin_required
def list_users():
    """获取用户列表"""
    users = AdminService.list_users()
    return jsonify({"success": True, "data": users})


@admin_bp.route('/users/<int:account_id>/toggle', methods=['POST'])
@admin_required
def toggle_user(account_id):
    """启用/禁用用户"""
    success, error = AdminService.toggle_user_active(account_id)
    if not success:
        return jsonify({"success": False, "error": error}), 400
    return jsonify({"success": True, "message": "操作成功"})


@admin_bp.route('/users/<int:account_id>/reset-password', methods=['POST'])
@admin_required
def reset_password(account_id):
    """重置用户密码"""
    data = request.json or {}
    new_password = data.get('new_password', '')
    success, error = AdminService.reset_user_password(account_id, new_password)
    if not success:
        return jsonify({"success": False, "error": error}), 400
    return jsonify({"success": True, "message": "密码已重置"})


# ==================== 知识库管理 ====================

@admin_bp.route('/knowledge', methods=['GET'])
@admin_required
def list_knowledge():
    """获取知识库列表"""
    category = request.args.get('category')
    items = AdminService.list_knowledge(category)
    return jsonify({"success": True, "data": items})


@admin_bp.route('/knowledge/<int:item_id>', methods=['GET'])
@admin_required
def get_knowledge(item_id):
    """获取单条知识"""
    item = AdminService.get_knowledge(item_id)
    if not item:
        return jsonify({"success": False, "error": "条目不存在"}), 404
    return jsonify({"success": True, "data": item})


@admin_bp.route('/knowledge', methods=['POST'])
@admin_required
def create_knowledge():
    """新增知识条目"""
    data = request.json or {}
    success, result, error = AdminService.create_knowledge(data)
    if not success:
        return jsonify({"success": False, "error": error}), 400
    return jsonify({"success": True, "data": result}), 201


@admin_bp.route('/knowledge/<int:item_id>', methods=['PUT'])
@admin_required
def update_knowledge(item_id):
    """更新知识条目"""
    data = request.json or {}
    success, error = AdminService.update_knowledge(item_id, data)
    if not success:
        return jsonify({"success": False, "error": error}), 400
    return jsonify({"success": True, "message": "更新成功"})


@admin_bp.route('/knowledge/<int:item_id>', methods=['DELETE'])
@admin_required
def delete_knowledge(item_id):
    """删除知识条目"""
    success, error = AdminService.delete_knowledge(item_id)
    if not success:
        return jsonify({"success": False, "error": error}), 400
    return jsonify({"success": True, "message": "删除成功"})


# ==================== RAG 知识库 ====================

@admin_bp.route('/rag/stats', methods=['GET'])
@admin_required
def rag_stats():
    """RAG 索引统计信息"""
    if not RAGService.is_ready():
        return jsonify({"success": True, "data": {"ready": False, "chunk_count": 0, "collection": None}})
    try:
        collection = RAGService._get_collection()
        return jsonify({"success": True, "data": {
            "ready": True,
            "chunk_count": collection.count(),
            "collection": collection.name,
        }})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route('/rag/chunks', methods=['GET'])
@admin_required
def rag_chunks():
    """分页获取 RAG chunk 列表"""
    if not RAGService.is_ready():
        return jsonify({"success": False, "error": "RAG 索引未就绪"}), 503
    try:
        page = max(1, int(request.args.get('page', 1)))
        size = min(50, max(5, int(request.args.get('size', 20))))
        search = (request.args.get('search') or '').strip()

        collection = RAGService._get_collection()
        total = collection.count()

        # ChromaDB 不支持原生分页，先获取全部再切片
        # 带搜索时用 where_document 过滤
        kwargs = {
            "include": ["documents", "metadatas"],
            "limit": total,
        }
        if search:
            kwargs["where_document"] = {"$contains": search}

        results = collection.get(**kwargs)
        docs = results.get("documents") or []
        metas = results.get("metadatas") or []

        # 分页切片
        start = (page - 1) * size
        end = start + size
        page_docs = docs[start:end]
        page_metas = metas[start:end]

        chunks = [
            {
                "index": start + i,
                "title": page_metas[i].get("title", ""),
                "chapter": page_metas[i].get("chapter", ""),
                "section": page_metas[i].get("section", ""),
                "preview": page_docs[i][:200],
                "length": len(page_docs[i]),
            }
            for i in range(len(page_docs))
        ]

        return jsonify({"success": True, "data": {
            "chunks": chunks,
            "total": len(docs),
            "page": page,
            "size": size,
            "pages": (len(docs) + size - 1) // size,
        }})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@admin_bp.route('/rag/search', methods=['POST'])
@admin_required
def rag_search():
    """RAG 检索测试"""
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
