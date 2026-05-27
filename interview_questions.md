# 合同审查Agent项目 - 技术面试题库

> 本文档基于对项目代码库的深入分析，涵盖RAG检索、LangChain/LangGraph、向量数据库、LLM集成、存储架构、系统设计等核心模块。
> 难度标记：⭐ 基础 | ⭐⭐ 进阶 | ⭐⭐⭐ 高级 | ⭐⭐⭐⭐ 开放性/设计题

---

## 一、RAG 检索增强生成（重点考察）

### 1.1 混合检索与权重分配

**Q1.1** ⭐⭐ 项目中采用了混合检索策略，请说明向量检索和关键词检索的权重是如何分配的？为什么选择这个比例？

> 参考要点：向量检索权重0.7，关键词检索权重0.3；向量检索捕获语义相似性，关键词检索确保关键术语不遗漏；权重可在配置文件中动态调整。

**Q1.2** ⭐⭐⭐ 混合检索的融合公式是什么？请详细说明融合过程，并解释为什么使用加权求和而非RRF（Reciprocal Rank Fusion）？

> 参考要点：`final_score = 0.7 × vector_score + 0.3 × keyword_score`；对向量召回结果计算Jaccard关键词分数后累加排序；RRF更关注排名而非绝对分数，当前方案更直观可调。

**Q1.3** ⭐⭐ 项目中关键词检索使用的是什么算法？请分析其优缺点及适用场景。

> 参考要点：Jaccard相似度（交集/并集）；优点是实现简单、无需额外模型；缺点是不考虑词序和语义，对中文分词依赖较大。

**Q1.4** ⭐⭐⭐ 当前系统是否存在Query改写机制？如果没有，你会如何设计一个？请给出至少两种方案并分析其优劣。

> 参考要点：当前无Query改写。可选方案：①同义词扩展（法律术语词典）②HyDE（让LLM生成假设文档再做Embedding）③LLM直接改写查询。

### 1.2 召回与重排

**Q1.5** ⭐⭐ 项目中是如何实现扩大召回的？`HYBRID_RECALL_TOP_K`的作用是什么？

> 参考要点：混合检索时先召回`HYBRID_RECALL_TOP_K=10`条结果（比用户请求的top_k多），经过融合重排后返回最终top_k条；确保混合融合有足够候选集。

**Q1.6** ⭐⭐⭐ 项目中是否使用了专门的Rerank模型（如Cross-Encoder）？如果没有，当前的"重排"是如何实现的？你认为引入专用Rerank模型的收益和成本分别是什么？

> 参考要点：当前未使用专用Rerank模型，而是通过混合融合分数重排；引入Cross-Encoder可提升精度但增加延迟和计算成本；需权衡业务场景的精度-时延需求。

**Q1.7** ⭐⭐ 相似度阈值是如何设置的？当检索结果低于阈值时如何处理？

> 参考要点：项目在`config.py`中配置了分层阈值策略——法律文档检索阈值`LAW_DOCUMENT_SCORE_THRESHOLD=0.5`（高精度场景）、系统操作文档阈值`SYSTEM_DOCUMENT_SCORE_THRESHOLD=0.4`（相对宽松）、ChatBot知识检索阈值`CHATBOT_KNOWLEDGE_THRESHOLD=0.3`（保证用户体验）；`VectorRetriever.retrieve`方法默认使用配置阈值（`score_threshold=None`时取配置值）；低于阈值的结果在检索结果转换阶段被过滤，并记录debug日志；阈值选择依据BGE-small-zh-v1.5模型的相似度分布特征。

### 1.3 向量数据库存储

**Q1.8** ⭐⭐ 项目中法律文档和系统操作文档是如何进行分离存储的？这种设计的优缺点是什么？

> 参考要点：物理隔离（不同目录`law_documents/`和`system_operations/`），逻辑统一（共用ChromaVectorStore抽象）；优点是数据安全隔离、互不影响；缺点是跨库检索需要额外处理。

**Q1.9** ⭐⭐⭐ 项目支持Chroma和FAISS两种向量数据库，请对比二者的差异。在什么场景下你会选择FAISS而不是Chroma？

