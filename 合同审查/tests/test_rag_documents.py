"""
RAG 文档向量化测试脚本

将 e:\Professional\合同审查agent\合同审查\documents 中的文件：
- 第一.docx
- 第二.docx
- 第三.docx

通过 RAG 流程存入向量数据库（Chroma）。
"""

import os
import sys
import asyncio
import uuid
from datetime import datetime
from typing import List, Dict, Any

# 设置项目根目录
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from 合同审查.app.core.config import settings
from 合同审查.app.rag.embeddings import Embeddings
from 合同审查.app.rag.vector_store import VectorStore
from 合同审查.app.rag.contract_schema import ClauseChunk


# 文档目录
DOCUMENTS_DIR = r"e:\Professional\合同审查agent\合同审查\documents"

# 向量数据库持久化目录
VECTOR_DB_DIR = os.path.join(project_root, "data", "vector_db", "law_documents")
os.makedirs(VECTOR_DB_DIR, exist_ok=True)


def read_docx_file(file_path: str) -> str:
    """读取 docx 文件内容"""
    try:
        from docx import Document
        doc = Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs)
    except ImportError:
        print("错误：未安装 python-docx，请运行: pip install python-docx")
        raise
    except Exception as e:
        print(f"读取文件 {file_path} 失败: {e}")
        raise


def split_text_into_chunks(text: str, chunk_size: int = 500, overlap: int = 100) -> List[Dict[str, Any]]:
    """
    将文本拆分为语义块

    Args:
        text: 原始文本
        chunk_size: 每个块的最大字符数
        overlap: 块之间的重叠字符数

    Returns:
        List[Dict]: 文本块列表，每个块包含 content 和 metadata
    """
    chunks = []

    # 按段落分割
    paragraphs = [p.strip() for p in text.split('\n') if p.strip()]

    current_chunk = []
    current_length = 0
    chunk_index = 0

    for para in paragraphs:
        para_length = len(para)

        # 如果当前段落加上已有内容超过 chunk_size，先保存当前块
        if current_length + para_length > chunk_size and current_chunk:
            chunk_text = "\n".join(current_chunk)
            chunks.append({
                "content": chunk_text,
                "metadata": {
                    "chunk_index": chunk_index,
                    "char_count": len(chunk_text),
                }
            })
            chunk_index += 1

            # 保留重叠部分
            overlap_text = "\n".join(current_chunk)[-overlap:] if current_length > overlap else ""
            current_chunk = [overlap_text, para] if overlap_text else [para]
            current_length = len(overlap_text) + para_length if overlap_text else para_length
        else:
            current_chunk.append(para)
            current_length += para_length

    # 保存最后一个块
    if current_chunk:
        chunk_text = "\n".join(current_chunk)
        chunks.append({
            "content": chunk_text,
            "metadata": {
                "chunk_index": chunk_index,
                "char_count": len(chunk_text),
            }
        })

    return chunks


def create_clause_chunks(
    file_name: str,
    file_path: str,
    text_chunks: List[Dict[str, Any]]
) -> List[ClauseChunk]:
    """
    将文本块转换为 ClauseChunk 对象

    Args:
        file_name: 文件名
        file_path: 文件路径
        text_chunks: 文本块列表

    Returns:
        List[ClauseChunk]: 条款块列表
    """
    chunks = []
    doc_id = str(uuid.uuid4())[:8]

    for i, chunk_data in enumerate(text_chunks):
        chunk = ClauseChunk(
            clause_id=f"{doc_id}_chunk_{i:03d}",
            clause_no=f"第{i+1}段",
            clause_content=chunk_data["content"],
            clause_title=f"{file_name} - 片段{i+1}",
            metadata={
                "source_file": file_name,
                "file_path": file_path,
                "doc_id": doc_id,
                "chunk_index": chunk_data["metadata"]["chunk_index"],
                "char_count": chunk_data["metadata"]["char_count"],
                "upload_time": datetime.now().isoformat(),
            }
        )
        chunks.append(chunk)

    return chunks


