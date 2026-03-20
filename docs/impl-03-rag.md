# RAG 知识检索——实现细节

> 对应源文件：`backend/services/rag_service.py`、`backend/rag_data/build_index.py`、`backend/services/agent_tools.py`（`get_health_knowledge`）
> 更新日期：2025-03

---

## 一、设计目标

大语言模型的医学知识来自训练数据，存在时效性限制且无法保证权威性。RAG（Retrieval-Augmented Generation）的核心思路是：**每次回答时先从权威文献中检索相关内容，再将检索到的片段作为 context 提供给 LLM**，使回答有可溯源的依据。

本系统以《默克家庭诊疗手册》（中文版，3.5MB）作为知识源，该手册是全球最广泛使用的医学参考书之一，内容涵盖疾病、症状、药物、检查项目等。

---

## 二、索引构建（`build_index.py`）

### 文本切分

读取 `默克家庭诊疗手册.txt`，按段落切分为 chunks，每个 chunk 约 300–500 字，相邻 chunk 之间有 50 字重叠（overlap）防止语义截断：

```python
def split_text(text, chunk_size=400, overlap=50):
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks
```

### 科室路由分片

构建时根据关键词将 chunks 分配到 5 个 ChromaDB Collection：

| Collection | 路由关键词（示例） |
|-----------|----------------|
| `merck_manual` | 全量（所有 chunks 都进入） |
| `dept_cardiology` | 心脏、血压、心肌梗死、冠心病、动脉 |
| `dept_endocrinology` | 糖尿病、胰岛素、甲状腺、血糖、代谢 |
| `dept_dermatology` | 皮肤、湿疹、荨麻疹、痤疮、皮疹 |
| `dept_general` | 其余未命中专科的内容 |

每个 chunk 可能同时进入全量 Collection 和专科 Collection（不互斥）。

### Embedding 生成

调用硅基流动 Embedding API（`BAAI/bge-m3`）将每个 chunk 向量化，向量维度 1024：

```python
def embed_texts(texts: list[str]) -> list[list[float]]:
    client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
    response = client.embeddings.create(
        model="BAAI/bge-m3",
        input=texts,
        encoding_format="float"
    )
    return [item.embedding for item in response.data]
```

构建时批量处理（batch_size=32）并在本地持久化到 `rag_data/chroma_db/`，无需每次启动重新计算。

---

## 三、检索流程（`rag_service.py`）

### 两阶段检索：召回 → 精排

```
用户 query
   ↓
① 向量召回
   bge-m3 embed(query) → ChromaDB 相似度搜索 → Top-20 候选
   ↓
② 精排（Reranking）
   bge-reranker-v2-m3 对 (query, chunk) 对打相关性分数 → Top-3
   ↓
③ 返回结果
   [{ title, text, relevance_score }, ...]
```

### 向量召回实现

```python
collection = chroma_client.get_collection(collection_name)
query_embedding = embed_texts([query])[0]

results = collection.query(
    query_embeddings=[query_embedding],
    n_results=20,              # 召回 20 条候选
    include=["documents", "metadatas", "distances"]
)
```

ChromaDB 使用余弦相似度计算向量距离。

### Reranking 实现

bge-reranker 是 cross-encoder 架构，输入是 (query, document) 拼接对，直接输出相关性分数，比 bi-encoder（向量检索）的语义理解更精准：

```python
def rerank(query: str, documents: list[str], top_n: int = 3) -> list[dict]:
    client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
    
    # 硅基流动 Reranker API
    response = client.post("/rerank", json={
        "model": "BAAI/bge-reranker-v2-m3",
        "query": query,
        "documents": documents,
        "top_n": top_n,
        "return_documents": True,
    })
    
    results = response.json()["results"]
    return [
        {
            "text": r["document"]["text"],
            "relevance_score": r["relevance_score"],
            "index": r["index"]
        }
        for r in results
    ]
```

### 科室路由

Agent 调用 `get_health_knowledge` 工具时携带 `department` 参数，RAGService 优先使用对应科室 Collection：

```python
collection_name = f"dept_{department}"   # 如 dept_cardiology
if not collection_exists(collection_name):
    collection_name = "merck_manual"      # 降级到全量
```

---

## 四、降级链路

```
① RAG 检索（ChromaDB）
   ↓（失败/索引未构建）
② SQLite 结构化知识库（health_knowledge 表）
   模糊匹配：WHERE title LIKE ? OR keywords LIKE ? OR content LIKE ?
   ↓（无匹配）
③ 返回空结果，LLM 凭自身知识回答
```

这三层降级保证了系统在各种部署状态下均可正常运行：开发环境没有构建 RAG 索引时，仍然有结构化知识库兜底。

---

## 五、工具集成（`get_health_knowledge`）

Agent 调用该工具时的完整链路：

```python
def get_health_knowledge(user_id, query, department="general", top_n=3, **kwargs) -> str:
    try:
        # 优先 RAG
        results = RAGService.search(query, department=department, top_n=top_n)
        if results:
            knowledge_text = "\n\n".join([
                f"【{r.get('title', '相关知识')}】\n{r['text']}"
                for r in results
            ])
            return json.dumps({
                "success": True,
                "source": "rag",
                "knowledge": knowledge_text,
                "result_count": len(results)
            })
    except Exception:
        pass
    
    # 降级：SQLite 结构化知识库
    db = SessionLocal()
    try:
        items = db.query(HealthKnowledge).filter(
            or_(
                HealthKnowledge.title.ilike(f"%{query}%"),
                HealthKnowledge.keywords.ilike(f"%{query}%"),
                HealthKnowledge.content.ilike(f"%{query}%"),
            )
        ).limit(3).all()
        ...
    finally:
        db.close()
```

工具返回的 `knowledge` 字段会被 Agent 直接引用，在最终回复中以"根据医学知识库..."的形式呈现，明确知识来源。

---

## 六、管理员 RAG 管理接口

系统提供了完整的 RAG 运维接口（`/api/admin/rag/*`）：

- **`GET /admin/rag/stats`**：查看各 Collection 的 chunk 数量、最后更新时间
- **`GET /admin/rag/chunks`**：分页浏览向量库中的所有文本块（支持关键词搜索）
- **`POST /admin/rag/search`**：测试检索效果（输入 query，返回 Top-N 结果及相关性分数）

这使得管理员可以在不接触代码的情况下验证 RAG 检索质量。

---

## 七、bge-m3 与 bge-reranker 选型理由

| 模型 | 类型 | 特点 |
|------|------|------|
| BAAI/bge-m3 | Bi-encoder | 多语言支持，中文表现优秀；向量化后可离线检索，速度快 |
| BAAI/bge-reranker-v2-m3 | Cross-encoder | 对 (query, doc) 精确建模，相关性判断比向量相似度更准确 |

两阶段组合的优势：向量召回速度快（可处理大规模语料），reranker 精度高但计算量大（只对小数候选集重排），兼顾效率与质量。