> 参考要点：Chroma支持持久化、元数据过滤、集合管理，适合中小规模；FAISS基于倒排索引/HNSW，适合大规模高性能场景；当数据量超过百万级或需要GPU加速时考虑FAISS。

**Q1.10** ⭐⭐ 请说明项目中向量检索的缓存机制是如何设计的？缓存Key是如何生成的？缓存策略（TTL、淘汰）是什么？

> 参考要点：`SimpleTTLCache`实现TTL+LRU；Key基于`query.strip().lower():top_k`的MD5哈希；默认TTL=3600s，maxsize=1000；存在过滤条件时跳过缓存。

---

## 二、LangChain / LangGraph Agent

**Q2.1** ⭐⭐ 项目中Agent是如何构建的？请说明`create_agent`函数的核心参数及其作用。

> 参考要点：使用LangGraph的`create_agent`，传入model（LLM）、tools（工具列表）、system_prompt、checkpointer（Redis）；checkpointer用于持久化对话状态。

**Q2.2** ⭐⭐⭐ 项目中使用了Redis Checkpointer来持久化Agent的对话状态，请说明checkpoint的存储格式、Key命名规则、以及如何实现消息截断？

> 参考要点：Key格式`{prefix}:{thread_id}:{ns}:{checkpoint_id}`；使用pickle序列化存储；保存时调用`trim_messages_by_checkpoint`进行滑动窗口截断；使用Sorted Set维护checkpoint索引。

**Q2.3** ⭐⭐ Agent中注册了哪些工具？请列举并说明其用途。工具调用时如何传递认证信息？

> 参考要点：共12个工具，包括search_contract_knowledge、review_contract、check_contract_exists、get_law_reference等；通过`RequestContext`和全局token机制在LangGraph独立线程中传递认证信息。

**Q2.4** ⭐⭐⭐ 当用户发送消息时，Agent是如何获取历史对话上下文的？为什么只传递当前消息而不是整个历史？

> 参考要点：LangGraph Agent使用`add_messages` reducer，从checkpointer自动恢复历史消息并追加新消息；避免重复传递历史，减少网络开销，由框架自动管理状态合并。

**Q2.5** ⭐⭐⭐⭐ 如果要给Agent增加一个新的工具（如"查询案例库"），需要做哪些改动？请从后端到前端完整描述。

> 参考要点：①在`tools.py`中定义@tool装饰器函数 ②在`chat_bot.py`的tools列表中注册 ③在system_prompt中添加工具使用说明 ④如有新的检索需求，需创建对应的向量存储和检索器 ⑤前端可能需要适配新的返回格式。

---

## 三、LLM 集成与结构化输出

**Q3.1** ⭐⭐ 项目中使用了哪种LLM？请说明LLM调用的降级策略是如何设计的。

> 参考要点：主要使用通义千问qwen3.6-flash（通过DashScope API）；`LLMFallbackManager`按优先级尝试备用模型（qwen3.6-plus → qwen3.6-35b-a3b → qwen3.5-35b-a3b）；实现了熔断器机制，连续失败后自动跳过主模型。

**Q3.2** ⭐⭐⭐ 项目中使用了`with_structured_output`实现结构化输出，请说明其实现原理。如果LLM输出的JSON格式不符合预期，系统如何处理？

> 参考要点：通过Pydantic模型定义输出Schema，LLM输出经JSON解析后用Pydantic校验；解析失败时尝试`_fix_json`修复常见格式问题；仍失败则调用`_create_partial_model`部分匹配或返回空模型。

**Q3.3** ⭐⭐ Prompt模板中是如何约束LLM减少幻觉的？请列举至少三种机制。

> 参考要点：①RAG检索提供法律依据作为上下文（有法可依）②低temperature=0.3减少随机性 ③结构化输出强制JSON格式 ④Prompt明确要求"参考上述法律依据" ⑤输出Pydantic校验过滤无效结果。

**Q3.4** ⭐⭐⭐ 风险分析链（RiskAnalysisChain）和合规检查链（ComplianceCheckChain）是如何并行执行的？为什么要关闭合规检查？

