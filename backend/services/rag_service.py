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
COLLECTION_NAME = "merck_manual"

EMBED_URL = "https://api.siliconflow.cn/v1/embeddings"
RERANK_URL = "https://api.siliconflow.cn/v1/rerank"
EMBED_MODEL = "BAAI/bge-m3"
RERANK_MODEL = "BAAI/bge-reranker-v2-m3"

RECALL_TOP_K = 20    # 向量检索召回数
RERANK_TOP_N = 3     # reranker 精选数


class RAGService:
    _client: Optional[chromadb.PersistentClient] = None
    _collection = None
    _api_key: Optional[str] = None

    @classmethod
    def _get_collection(cls):
        if cls._collection is None:
            if not os.path.exists(CHROMA_DIR):
                raise RuntimeError(
                    "RAG 索引不存在，请先运行 backend/rag_data/build_index.py 构建索引"
                )
            cls._client = chromadb.PersistentClient(path=CHROMA_DIR)
            cls._collection = cls._client.get_collection(COLLECTION_NAME)
        return cls._collection

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
    def search(cls, query: str, top_n: int = RERANK_TOP_N) -> list[dict]:
        """
        RAG 检索主入口：向量召回 → reranker 重排 → 返回 top_n 结果

        Returns:
            [{"title": str, "text": str, "score": float}, ...]
        """
        collection = cls._get_collection()

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
    def is_ready(cls) -> bool:
        """检查索引是否已构建"""
        return os.path.exists(CHROMA_DIR)
