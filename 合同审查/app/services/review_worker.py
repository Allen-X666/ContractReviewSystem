"""
审查工作器 - 异步执行审查任务
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from 合同审查.app.schemas.enums import ReviewStatus, ReviewStage, RiskType, RiskLevel
from 合同审查.app.schemas.models import RelatedLaw
from 合同审查.app.rag import document_loader, text_splitter
from 合同审查.app.rag.retriever import get_law_retriever
from 合同审查.app.llm import (
    RiskAnalysisChain,
    ComplianceCheckChain,
    CompleteReviewChain,
    LLMFactory
)
from 合同审查.app.utils.enum_mapping import convert_risk_item, convert_risk_items

logger = logging.getLogger(__name__)


@dataclass
class ReviewContext:
    """审查上下文"""
    review_id: int
    task_service: Any  # ReviewTaskService
    cancel_check_interval: float = 1.0


class ReviewWorker:
    """审查工作器 - 在后台执行实际的审查任务"""

    def __init__(self, task_service):
        self._task_service = task_service
        self._running_tasks: Dict[int, asyncio.Task] = {}
        # 初始化LLM链
        self._risk_chain = None
        self._compliance_chain = None
        self._review_chain = None
        # 初始化检索器
        self._retriever = None
        # 风险计数器（用于生成id）
        self._risk_counter = 0

    async def _init_llm_chains_async(self):
        """初始化LLM链（异步版本，避免阻塞事件循环）"""
        if self._risk_chain is None:
            import asyncio
            loop = asyncio.get_event_loop()

            def sync_init():
                llm = LLMFactory.create_review_llm()
                risk_chain = RiskAnalysisChain(llm=llm)
                compliance_chain = ComplianceCheckChain(llm=llm)
                review_chain = CompleteReviewChain(
                    risk_chain=risk_chain,
                    compliance_chain=compliance_chain,
                )
                return risk_chain, compliance_chain, review_chain

            self._risk_chain, self._compliance_chain, self._review_chain = await loop.run_in_executor(None, sync_init)
            logger.info("LLM链和智能分析器初始化完成")

    async def _init_retriever_async(self):
        """初始化法律文档检索器（异步版本，避免阻塞事件循环）"""
        if self._retriever is None:
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                # 在线程池中执行同步的检索器初始化，使用法律文档检索器
                self._retriever = await loop.run_in_executor(None, get_law_retriever)
                logger.info("法律文档检索器初始化完成")
            except Exception as e:
                logger.warning(f"法律文档检索器初始化失败: {e}，将使用空检索结果")
                self._retriever = None

    def _retrieve_related_laws(self, query: str, top_k: int = 3) -> List[RelatedLaw]:
        """
        检索关联法条（同步版本）

        Args:
            query: 查询文本（条款内容或风险描述）
            top_k: 返回结果数量

        Returns:
            List[RelatedLaw]: 关联法条列表
        """
        if self._retriever is None:
            logger.debug("检索器未初始化，跳过RAG检索")
            return []

        try:
            logger.info(f"【RAG检索】查询: '{query[:100]}...' | top_k={top_k}")
            retrieved_clauses = self._retriever.retrieve(query=query, top_k=top_k)

            related_laws = []
            for clause in retrieved_clauses:
                # 从检索结果构建RelatedLaw对象
                related_law = RelatedLaw(
                    law_id=0,  # 向量库中的记录可能没有law_id，使用默认值
                    law_name=clause.metadata.get("law_name", "未知法规") if clause.metadata else "未知法规",
                    article_no=clause.clause_no or "相关条款",
                    content=clause.clause_content or ""
                )
                related_laws.append(related_law)
                logger.info(f"【RAG检索】结果: {related_law.law_name} - {related_law.article_no}")

            logger.info(f"【RAG检索】共找到 {len(related_laws)} 条关联法条")
            return related_laws

        except Exception as e:
            logger.error(f"【RAG检索】检索失败: {e}")
            return []

    async def _retrieve_related_laws_async(self, query: str, top_k: int = 3) -> List[RelatedLaw]:
        """
        检索关联法条（异步版本，使用线程池避免阻塞事件循环）

        Args:
            query: 查询文本（条款内容或风险描述）
            top_k: 返回结果数量

        Returns:
            List[RelatedLaw]: 关联法条列表
        """
        loop = asyncio.get_event_loop()
        # 使用线程池执行同步的RAG检索，避免阻塞事件循环
        return await loop.run_in_executor(None, self._retrieve_related_laws, query, top_k)

    async def start_review(
            self,
            review_id: int,
            contract_id: int,
            file_content: bytes,
            file_name: str,
            file_type: str,
            review_options: Dict[str, Any]
    ) -> None:
        """
        启动异步审查任务

        Args:
            review_id: 审查任务ID
            contract_id: 合同ID
            file_content: 文件内容（字节）
            file_name: 文件名
            file_type: 文件类型
            review_options: 审查选项
        """
        context = ReviewContext(
            review_id=review_id,
            task_service=self._task_service
        )

        # 创建异步任务
        task = asyncio.create_task(
            self._execute_review(
                context,
                contract_id,
                file_content,
                file_name,
                file_type,
                review_options
            )
        )
        self._running_tasks[review_id] = task

        # 添加完成回调清理
        task.add_done_callback(
            lambda t: self._cleanup_task(review_id, t)
        )

    def _cleanup_task(self, review_id: int, task: asyncio.Task) -> None:
        """清理完成的任务"""
        self._running_tasks.pop(review_id, None)

        # 检查任务是否异常
        try:
            task.result()
        except asyncio.CancelledError:
            logger.info(f"审查任务 {review_id} 被取消")
        except Exception as e:
            logger.error(f"审查任务 {review_id} 异常: {e}")

    async def _execute_review(
            self,
            context: ReviewContext,
            contract_id: int,
            file_content: bytes,
            file_name: str,
            file_type: str,
            review_options: Dict[str, Any]
    ) -> None:
        """执行审查流程"""
        review_id = context.review_id

        try:
            # 更新状态为处理中
            self._task_service.update_task_status(
                review_id,
                status=ReviewStatus.PROCESSING,
                stage=ReviewStage.PARSING,
                progress=5,
                message="正在加载文档..."
            )

            # 1. 文档加载阶段 (5-25%)
            clauses_list = await self._load_document(context, file_content, file_name, file_type)
            total_clauses = sum(len(clauses) for clauses in clauses_list)
            if total_clauses == 0:
                raise ValueError("未能从文档中提取到任何条款")

            self._task_service.update_task(
                review_id,
                {
                    "total_clauses": total_clauses,
                    "started_at": datetime.now()
                }
            )

            self._task_service.update_task_status(
                review_id,
                stage=ReviewStage.PARSING,
                progress=25,
                message=f"文档解析完成，共 {total_clauses} 个条款"
            )

            # 2. 法律文档检索器初始化阶段 (25-40%)
            self._task_service.update_task_status(
                review_id,
                stage=ReviewStage.RETRIEVING,
                progress=25,
                message="正在连接法律文档知识库..."
            )
            await self._init_retriever_async()

            self._task_service.update_task_status(
                review_id,
                stage=ReviewStage.RETRIEVING,
                progress=40,
                message="法律文档知识库连接完成"
            )

            # 3. AI分析阶段 (40-90%)
            logger.info(f"开始分析条款，共 {sum(len(clauses) for clauses in clauses_list)} 个条款")
            self._task_service.update_task_status(
                review_id,
                stage=ReviewStage.ANALYZING,
                progress=40,
                message="正在初始化分析引擎..."
            )
            risk_items = await self._analyze_clauses(
                context, clauses_list, review_options
            )

            # 4. 结果生成阶段 (90-100%)
            self._task_service.update_task_status(
                review_id,
                stage=ReviewStage.GENERATING,
                progress=90,
                message="正在生成审查报告..."
            )

            # 完成审查
            self._task_service.complete_task(review_id, risk_items)
            logger.info(f"审查任务 {review_id} 完成，发现 {len(risk_items)} 个风险")

        except asyncio.CancelledError:
            logger.info(f"审查任务 {review_id} 被取消")
            self._task_service.cancel_task(review_id)
            raise
        except Exception as e:
            logger.error(f"审查任务 {review_id} 失败: {e}", exc_info=True)
            self._task_service.fail_task(review_id, str(e))

    async def _load_document(
            self,
            context: ReviewContext,
            file_content: bytes,
            file_name: str,
            file_type: str
    ) -> List[List[Any]]:
        """加载并拆分文档"""
        review_id = context.review_id

        # 在线程池中执行同步的文档加载
        loop = asyncio.get_event_loop()

        try:
            # 使用 BytesIO 包装字节内容
            from io import BytesIO
            file_obj = BytesIO(file_content)

            loader = document_loader.DocumentLoader()
            document = await loop.run_in_executor(
                None, lambda: loader.load(file_obj=file_obj, file_name=file_name)
            )

            if not document:
                return []

            clauses_list = []
            for i, chunk in enumerate(document):
                # 检查取消请求
                if await self._is_cancelled(context):
                    raise asyncio.CancelledError()

                # 更新进度
                progress = 5 + int((i + 1) / len(document) * 20)
                self._task_service.update_task_status(
                    review_id,
                    progress=progress,
                    message=f"正在解析文档 ({i + 1}/{len(document)})..."
                )

                # 【修复】使用智能拆分函数，替代原来的两步处理
                # 智能拆分会自动处理子条款合并、重复内容过滤等问题
                clauses = await loop.run_in_executor(
                    None, text_splitter.split_contract_intelligently, chunk.clause_content
                )

                clauses_list.append(clauses)

            return clauses_list

        except Exception as e:
            logger.error(f"文档加载失败: {e}")
            raise

    async def _analyze_clauses(
            self,
            context: ReviewContext,
            clauses_list: List[List[Any]],
            review_options: Dict[str, Any]
    ) -> List[Dict]:
        """分析条款（调用LLM）"""
        review_id = context.review_id

        logger.info("开始初始化LLM链...")
        # 初始化LLM链（异步版本，避免阻塞事件循环）
        await self._init_llm_chains_async()
        logger.info("LLM链初始化完成")

        # 准备条款数据
        all_clauses = []
        for clauses in clauses_list:
            for clause in clauses:
                clause_data = self._extract_clause_data(clause)
                if clause_data:
                    all_clauses.append(clause_data)

        total_clauses = len(all_clauses)
        logger.info(f"准备分析 {total_clauses} 个条款")
        if total_clauses == 0:
            logger.warning("没有可分析的条款")
            return []

        # 检查需要执行的审查类型
        # 注意：只启用风险分析，关闭合规检查以避免重复
        # 风险分析已经包含合规检查的内容（法律风险维度）
        check_legal_risk = review_options.get("check_legal_risk", True)
        check_invalid_clause = False  # 关闭合规检查，避免与风险分析重复
        logger.info(f"审查选项: legal_risk={check_legal_risk}, invalid_clause={check_invalid_clause} (合规检查已关闭以避免重复)")

        risk_items = []
        # 批量分析条款 - 使用并发提高速度
        batch_size = 2  # 减小批次大小，避免超时
        semaphore = asyncio.Semaphore(1)  # 限制并发数为1，串行处理避免限流

        # 重置风险计数器
        self._risk_counter = 0

        def format_legal_basis(related_laws: List[RelatedLaw]) -> str:
            """将RelatedLaw列表格式化为法律依据字符串"""
            if not related_laws:
                return "《中华人民共和国民法典》合同编及相关司法解释"
            
            formatted = []
            for i, law in enumerate(related_laws, 1):
                law_text = f"{i}. {law.law_name} - {law.article_no}\n   {law.content}"
                formatted.append(law_text)
            
            return "\n\n".join(formatted)
        
        async def analyze_batch(batch_idx: int, batch: List[Dict]) -> List[Dict]:
            """分析单个批次"""
            logger.info(f"开始分析批次 {batch_idx}, 包含 {len(batch)} 个条款")
            async with semaphore:
                batch_risk_items = []
                
                # 【关键优化】先为每个条款进行RAG检索，获取相关法律依据
                logger.info(f"批次 {batch_idx}: 先进行RAG检索获取法律依据...")
                enriched_batch = []
                for clause in batch:
                    # 使用条款内容进行RAG检索
                    query = clause.get("clause_content", "")
                    clause_no = clause.get("clause_no", "未知")
                    logger.info(f"【RAG检索-预处理】条款[{clause_no}] 查询内容: '{query[:100]}...'")
                    
                    related_laws = await self._retrieve_related_laws_async(query, top_k=3)
                    
                    # 记录检索结果
                    if related_laws:
                        logger.info(f"【RAG检索-预处理】条款[{clause_no}] 检索到 {len(related_laws)} 条关联法条:")
                        for i, law in enumerate(related_laws, 1):
                            logger.info(f"  [{i}] {law.law_name} - {law.article_no}: {law.content[:80]}...")
                    else:
                        logger.info(f"【RAG检索-预处理】条款[{clause_no}] 未检索到关联法条")
                    
                    # 将法律依据格式化为字符串并添加到条款数据中
                    legal_basis = format_legal_basis(related_laws)
                    enriched_clause = {
                        **clause,
                        "legal_basis": legal_basis,
                        "related_laws": related_laws  # 保留原始数据供后续使用
                    }
                    enriched_batch.append(enriched_clause)
                
                logger.info(f"批次 {batch_idx}: RAG检索完成，开始调用LLM分析...")
                
                try:
                    # 1. 调用LLM进行深度风险分析（传入包含法律依据的条款）
                    if check_legal_risk:
                        logger.info(f"批次 {batch_idx}: 调用风险分析链...")
                        try:
                            batch_risks = await asyncio.wait_for(
                                self._risk_chain.analyze_risks(
                                    clauses=enriched_batch,
                                    contract_type="一般合同"
                                ),
                                timeout=150  # 150秒超时
                            )
                            logger.info(f"批次 {batch_idx}: 风险分析完成，返回 {len(batch_risks)} 个风险")

                            # 转换RiskItem为字典格式
                            for risk in batch_risks:
                                # 获取当前风险计数并递增
                                current_risk_index = self._risk_counter
                                self._risk_counter += 1

                                # 查找对应的条款信息以获取clause_id和related_laws
                                clause_id = ""
                                related_laws = []
                                for clause in enriched_batch:
                                    if clause.get("clause_no") == risk.clause_no:
                                        clause_id = clause.get("clause_id", "")
                                        related_laws = clause.get("related_laws", [])
                                        break

                                # 转换RiskItem为字典格式，传入所有必要参数
                                risk_item = self._convert_risk_to_dict(
                                    risk=risk,
                                    risk_index=current_risk_index,
                                    total_risks=self._risk_counter,
                                    clause_id=clause_id,
                                    related_laws=related_laws
                                )
                                risk_item["source"] = "llm_analysis"
                                batch_risk_items.append(risk_item)
                        except asyncio.TimeoutError:
                            logger.error(f"批次 {batch_idx}: 风险分析超时")

                    # 2. 调用LLM进行合规检查（传入包含法律依据的条款）
                    if check_invalid_clause:
                        logger.info(f"批次 {batch_idx}: 调用合规检查链...")
                        try:
                            batch_compliance = await asyncio.wait_for(
                                self._compliance_chain.check_compliance(
                                    clauses=enriched_batch,
                                    contract_type="一般合同"
                                ),
                                timeout=150  # 150秒超时
                            )
                            logger.info(f"批次 {batch_idx}: 合规检查完成，返回 {len(batch_compliance)} 个结果")

                            # 将不合规结果转换为风险项
                            non_compliant_count = 0
                            for compliance in batch_compliance:
                                if not compliance.is_compliant:
                                    # 获取当前风险计数并递增
                                    current_risk_index = self._risk_counter
                                    self._risk_counter += 1

                                    # 查找对应的条款信息以获取clause_id和related_laws
                                    clause_id = ""
                                    related_laws = []
                                    for clause in enriched_batch:
                                        if clause.get("clause_no") == compliance.clause_no:
                                            clause_id = clause.get("clause_id", "")
                                            related_laws = clause.get("related_laws", [])
                                            break

                                    # 记录检索结果
                                    if related_laws:
                                        logger.info(f"【RAG检索-合规检查】条款[{compliance.clause_no}] 使用已检索到的 {len(related_laws)} 条关联法条")
                                        for i, law in enumerate(related_laws, 1):
                                            logger.info(f"  [{i}] {law.law_name} - {law.article_no}: {law.content[:80]}...")
                                    else:
                                        logger.info(f"【RAG检索-合规检查】条款[{compliance.clause_no}] 未检索到关联法条，将使用默认法律依据")

                                    risk_item = self._convert_compliance_to_risk(
                                        compliance=compliance,
                                        risk_index=current_risk_index,
                                        total_risks=self._risk_counter,
                                        clause_id=clause_id,
                                        related_laws=related_laws
                                    )
                                    risk_item["source"] = "compliance_check"
                                    batch_risk_items.append(risk_item)
                                    non_compliant_count += 1
                            logger.info(f"批次 {batch_idx}: 发现 {non_compliant_count} 个不合规项")
                            logger.info(f"批次 {batch_idx}: {batch_risk_items}")
                        except asyncio.TimeoutError:
                            logger.error(f"批次 {batch_idx}: 合规检查超时")

                except Exception as e:
                    logger.error(f"LLM分析批次 {batch_idx} 失败: {e}", exc_info=True)
                    # 继续处理，不中断整个流程

                logger.info(f"批次 {batch_idx} 完成，返回 {len(batch_risk_items)} 个风险项")
                return batch_risk_items

        async def analyze_batch_with_progress(batch_idx: int, batch: List[Dict], start_idx: int) -> tuple:
            """分析单个批次并返回批次信息"""
            result = await analyze_batch(batch_idx, batch)
            return (start_idx, batch, result)

        # 创建所有批次的任务
        batch_tasks = []
        total_batches = (total_clauses + batch_size - 1) // batch_size
        logger.info(f"创建 {total_batches} 个批次任务，每批 {batch_size} 个条款")

        for i in range(0, total_clauses, batch_size):
            batch = all_clauses[i:i + batch_size]
            batch_idx = i // batch_size
            logger.debug(f"创建批次 {batch_idx} 任务，包含条款 {i}-{min(i+batch_size, total_clauses)-1}")
            task = asyncio.create_task(analyze_batch_with_progress(batch_idx, batch, i))
            batch_tasks.append((i, batch, task))

        logger.info(f"开始并发执行 {len(batch_tasks)} 个批次任务")

        # 并发执行所有批次，并实时更新进度
        completed = 0
        batch_count = 0
        for coro in asyncio.as_completed([task for _, _, task in batch_tasks]):
            batch_count += 1
            logger.info(f"等待批次 {batch_count}/{total_batches} 完成...")

            # 检查取消请求
            if await self._is_cancelled(context):
                raise asyncio.CancelledError()

            # 等待当前批次完成
            try:
                start_idx, batch, batch_results = await coro
                logger.info(f"批次完成: 起始索引 {start_idx}, 返回 {len(batch_results)} 个风险项")
                risk_items.extend(batch_results)
            except Exception as e:
                logger.error(f"批次处理失败: {e}", exc_info=True)
                continue

            # 更新进度 - 逐个条款更新，避免跳跃
            for j, clause in enumerate(batch):
                completed += 1
                progress = 40 + int((completed / total_clauses) * 50)

                self._task_service.update_task_status(
                    review_id,
                    stage=ReviewStage.ANALYZING,
                    progress=progress,
                    message=f"正在分析条款 {clause.get('clause_no', f'第{completed}条')} ({completed}/{total_clauses})...",
                    processed_clauses=completed
                )

                # 小延迟让进度更新更平滑
                await asyncio.sleep(0.01)

        # 对风险项进行去重
        unique_risk_items = self._deduplicate_risks(risk_items)
        logger.info(f"条款分析完成，共发现 {len(risk_items)} 个风险项，去重后 {len(unique_risk_items)} 个")
        return unique_risk_items
    
    def _deduplicate_risks(self, risk_items: List[Dict]) -> List[Dict]:
        """
        对风险项进行去重
        
        基于条款编号和风险描述的相似度进行去重
        """
        if not risk_items:
            return risk_items
        
        unique_items = []
        seen_signatures = set()
        
        for risk in risk_items:
            # 生成风险签名：条款编号 + 风险描述的前50个字符
            clause_no = risk.get("clause", "")
            description = risk.get("description", "")
            # 使用描述的前50个字符作为签名的一部分
            desc_prefix = description[:50] if description else ""
            signature = f"{clause_no}:{desc_prefix}"
            
            # 检查是否已经存在相似的风险
            is_duplicate = False
            for existing_sig in seen_signatures:
                existing_clause, existing_desc = existing_sig.split(":", 1)
                if existing_clause == clause_no:
                    # 如果条款相同，检查描述相似度
                    similarity = self._calculate_similarity(desc_prefix, existing_desc)
                    if similarity > 0.7:  # 相似度超过70%认为是重复
                        is_duplicate = True
                        logger.info(f"发现重复风险项: {clause_no}, 相似度: {similarity:.2f}")
                        break
            
            if not is_duplicate:
                seen_signatures.add(signature)
                unique_items.append(risk)
        
        return unique_items
    
    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """
        计算两个字符串的相似度（使用简单的Jaccard相似度）
        """
        if not str1 or not str2:
            return 0.0
        
        # 将字符串转换为字符集合
        set1 = set(str1)
        set2 = set(str2)
        
        # 计算Jaccard相似度
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0

    def _extract_clause_data(self, clause: Any) -> Optional[Dict[str, str]]:
        """从条款对象中提取数据"""
        if hasattr(clause, 'clause_no') and hasattr(clause, 'clause_content'):
            return {
                "clause_no": clause.clause_no,
                "clause_content": clause.clause_content,
                "clause_id": getattr(clause, 'clause_id', ""),
            }
        elif isinstance(clause, dict):
            return {
                "clause_no": clause.get("clause_no", "未知条款"),
                "clause_content": clause.get("clause_content", ""),
                "clause_id": clause.get("clause_id", ""),
            }
        elif isinstance(clause, str):
            return {
                "clause_no": "未知条款",
                "clause_content": clause,
                "clause_id": "",
            }
        return None

    def _convert_risk_to_dict(
        self,
        risk,
        risk_index: int = 0,
        total_risks: int = 0,
        clause_id: str = "",
        related_laws: List[RelatedLaw] = None
    ) -> Dict[str, Any]:
        """
        将RiskItem转换为字典

        Args:
            risk: RiskItem对象
            risk_index: 当前风险项索引（用于生成id）
            total_risks: 风险总数
            clause_id: 条款ID（用于paragraph_index）
            related_laws: RAG检索到的关联法条列表
        """
        # 处理 suggestion：将列表转换为字符串，如果没有则使用 risk_description 或默认文本
        if hasattr(risk, 'suggestions') and risk.suggestions:
            if isinstance(risk.suggestions, list):
                suggestion = "；".join(risk.suggestions) if risk.suggestions else ""
            else:
                suggestion = str(risk.suggestions)
        else:
            suggestion = f"建议修改该条款以避免潜在风险。{risk.risk_description[:100]}..." if risk.risk_description else "建议审查该条款"

        # 处理 related_laws：只保留content字段，但格式仍为RelatedLaw对象列表
        if not related_laws:
            if hasattr(risk, 'legal_basis') and risk.legal_basis:
                # 使用AI给出的法律依据作为通用条款
                related_laws_list = [{
                    "law_id": 0,
                    "law_name": "",
                    "article_no": "",
                    "content": f"知识库不存在相关条款，通用条款如下：{risk.legal_basis}"
                }]
            else:
                related_laws_list = [{
                    "law_id": 0,
                    "law_name": "",
                    "article_no": "",
                    "content": "知识库不存在相关条款，通用条款如下：建议参考相关法律法规进行审查"
                }]
        else:
            related_laws_list = [
                {
                    "law_id": 0,
                    "law_name": "",
                    "article_no": "",
                    "content": law.content if hasattr(law, 'content') else law.get("content", "")
                }
                for law in related_laws
            ]

        result = {
            "id": risk_index + 1,  # id 根据风险总数自增长，从1开始
            "clause_title": risk.clause_no if risk.clause_no else "未知条款",  # clause_title 为对应的 clause_no
            "clause_no": risk.clause_no,
            "clause_content": risk.clause_content[:500] if risk.clause_content else "",  # 限制长度
            "risk_type": risk.risk_type if risk.risk_type else RiskType.LEGAL_RISK,
            "risk_level": risk.risk_level.value if hasattr(risk.risk_level, 'value') else str(risk.risk_level).lower(),
            "risk_description": risk.risk_description if risk.risk_description else "",
            "suggestion": suggestion,  # suggestion 处理
            "related_laws": related_laws_list,  # related_laws 只保留content
            "paragraph_index": clause_id if clause_id else 0,  # paragraph_index 为对应的 clause_id
            "legal_basis": risk.legal_basis if hasattr(risk, 'legal_basis') else None,
            "suggestions": risk.suggestions if hasattr(risk, 'suggestions') else [],
            "score": risk.score if hasattr(risk, 'score') else None,
        }
        # 转换中文枚举值为英文枚举值
        return convert_risk_item(result)

    def _convert_compliance_to_risk(
        self,
        compliance,
        risk_index: int = 0,
        total_risks: int = 0,
        clause_id: str = "",
        related_laws: List[RelatedLaw] = None
    ) -> Dict[str, Any]:
        """
        将ComplianceResult转换为风险项字典

        Args:
            compliance: ComplianceResult对象
            risk_index: 当前风险项索引（用于生成id）
            total_risks: 风险总数
            clause_id: 条款ID（用于paragraph_index）
            related_laws: RAG检索到的关联法条列表
        """
        # 处理 suggestion：将列表转换为字符串
        if hasattr(compliance, 'recommendations') and compliance.recommendations:
            if isinstance(compliance.recommendations, list):
                suggestion = "；".join(compliance.recommendations) if compliance.recommendations else ""
            else:
                suggestion = str(compliance.recommendations)
        else:
            suggestion = "建议修改该条款以符合相关法律法规要求"

        # 处理 related_laws：只保留content字段，但格式仍为RelatedLaw对象列表
        if not related_laws:
            if hasattr(compliance, 'violated_laws') and compliance.violated_laws:
                # 使用AI给出的法律依据作为通用条款
                violated_laws_str = ", ".join(compliance.violated_laws) if isinstance(compliance.violated_laws, list) else str(compliance.violated_laws)
                related_laws_list = [{
                    "law_id": 0,
                    "law_name": "",
                    "article_no": "",
                    "content": f"知识库不存在相关条款，通用条款如下：{violated_laws_str}"
                }]
            else:
                related_laws_list = [{
                    "law_id": 0,
                    "law_name": "",
                    "article_no": "",
                    "content": "知识库不存在相关条款，通用条款如下：建议参考相关法律法规进行审查"
                }]
        else:
            related_laws_list = [
                {
                    "law_id": 0,
                    "law_name": "",
                    "article_no": "",
                    "content": law.content if hasattr(law, 'content') else law.get("content", "")
                }
                for law in related_laws
            ]

        # 构建legal_basis字符串
        legal_basis = None
        if hasattr(compliance, 'violated_laws') and compliance.violated_laws:
            legal_basis = ", ".join(compliance.violated_laws) if isinstance(compliance.violated_laws, list) else str(compliance.violated_laws)

        result = {
            "id": risk_index + 1,  # id 根据风险总数自增长，从1开始
            "clause_title": compliance.clause_no if compliance.clause_no else "未知条款",  # clause_title 为对应的 clause_no
            "clause_no": compliance.clause_no,
            "clause_content": compliance.clause_content if compliance.clause_content else "",
            "risk_type": RiskType.LEGAL_RISK,  # 合规风险归类为法律风险
            "risk_level": RiskLevel.HIGH if compliance.violated_laws else RiskLevel.MEDIUM,
            "risk_description": compliance.violation_details or "该条款可能存在合规问题",
            "suggestion": suggestion,  # suggestion 处理
            "related_laws": related_laws_list,  # related_laws 只保留content
            "paragraph_index": clause_id if clause_id else 0,  # paragraph_index 为对应的 clause_id
            "legal_basis": legal_basis,
            "suggestions": compliance.recommendations if hasattr(compliance, 'recommendations') else [],
            "score": compliance.score if hasattr(compliance, 'score') else None,
        }
        # 转换中文枚举值为英文枚举值
        return convert_risk_item(result)

    async def _is_cancelled(self, context: ReviewContext) -> bool:
        """检查是否请求取消"""
        return self._task_service.is_cancel_requested(context.review_id)

    async def cancel_review(self, review_id: int) -> bool:
        """取消审查任务"""
        # 1. 标记取消请求
        self._task_service.request_cancel(review_id)

        # 2. 如果任务正在运行，取消它
        if review_id in self._running_tasks:
            task = self._running_tasks[review_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            return True

        # 3. 如果任务还未开始，直接标记为取消
        task_info = self._task_service.get_task(review_id)
        if task_info and task_info.status == ReviewStatus.PENDING:
            self._task_service.cancel_task(review_id)
            return True

        return False