> 参考要点：`CompleteReviewChain`使用`asyncio.gather`并行执行风险分析和合规检查；但实际审查流程中关闭了合规检查（`check_invalid_clause = False`），因为风险分析已包含法律风险维度，避免重复分析。

**Q3.5** ⭐⭐ 项目中LLM的Temperature参数是如何配置的？在不同场景下是否有不同的设置？

> 参考要点：通义千问`TONGYI_TEMPERATURE = 0.3`（较低，减少幻觉）；通用Chat `CHAT_TEMPERATURE = 0.7`（稍高，增加对话自然性）；本地模型`LOCAL_QWEN_TEMPERATURE = 0.7`。

---

## 四、存储架构与对话历史管理

**Q4.1** ⭐⭐⭐ 项目的对话历史存储采用了什么架构？请说明短期存储和长期存储的区别及各自用途。

> 参考要点：短期存储使用Redis Checkpointer（LangGraph状态持久化，支持滑动窗口截断，保留最近20条）；长期存储使用MySQL（chatbot_conversation + chatbot_message表，存储完整消息历史）；Redis缓存对话列表和详情加速查询。

**Q4.2** ⭐⭐ 请详细说明上下文截断（滑动窗口）的实现原理。为什么要保留系统消息？截断后如何影响对话质量？

> 参考要点：`trim_messages_sliding_window`分离SystemMessage和其他消息，保留最近N条非系统消息+所有系统消息；`MAX_HISTORY_MESSAGES=20`；系统消息（如工具调用结果）对Agent运行至关重要不能丢弃；截断可能导致早期上下文丢失，影响长对话连贯性。

**Q4.3** ⭐⭐ Spring Boot后端是如何缓存对话数据的？当数据更新时缓存如何失效？

> 参考要点：对话列表缓存Key为`conversation:list:{userId}`，对话详情缓存Key为`conversation:detail:{conversationId}`；更新/删除/重命名操作时调用`deleteCach`清除相关缓存，下次查询时重新从MySQL加载并缓存。

**Q4.4** ⭐⭐⭐ 项目中Redis的使用场景有哪些？请分类说明。

> 参考要点：①LangGraph Checkpointer（对话状态持久化）②对话列表/详情缓存（业务缓存）③分布式锁（防止合同重复审查）④Token黑名单/会话管理；使用不同db隔离（如db=1用于checkpoint）。

**Q4.5** ⭐⭐ 消息保存流程是怎样的？用户消息和AI回复的保存时机有何不同？

> 参考要点：用户消息在调用AI前同步保存到MySQL；AI回复在流式响应完成后通过回调异步保存（使用线程池`executorService`）；这样确保即使前端断开连接，AI回复也能被持久化。

---

## 五、系统架构与工程设计

**Q5.1** ⭐⭐⭐ 项目采用了Spring Boot + FastAPI双后端架构，请分析这种设计的优缺点。各后端的职责划分是什么？

> 参考要点：Spring Boot负责业务逻辑（用户管理、合同管理、对话CRUD、缓存）；FastAPI负责AI推理（Agent、RAG、LLM调用）；优点是职责分离、AI部分可用Python生态；缺点是增加运维复杂度、跨服务通信开销。

**Q5.2** ⭐⭐⭐ 项目中合同审查任务是如何防止重复提交的？请说明分布式锁的实现方案。

> 参考要点：使用Redis分布式锁（`RedisLock`），lock_key为`review:contract:{contractId}`；非阻塞获取锁，已锁定时返回409；支持自动续期（Watchdog）防止长任务锁过期；锁超时5分钟。

**Q5.3** ⭐⭐⭐ 如果要将系统从单机部署扩展到多机部署，需要考虑哪些问题？请从对话状态、向量检索、缓存三个维度分析。

> 参考要点：①对话状态：Redis Checkpointer天然支持多机共享 ②向量检索：需要将Chroma切换为Milvus等分布式向量库，或使用共享存储 ③缓存：Redis已经是分布式缓存，需考虑缓存一致性 ④额外：需要Session共享、负载均衡、文件存储共享（如MinIO）。

**Q5.4** ⭐⭐ 项目中的降级策略是如何设计的？请分别说明LLM调用和RAG检索的降级方案。

