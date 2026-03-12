"""
RAG 检索服务
使用 ChromaDB + SiliconFlow bge-m3 (embedding) + bge-reranker-v2-m3 (rerank)
"""
import os
import httpx
import chromadb
from typing import Optional

RAG_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "rag_data")
CHROMA_DIR = os.path.join(RAG_DATA_DIR, "chroma_db")
COLLECTION_NAME = "merck_manual"  # 全量 collection（全科兜底）

EMBED_URL = "https://api.siliconflow.cn/v1/embeddings"
RERANK_URL = "https://api.siliconflow.cn/v1/rerank"
EMBED_MODEL = "BAAI/bge-m3"
RERANK_MODEL = "BAAI/bge-reranker-v2-m3"

RECALL_TOP_K = 20    # 向量检索召回数
RERANK_TOP_N = 3     # reranker 精选数

# 科室 → collection 名称映射
# 对应 build_index.py 中 DEPT_COLLECTIONS 的 key
DEPT_COLLECTION_MAP = {
    "general":       "dept_general",
    "cardiology":    "dept_cardiology",
    "endocrinology": "dept_endocrinology",
    "dermatology":   "dept_dermatology",
}


class RAGService:
    _client: Optional[chromadb.PersistentClient] = None
    _collections: dict = {}  # name -> collection 实例缓存
    _api_key: Optional[str] = None

    @classmethod
    def _get_client(cls):
        if cls._client is None:
            if not os.path.exists(CHROMA_DIR):
                raise RuntimeError(
                    "RAG 索引不存在，请先运行 backend/rag_data/build_index.py 构建索引"
                )
            cls._client = chromadb.PersistentClient(path=CHROMA_DIR)
        return cls._client

    @classmethod
    def _get_collection(cls, name: str = COLLECTION_NAME):
        if name not in cls._collections:
            client = cls._get_client()
            existing = [c.name for c in client.list_collections()]
            # 科室 collection 不存在时降级到全量
            if name not in existing:
                if name != COLLECTION_NAME:
                    import logging
                    logging.getLogger(__name__).warning(
                        "Collection '%s' 不存在，降级到全量 '%s'", name, COLLECTION_NAME
                    )
                    name = COLLECTION_NAME
            cls._collections[name] = client.get_collection(name)
        return cls._collections[name]

    @classmethod
    def _get_api_key(cls) -> str:
        if cls._api_key is None:
            from config import config
            cls._api_key = config.LLM_API_KEY
        return cls._api_key

    @classmethod
    def _embed_query(cls, query: str) -> list[float]:
        headers = {
            "Authorization": f"Bearer {cls._get_api_key()}",
            "Content-Type": "application/json",
        }
        resp = httpx.post(
            EMBED_URL,
            headers=headers,
            json={"model": EMBED_MODEL, "input": [query]},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["data"][0]["embedding"]

    @classmethod
    def _rerank(cls, query: str, documents: list[str], top_n: int) -> list[dict]:
        """调用 bge-reranker-v2-m3 对召回结果重排序"""
        headers = {
            "Authorization": f"Bearer {cls._get_api_key()}",
            "Content-Type": "application/json",
        }
        resp = httpx.post(
            RERANK_URL,
            headers=headers,
            json={
                "model": RERANK_MODEL,
                "query": query,
                "documents": documents,
                "top_n": top_n,
                "return_documents": True,
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("results", [])

    @classmethod
    def get_collection_for_dept(cls, department: str) -> str:
        """根据科室 ID 返回对应 collection 名称"""
        return DEPT_COLLECTION_MAP.get(department, COLLECTION_NAME)

    @classmethod
    def search(cls, query: str, top_n: int = RERANK_TOP_N,
               collection_name: Optional[str] = None) -> list[dict]:
        """
        RAG 检索主入口：向量召回 → reranker 重排 → 返回 top_n 结果

        Args:
            query: 检索问题
            top_n: 最终返回条数
            collection_name: 指定 collection，None 则使用全量 merck_manual

        Returns:
            [{"title": str, "text": str, "score": float}, ...]
        """
        collection = cls._get_collection(collection_name or COLLECTION_NAME)

        # 1. 向量检索
        query_embedding = cls._embed_query(query)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(RECALL_TOP_K, collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        docs = results["documents"][0]
        metas = results["metadatas"][0]

        if not docs:
            return []

        # 2. reranker 重排序
        reranked = cls._rerank(query, docs, top_n=top_n)

        # 3. 组装返回结果
        output = []
        for item in reranked:
            idx = item.get("index", 0)
            output.append({
                "title": metas[idx].get("title", ""),
                "text": item.get("document", {}).get("text", docs[idx]),
                "score": round(item.get("relevance_score", 0.0), 4),
            })

        return output

    @classmethod
    def is_ready(cls, collection_name: Optional[str] = None) -> bool:
        """检查索引是否已构建（指定 collection 时检查该 collection 是否存在）"""
        if not os.path.exists(CHROMA_DIR):
            return False
        if collection_name:
            try:
                client = chromadb.PersistentClient(path=CHROMA_DIR)
                existing = [c.name for c in client.list_collections()]
                return collection_name in existing
            except Exception:
                return False
        return True

    @classmethod
    def list_collections(cls) -> list[str]:
        """返回所有已有 collection 名称"""
        try:
            client = cls._get_client()
            return [c.name for c in client.list_collections()]
        except Exception:
            return []
