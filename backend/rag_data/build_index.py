"""
RAG 索引构建脚本
将《默克家庭诊疗手册》按节分块，通过 SiliconFlow bge-m3 embedding，写入本地 ChromaDB
用法：python build_index.py
"""
import os
import re
import sys
import time
import httpx
import chromadb

# ==================== 配置 ====================
RAG_DATA_DIR = os.path.dirname(os.path.abspath(__file__))
TXT_FILE = os.path.join(RAG_DATA_DIR, "默克家庭诊疗手册.txt")
CHROMA_DIR = os.path.join(RAG_DATA_DIR, "chroma_db")
COLLECTION_NAME = "merck_manual"

# SiliconFlow API
sys.path.insert(0, os.path.join(RAG_DATA_DIR, ".."))
from config import config

SILICONFLOW_API_KEY = config.LLM_API_KEY
EMBED_MODEL = "BAAI/bge-m3"
EMBED_URL = "https://api.siliconflow.cn/v1/embeddings"
EMBED_BATCH_SIZE = 4    # 每批 embedding 的 chunk 数（避免 413）
EMBED_RETRY = 3         # 失败重试次数


# ==================== 文本分块 ====================

def load_and_split(filepath: str) -> list[dict]:
    """
    按「第X节」分块，返回 [{title, chapter, section, text}, ...]
    同时跳过目录区域（第57行前）
    """
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 章节标题匹配
    chapter_pat = re.compile(r"^第[零一二三四五六七八九十百]+章\s+(.+)")
    section_pat = re.compile(r"^第\d+节[\s　]+(.+)")

    chunks = []
    current_chapter = ""
    current_section = ""
    current_lines = []
    in_toc = True   # 跳过目录

    def flush(chapter, section, lines_buf):
        text = "\n".join(l.rstrip() for l in lines_buf).strip()
        # 去除连续空行（超过2行的压缩为1行）
        text = re.sub(r"\n{3,}", "\n\n", text)
        if len(text) < 50:   # 太短的忽略
            return
        chunks.append({
            "title": f"{chapter} / {section}" if section else chapter,
            "chapter": chapter,
            "section": section,
            "text": text,
        })

    for line in lines:
        stripped = line.strip()

        # 跳过目录（检测到第一章正文出现后才开始）
        if in_toc:
            if chapter_pat.match(stripped) and len(chunks) == 0:
                # 检查后续是否有正文（目录里的章节行不要收集）
                pass
            # 目录结束标志：出现"第1节"正文
            if section_pat.match(stripped) and current_chapter:
                in_toc = False
            # 目录中遇到章节标题，记录当前章
            m = chapter_pat.match(stripped)
            if m:
                current_chapter = stripped
            continue

        m_chapter = chapter_pat.match(stripped)
        m_section = section_pat.match(stripped)

        if m_chapter:
            # 新章开始：flush 当前节
            if current_section and current_lines:
                flush(current_chapter, current_section, current_lines)
            current_chapter = stripped
            current_section = ""
            current_lines = []

        elif m_section:
            # 新节开始：flush 当前节
            if current_lines:
                flush(current_chapter, current_section, current_lines)
            current_section = stripped
            current_lines = []

        else:
            # 跳过"回总目录"等导航文本
            if stripped in ("回总目录", "回本章目录"):
                continue
            current_lines.append(line.rstrip())

    # 最后一节
    if current_lines:
        flush(current_chapter, current_section, current_lines)

    return chunks


# ==================== Embedding ====================

def embed_texts(texts: list[str]) -> list[list[float]]:
    """调用 SiliconFlow bge-m3 批量 embedding"""
    headers = {
        "Authorization": f"Bearer {SILICONFLOW_API_KEY}",
        "Content-Type": "application/json",
    }
    all_embeddings = []

    for i in range(0, len(texts), EMBED_BATCH_SIZE):
        batch = texts[i: i + EMBED_BATCH_SIZE]
        for attempt in range(EMBED_RETRY):
            try:
                resp = httpx.post(
                    EMBED_URL,
                    headers=headers,
                    json={"model": EMBED_MODEL, "input": batch},
                    timeout=60,
                )
                resp.raise_for_status()
                data = resp.json()
                batch_embeddings = [item["embedding"] for item in sorted(data["data"], key=lambda x: x["index"])]
                all_embeddings.extend(batch_embeddings)
                print(f"  ✅ Batch {i // EMBED_BATCH_SIZE + 1}: {len(batch)} chunks embedded")
                time.sleep(0.3)  # 避免触发限流
                break
            except Exception as e:
                print(f"  ⚠️  Batch {i // EMBED_BATCH_SIZE + 1} attempt {attempt + 1} failed: {e}")
                if attempt == EMBED_RETRY - 1:
                    raise
                time.sleep(2)

    return all_embeddings


# ==================== 写入 ChromaDB ====================

def build_index():
    print("📖 读取并分块文本...")
    chunks = load_and_split(TXT_FILE)
    print(f"  共 {len(chunks)} 个 chunk")

    print("\n🔢 生成 embeddings（使用 BAAI/bge-m3 via SiliconFlow）...")
    MAX_CHUNK_CHARS = 1500  # bge-m3 单条最大字符数
    texts = [c["text"][:MAX_CHUNK_CHARS] for c in chunks]
    embeddings = embed_texts(texts)

    print(f"\n💾 写入 ChromaDB: {CHROMA_DIR}")
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    # 若已存在则删除重建
    existing = [c.name for c in client.list_collections()]
    if COLLECTION_NAME in existing:
        client.delete_collection(COLLECTION_NAME)
        print(f"  🗑️  已删除旧 collection: {COLLECTION_NAME}")

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    ids = [f"chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"title": c["title"], "chapter": c["chapter"], "section": c["section"]} for c in chunks]

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    print(f"\n🎉 索引构建完成！共写入 {len(chunks)} 条文档到 '{COLLECTION_NAME}'")


if __name__ == "__main__":
    build_index()