> 参考要点：LLM降级：主模型失败→按优先级尝试备用模型→熔断器机制；RAG降级：向量检索失败→关键词匹配降级→返回空结果；两种降级都通过`FallbackManager`统一管理，使用`FallbackResult`封装结果。

**Q5.5** ⭐⭐⭐⭐ 请设计一个方案，让系统能够支持多租户（不同公司的法律文档完全隔离）。

> 参考要点：①向量数据库：每个租户独立Collection或独立Chroma实例 ②MySQL：租户ID字段隔离 ③Redis：Key前缀加入租户标识 ④Embedding模型可共享（降低成本）⑤LLM调用可共享 ⑥文件存储按租户分目录。

---

## 六、前端与流式输出

**Q6.1** ⭐⭐ 项目中是如何实现SSE（Server-Sent Events）流式输出的？请描述从用户发送消息到前端渲染的完整链路。

> 参考要点：前端POST纯文本→Spring Boot转发→FastAPI `StreamingResponse`（text/event-stream）→SSE事件流→前端EventSource接收→逐字渲染；事件格式：`data: {"content": "..."}` 或 `data: [DONE]`。

**Q6.2** ⭐⭐ 前端是如何管理对话状态的？请说明Vuex/Pinia Store的设计。

> 参考要点：使用Pinia Store（chatbot.js）管理对话列表、当前对话、消息列表；`conversationId`存储在localStorage中持久化；支持新建对话、切换对话、重命名、删除等操作。

**Q6.3** ⭐⭐⭐ 如何处理流式输出过程中的中断场景？当用户主动中断或网络断开时，系统如何保证数据一致性？

> 参考要点：①用户中断：调用`stop_conversation`接口设置中断标记，Agent检查标记后停止输出 ②网络断开：AI回复通过回调异步保存，即使前端断开也能持久化 ③`CancelledError`捕获：异常时清理token和中断标记。

---

## 七、Embedding与向量化

**Q7.1** ⭐⭐ 项目中使用了什么Embedding模型？其向量维度是多少？为什么选择这个模型？

> 参考要点：默认使用`BAAI/bge-small-zh-v1.5`（HuggingFace加载）；向量维度512；选择原因：中文优化、模型体积小（约90MB）、推理速度快、在中文语义相似度任务上表现优秀。

**Q7.2** ⭐⭐ 项目中支持哪些Embedding类型？如何切换？

> 参考要点：支持HuggingFace本地模型、OpenAI Embedding、ModelScope Embedding、Ollama Embedding；通过配置`EMBEDDING_TYPE`和`EMBEDDING_MODEL`切换；使用工厂模式（`get_embeddings`）创建实例。

**Q7.3** ⭐⭐⭐ 在向量检索时，系统如何检测和处理无效的查询向量（如零向量）？

> 参考要点：计算向量模长`vector_norm`，若小于`1e-6`则判定为零向量，记录错误日志并返回空结果；这种防御性编程避免了无效查询导致的异常或错误结果。

---

## 八、安全与认证

**Q8.1** ⭐⭐ 项目中Agent工具调用时是如何传递用户认证信息的？为什么需要特殊的传递机制？

> 参考要点：使用`RequestContext`（上下文变量）和`set_request_token`（全局变量）双重机制；因为LangGraph在独立线程中执行工具函数，无法直接访问FastAPI的Request上下文，需要特殊机制跨线程传递。

**Q8.2** ⭐⭐ 项目中的分布式锁是如何防止死锁的？请说明其自动过期和续期机制。

> 参考要点：使用Redis `SET NX EX`原子操作设置锁和过期时间；支持Watchdog自动续期（定期延长锁过期时间）；获取锁时可选阻塞/非阻塞模式；异常时在finally中释放锁。

---

## 九、开放性设计题

**Q9.1** ⭐⭐⭐⭐ 如果合同审查的准确率不够高，你会从哪些维度进行优化？请给出完整的优化方案。

> 参考方向：①检索优化：引入Query改写、Rerank模型、多路召回 ②Prompt优化：细化风险维度、增加Few-shot示例 ③模型优化：使用更大模型、Fine-tune法律领域模型 ④后处理优化：事实校验、置信度评分 ⑤数据优化：法律知识库更新、文档分块策略优化。

