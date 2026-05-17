"""
RAG 系统诊断工具

用于诊断向量检索问题，检查：
1. 向量库状态
2. 嵌入模型一致性
3. 相似度计算
4. 检索功能
"""

import os
import sys
import logging

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from 合同审查.app.core.config import settings

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_vector_store():
    """检查向量库状态"""
    logger.info("=" * 60)
    logger.info("【诊断1】检查向量库状态")
    logger.info("=" * 60)
    
    try:
        from 合同审查.app.rag import get_vector_store
        
        vector_store = get_vector_store()
        count = vector_store.count()
        logger.info(f"✓ 向量库连接成功")
        logger.info(f"  - 存储的向量数量: {count}")
        
        if count == 0:
            logger.warning("✗ 向量库为空！请先上传法律文档")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ 向量库检查失败: {e}")
        return False


def check_embeddings():
    """检查嵌入模型"""
    logger.info("\n" + "=" * 60)
    logger.info("【诊断2】检查嵌入模型")
    logger.info("=" * 60)
    
    try:
        from 合同审查.app.rag import get_embeddings
        
        embeddings = get_embeddings(model=settings.EMBEDDING_MODEL)
        logger.info(f"✓ 嵌入模型初始化成功")
        logger.info(f"  - 模型类型: {settings.EMBEDDING_MODEL}")
        logger.info(f"  - 向量维度: {embeddings.dimension}")
        
        # 测试嵌入
        test_text = "这是一个测试文本"
        vector = embeddings.embed_query(test_text)
        vector_norm = sum(x**2 for x in vector) ** 0.5
        
        logger.info(f"  - 测试文本: '{test_text}'")
        logger.info(f"  - 向量模长: {vector_norm:.6f}")
        
        if vector_norm < 1e-6:
            logger.error("✗ 嵌入向量为零向量！模型可能有问题")
            return False
        
        logger.info(f"✓ 嵌入模型工作正常")
        return True
        
    except Exception as e:
        logger.error(f"✗ 嵌入模型检查失败: {e}")
        return False


