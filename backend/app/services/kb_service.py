
from pydoc import doc
from typing import final
from chromadb.api.models.Collection import Collection
from chromadb.utils import embedding_functions
import chromadb
from app.config import BASE_DIR

KB_DIR = BASE_DIR / "data" / "kb"
CHROMA_DIR = BASE_DIR / "data" / "chroma"

_collection = None
_embedding_fn = None


def get_embedding_fn():
    """懒加载 embedding 模型：只加载一次，之后复用同一个实例"""
    global _embedding_fn
    if _embedding_fn is not None:
        return _embedding_fn
    # SentenceTransformerEmbeddingFunction 自带类级缓存，同名模型也不会重复加载
    _embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="BAAI/bge-small-zh-v1.5"
    )
    return _embedding_fn

# get_collcetion() 里换掉引用
# col = client.get_or_create_collection(
#     name="lab_kb", embedding_function=get_embedding_fn()
# )    

def warmup():
    """启动时预热：把模型加载+首次检索的开销付在启动阶段，别落在第一个用户请求上"""
    col = get_collcetion()
    if col.count() > 0:
        col.query(query_texts=["预热"], n_results=1)

def get_collcetion() -> Collection:
    """向量库的初始化"""

    global _collection
    if _collection is not None:
        return _collection
    KB_DIR.mkdir(parents=True, exist_ok=True)
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    col = client.get_or_create_collection(
        name="lab_kb", embedding_function=get_embedding_fn()
    )
    if col.count() == 0:
        ids = []
        docs = []
        metas = []
        for path in sorted(KB_DIR.glob("*.md")):
            text = path.read_text(encoding="UTF-8").strip()
            if not text:
                continue
            docs.append(text)
            ids.append(path.stem)
            metas.append({"source": path.name})
        if docs:
            col.add(ids=ids, documents=docs, metadatas=metas)
    _collection = col
    return col

def retrieve(
    query: str, n_results: int = 5, min_score: float = 0.0
) -> list[dict]:
    """检索并返回按相关度排序的结果，供 search 和离线评测共用。

    score = 1 / (1 + distance)，取值 0-1，越接近 1 越相关。
    """
    col = get_collcetion()
    if col.count() == 0:
        return []
    limit = min(n_results, col.count())
    res = col.query(query_texts=[query], n_results=limit)
    docs = (res.get("documents") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]
    distances = (res.get("distances") or [[]])[0]

    results = []
    for doc, meta, dist in zip(docs, metas, distances):
        score = 1 / (1 + dist)
        if score < min_score:
            continue
        results.append(
            {
                "source": (meta or {}).get("source") or "",
                "content": doc,
                "score": score,
            }
        )
    results.sort(key=lambda item: item["score"], reverse=True)
    return results


def search(query: str):
    """根据关键字去检索向量库，返回拼好的 Top-2 正文注入 System Prompt。"""
    results = retrieve(query, n_results=5, min_score=0.5)
    return "\n\n".join(
        f"[{item['source']}]\n{item['content']}" for item in results[:2]
    )