**Q9.2** ⭐⭐⭐⭐ 当前系统是否有幻觉风险？如果有，你会如何设计一套完整的幻觉检测和缓解机制？

> 参考方向：①RAG检索提供法律依据约束 ②结构化输出+Pydantic校验 ③低Temperature ④增加事实一致性校验层（对引用的法条编号进行真实性验证）⑤置信度评分+人工审核标记 ⑥多模型交叉验证。

**Q9.3** ⭐⭐⭐⭐ 如果要让系统支持多模态合同审查（如扫描件PDF、合同图片），需要做哪些改造？

> 参考方向：①OCR模块集成（如PaddleOCR）②多模态LLM（如qwen-vl-max）③图片预处理（去噪、矫正）④PDF解析增强（表格识别、版面分析）⑤向量化流程适配（图文混合Embedding）。

**Q9.4** ⭐⭐⭐⭐ 如果要实现"合同版本对比"功能（对比两版合同的差异并分析风险变化），你会如何设计？

> 参考方向：①文本Diff算法（如diff-match-patch）②条款级别的结构化对比 ③风险变化分析（新增/删除/修改的风险）④LLM辅助分析变更意图和影响 ⑤可视化展示（高亮差异）。

**Q9.5** ⭐⭐⭐ 当前检索阶段没有Query改写，请设计一个完整的Query改写模块，包括架构、算法选择和集成方案。

> 参考方向：①同义词扩展（法律术语词典，如"违约金"→"违约责任/违约赔偿"）②HyDE（LLM生成假设文档→Embedding→检索）③查询意图分类+模板扩展 ④多查询融合（生成多个改写查询，分别检索后合并去重）⑤集成位置：在`embed_query`之前插入改写层。

---

## 十、场景题与代码阅读

**Q10.1** ⭐⭐ 请阅读以下代码片段，说明其作用并指出可能的问题：

```python
def _calculate_keyword_score(self, query: str, clause_content: str) -> float:
    query_words = set(query.lower().split())
    content_words = set(clause_content.lower().split())
    if not query_words:
        return 0.0
    intersection = len(query_words & content_words)
    union = len(query_words | content_words)
    return intersection / union if union > 0 else 0.0
```

> 参考要点：Jaccard相似度计算；问题：①对中文使用空格分词效果差（应使用jieba等分词器）②未考虑词频信息 ③未做停用词过滤 ④大小写转换对中文无效。

**Q10.2** ⭐⭐⭐ 请解释以下Redis Checkpointer的Key设计，并说明为什么使用Sorted Set来管理checkpoint索引：

```
chatRecord:checkpoint:{thread_id}:{checkpoint_ns}:{checkpoint_id}
chatRecord:checkpoint:index:{thread_id}  (Sorted Set, score=timestamp)
```

> 参考要点：Key包含线程ID、命名空间、checkpoint ID，支持多维度查询；Sorted Set按时间戳排序，支持快速获取最新checkpoint、范围查询、按时间删除过期数据等操作。

**Q10.3** ⭐⭐⭐ 当用户发送"帮我审查这份合同"时，系统内部的完整调用链路是怎样的？请从HTTP请求开始，画出时序图或文字描述。

> 参考要点：前端POST → Spring Boot接收 → 准备对话（MySQL） → 保存用户消息（MySQL） → 转发到FastAPI → LangGraph Agent从Redis恢复状态 → 检索法律文档（Chroma） → 调用LLM分析 → 流式返回 → Spring Boot回调保存AI回复（MySQL） → 前端渲染。

---

## 面试评分维度

| 维度 | 权重 | 考察内容 |
|------|------|---------|
| **RAG理解深度** | 25% | 混合检索、向量数据库、召回重排策略 |
| **工程架构能力** | 25% | 双后端设计、存储分层、缓存策略 |
| **LLM应用经验** | 20% | Prompt设计、结构化输出、幻觉控制 |
| **问题解决能力** | 15% | 降级策略、并发处理、异常处理 |
| **系统设计思维** | 15% | 扩展性、可维护性、性能优化 |