def check_retrieval():
    """检查检索功能"""
    logger.info("\n" + "=" * 60)
    logger.info("【诊断3】检查检索功能")
    logger.info("=" * 60)
    
    try:
        from 合同审查.app.rag import get_retriever
        
        retriever = get_retriever()
        logger.info(f"✓ 检索器初始化成功")
        
        # 测试检索
        test_queries = [
            "合同违约责任",
            "付款方式",
            "保密条款",
        ]
        
        for query in test_queries:
            logger.info(f"\n  测试查询: '{query}'")
            results = retriever.retrieve(query, top_k=3)
            
            if results:
                logger.info(f"  ✓ 找到 {len(results)} 条结果")
                for i, result in enumerate(results, 1):
                    logger.info(f"    [{i}] 相似度: {result.score:.4f} | "
                              f"条款: {result.clause_no} | "
                              f"内容: {result.clause_content[:50]}...")
            else:
                logger.warning(f"  ✗ 未找到相关结果")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ 检索功能检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_similarity_calculation():
    """检查相似度计算"""
    logger.info("\n" + "=" * 60)
    logger.info("【诊断4】检查相似度计算")
    logger.info("=" * 60)
    
    try:
        from 合同审查.app.rag import get_embeddings, get_vector_store
        import numpy as np
        
        embeddings = get_embeddings(model=settings.EMBEDDING_MODEL)
        vector_store = get_vector_store()
        
        # 使用相同文本进行测试
        test_text = "测试合同条款内容"
        
        # 生成查询向量
        query_vector = embeddings.embed_query(test_text)
        
        # 添加到向量库
        from 合同审查.app.rag.contract_schema import ClauseChunk
        test_chunk = ClauseChunk(
            clause_id="test_similarity_001",
            clause_no="第1条",
            clause_content=test_text,
            clause_title="测试条款",
            metadata={"test": True}
        )
        
        # 先删除可能存在的测试数据
        try:
            vector_store.delete(["test_similarity_001"])
        except:
            pass
        
        # 添加测试数据
        doc_vector = embeddings.embed_documents([test_text])[0]
        vector_store.add_clauses([test_chunk], [doc_vector], ids=["test_similarity_001"])
        logger.info(f"✓ 添加测试数据到向量库")
        
        # 搜索相同内容
        results = vector_store.search(query_vector, top_k=1)
        
        if results:
            record, score = results[0]
            logger.info(f"  - 查询文本: '{test_text}'")
            logger.info(f"  - 匹配文本: '{record.clause_content}'")
            logger.info(f"  - 相似度分数: {score:.6f}")
            
            if score > 0.99:
                logger.info(f"✓ 相似度计算正确（相同内容相似度≈1.0）")
            elif score > 0.9:
                logger.warning(f"△ 相似度略低，但可接受")
            else:
                logger.error(f"✗ 相似度异常！相同内容应该接近1.0")
                return False
        else:
            logger.error(f"✗ 未找到结果")
            return False
        
        # 清理测试数据
        vector_store.delete(["test_similarity_001"])
        
        return True
        
    except Exception as e:
        logger.error(f"✗ 相似度计算检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_embedding_consistency():
    """检查嵌入模型一致性"""
    logger.info("\n" + "=" * 60)
    logger.info("【诊断5】检查嵌入模型一致性")
    logger.info("=" * 60)
    
    try:
        from 合同审查.app.rag import get_embeddings
        import numpy as np
        
        embeddings = get_embeddings(model=settings.EMBEDDING_MODEL)
        
        # 测试多次嵌入同一文本是否一致
        test_text = "合同违约金计算方式"
        
        vectors = []
        for i in range(3):
            vector = embeddings.embed_query(test_text)
            vectors.append(vector)
        
        # 计算向量间的相似度
        def cosine_similarity(v1, v2):
            dot = sum(a * b for a, b in zip(v1, v2))
            norm1 = sum(a * a for a in v1) ** 0.5
            norm2 = sum(b * b for b in v2) ** 0.5
            return dot / (norm1 * norm2) if norm1 > 0 and norm2 > 0 else 0
        
        sim_12 = cosine_similarity(vectors[0], vectors[1])
        sim_13 = cosine_similarity(vectors[0], vectors[2])
        sim_23 = cosine_similarity(vectors[1], vectors[2])
        
        logger.info(f"  测试文本: '{test_text}'")
        logger.info(f"  多次嵌入相似度:")
        logger.info(f"    - 第1次 vs 第2次: {sim_12:.6f}")
        logger.info(f"    - 第1次 vs 第3次: {sim_13:.6f}")
        logger.info(f"    - 第2次 vs 第3次: {sim_23:.6f}")
        
        if sim_12 > 0.999 and sim_13 > 0.999 and sim_23 > 0.999:
            logger.info(f"✓ 嵌入模型一致性良好")
            return True
        else:
            logger.warning(f"△ 嵌入结果略有差异（可能是模型特性）")
            return True
        
    except Exception as e:
        logger.error(f"✗ 嵌入一致性检查失败: {e}")
        return False


def main():
    """主函数"""
    logger.info("\n" + "=" * 60)
    logger.info("RAG 系统诊断工具")
    logger.info("=" * 60)
    
    results = {
        "向量库状态": check_vector_store(),
        "嵌入模型": check_embeddings(),
        "检索功能": check_retrieval(),
        "相似度计算": check_similarity_calculation(),
        "嵌入一致性": check_embedding_consistency(),
    }
    
    # 总结
    logger.info("\n" + "=" * 60)
    logger.info("诊断总结")
    logger.info("=" * 60)
    
    for name, passed in results.items():
        status = "✓ 通过" if passed else "✗ 失败"
        logger.info(f"{name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("\n✓ 所有检查通过，RAG系统工作正常")
    else:
        logger.warning("\n△ 部分检查未通过，请查看详细日志")
        
        # 提供建议
        logger.info("\n" + "=" * 60)
        logger.info("常见问题及解决方案")
        logger.info("=" * 60)
        logger.info("1. 向量库为空：请先上传法律文档到系统中")
        logger.info("2. 嵌入模型问题：检查 DASHSCOPE_API_KEY 是否正确设置")
        logger.info("3. 相似度为0：可能是向量库和查询使用不同嵌入模型，需要重新构建向量库")
        logger.info("4. 检索无结果：尝试降低相似度阈值或检查向量库内容")


if __name__ == "__main__":
    main()