async def process_document(
    file_path: str,
    embeddings: Embeddings,
    vector_store: VectorStore
) -> Dict[str, Any]:
    """
    处理单个文档：读取 -> 分块 -> 嵌入 -> 存储

    Args:
        file_path: 文档路径
        embeddings: 嵌入模型
        vector_store: 向量存储

    Returns:
        Dict: 处理结果
    """
    file_name = os.path.basename(file_path)
    print(f"\n{'='*60}")
    print(f"处理文档: {file_name}")
    print(f"{'='*60}")

    # 1. 读取文档
    print(f"[1/4] 读取文档...")
    text = read_docx_file(file_path)
    print(f"      文档字符数: {len(text)}")

    # 2. 文本分块
    print(f"[2/4] 文本分块...")
    text_chunks = split_text_into_chunks(text, chunk_size=800, overlap=150)
    print(f"      分成 {len(text_chunks)} 个块")

    # 3. 转换为 ClauseChunk
    print(f"[3/4] 创建条款块...")
    clause_chunks = create_clause_chunks(file_name, file_path, text_chunks)

    # 4. 生成嵌入向量
    print(f"[4/4] 生成嵌入向量并存储...")
    texts = [chunk.to_text() for chunk in clause_chunks]

    # 使用线程池执行同步嵌入
    loop = asyncio.get_event_loop()
    embeddings_list = await loop.run_in_executor(
        None,
        embeddings.embed_documents,
        texts
    )
    print(f"      生成 {len(embeddings_list)} 个向量，维度: {len(embeddings_list[0])}")

    # 5. 存入向量数据库
    ids = vector_store.add_clauses(clause_chunks, embeddings_list)
    print(f"      成功存储 {len(ids)} 条记录")

    return {
        "file_name": file_name,
        "file_path": file_path,
        "total_chars": len(text),
        "chunk_count": len(clause_chunks),
        "vector_count": len(ids),
        "vector_ids": ids,
    }


async def main():
    """主函数"""
    print("="*60)
    print("RAG 文档向量化测试")
    print("="*60)
    print(f"文档目录: {DOCUMENTS_DIR}")
    print(f"向量数据库: {VECTOR_DB_DIR}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 初始化嵌入模型
    print("\n[初始化] 加载嵌入模型 (DashScope)...")
    embeddings = Embeddings(embedding_type=settings.EMBEDDING_TYPE)
    print("         嵌入模型加载完成")

    # 初始化向量存储
    print("[初始化] 连接向量数据库 (Chroma)...")
    vector_store = VectorStore(
        store_type="chroma",
        collection_name="law_documents",
        persist_directory=VECTOR_DB_DIR,
    )
    print("         向量数据库连接完成")

    # 获取文档列表
    doc_files = [f for f in os.listdir(DOCUMENTS_DIR) if f.endswith('.docx')]
    doc_files.sort()

    if not doc_files:
        print(f"\n错误: 未在 {DOCUMENTS_DIR} 找到 .docx 文件")
        return

    print(f"\n发现 {len(doc_files)} 个文档:")
    for f in doc_files:
        print(f"  - {f}")

    # 处理每个文档
    results = []
    for doc_file in doc_files:
        file_path = os.path.join(DOCUMENTS_DIR, doc_file)
        try:
            result = await process_document(file_path, embeddings, vector_store)
            results.append(result)
        except Exception as e:
            print(f"处理 {doc_file} 失败: {e}")
            import traceback
            traceback.print_exc()

    # 统计结果
    print("\n" + "="*60)
    print("处理完成统计")
    print("="*60)
    total_chunks = sum(r["chunk_count"] for r in results)
    total_vectors = sum(r["vector_count"] for r in results)
    print(f"成功处理文档: {len(results)}/{len(doc_files)}")
    print(f"总文本块数: {total_chunks}")
    print(f"总向量数: {total_vectors}")

    # 显示向量数据库统计
    try:
        count = vector_store.store.count()
        print(f"向量数据库总记录数: {count}")
    except Exception as e:
        print(f"获取向量数据库统计失败: {e}")

    print("\n测试完成！")


if __name__ == "__main__":
    asyncio.run(main())
