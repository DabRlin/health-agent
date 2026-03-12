"""
RAG 索引构建脚本
将《默克家庭诊疗手册》按节分块，通过 SiliconFlow bge-m3 embedding，写入本地 ChromaDB

用法：
  python build_index.py              # 仅构建全量 merck_manual collection
  python build_index.py --dept       # 构建全量 + 四个科室 collection
  python build_index.py --dept-only  # 仅构建四个科室 collection（不重建全量）
"""
import os
import re
import sys
import time
import argparse
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

# ==================== 科室→章节映射 ====================
# key: collection 名称，value: 包含的章节标题关键词（匹配 chunk["chapter"]）
DEPT_COLLECTIONS = {
    "dept_cardiology": {
        "label": "心血管科",
        "chapters": ["第三章 心血管疾病"],
    },
    "dept_endocrinology": {
        "label": "内分泌科",
        "chapters": [
            "第十二章 营养与代谢障碍",
            "第十三章 内分泌疾病",
        ],
    },
    "dept_dermatology": {
        "label": "皮肤科",
        "chapters": ["第十八章 皮肤疾病"],
    },
    "dept_general": {
        "label": "全科（精选）",
        "chapters": [
            "第一章 基础",
            "第二章 药物",
            "第三章 心血管疾病",
            "第四章 肺和气道疾病",
            "第五章 骨骼、关节和肌肉疾病",
            "第六章 脑和神经疾病",
            "第七章 精神疾病",
            "第九章 消化系统疾病",
            "第十章 肝胆疾病",
            "第十一章 肾脏和尿路疾病",
            "第十二章 营养与代谢障碍",
            "第十三章 内分泌疾病",
            "第十七章 感染性疾病",
            "第十八章 皮肤疾病",
        ],
    },
}


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


# ==================== 科室分集构建 ====================

def build_dept_index(all_chunks: list[dict]):
    """根据 DEPT_COLLECTIONS 映射，为每个科室建立独立 collection"""
    client = chromadb.PersistentClient(path=CHROMA_DIR)

    for coll_name, dept_cfg in DEPT_COLLECTIONS.items():
        label = dept_cfg["label"]
        target_chapters = set(dept_cfg["chapters"])

        # 按章节过滤
        dept_chunks = [c for c in all_chunks if c["chapter"] in target_chapters]
        if not dept_chunks:
            print(f"\n⚠️  {label}（{coll_name}）：未找到匹配章节，跳过")
            continue

        print(f"\n📚 构建 {label}（{coll_name}）：{len(dept_chunks)} 个 chunk")

        print(f"  🔢 生成 embeddings...")
        MAX_CHUNK_CHARS = 1500
        texts = [c["text"][:MAX_CHUNK_CHARS] for c in dept_chunks]
        embeddings = embed_texts(texts)

        # 删除旧 collection（若存在）
        existing = [c.name for c in client.list_collections()]
        if coll_name in existing:
            client.delete_collection(coll_name)
            print(f"  🗑️  已删除旧 collection: {coll_name}")

        collection = client.create_collection(
            name=coll_name,
            metadata={"hnsw:space": "cosine"},
        )

        ids = [f"{coll_name}_chunk_{i}" for i in range(len(dept_chunks))]
        metadatas = [
            {"title": c["title"], "chapter": c["chapter"], "section": c["section"]}
            for c in dept_chunks
        ]
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )
        print(f"  ✅ {label} 写入完成，共 {len(dept_chunks)} 条")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAG 索引构建工具")
    parser.add_argument("--dept", action="store_true", help="构建全量 + 科室 collection")
    parser.add_argument("--dept-only", action="store_true", help="仅构建科室 collection，跳过全量重建")
    args = parser.parse_args()

    if args.dept_only:
        # 只拆分文本，不重建全量
        print("📖 读取并分块文本（科室模式）...")
        all_chunks = load_and_split(TXT_FILE)
        print(f"  共 {len(all_chunks)} 个 chunk")
        build_dept_index(all_chunks)
        print("\n🎉 科室索引构建完成！")
    elif args.dept:
        # 先建全量，再建科室
        all_chunks_for_dept = load_and_split(TXT_FILE)
        build_index()
        print("\n" + "="*50)
        print("开始构建科室分集索引...")
        build_dept_index(all_chunks_for_dept)
        print("\n🎉 全量 + 科室索引均构建完成！")
    else:
        # 默认：只建全量
        build_index()
