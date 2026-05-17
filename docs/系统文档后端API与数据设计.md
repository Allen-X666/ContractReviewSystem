# 系统文档后端 API 与数据设计文档

## 一、架构概述

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   前端      │────▶│  SpringBoot  │────▶│   FastAPI   │
│  (Vue3)     │◀────│   (业务层)   │◀────│  (AI服务层) │
└─────────────┘     └──────────────┘     └─────────────┘
                          │
                          ▼
                   ┌──────────────┐
                   │   MySQL      │
                   │  (业务数据)  │
                   └──────────────┘
```

**分层职责**:
- **SpringBoot**: 业务逻辑处理、用户认证、数据持久化、文件存储
- **FastAPI**: AI能力服务（文档向量化、智能检索）

---

## 二、SpringBoot 业务层

### 2.1 项目结构

```
ContractReview/src/main/java/com/example/contractreview/
├── controller/
│   └── AdminController.java          # 系统管理API
├── service/
│   ├── AdminService.java             # 服务接口
│   └── serviceImpl/
│       └── AdminServiceImpl.java     # 服务实现
├── client/
│   └── FastApiClient.java            # FastAPI调用客户端
├── model/
│   ├── entity/                       # 数据库实体
│   ├── dto/                          # 数据传输对象
│   └── vo/                           # 视图对象
├── mapper/                           # MyBatis映射器
└── enums/                            # 枚举定义
```

### 2.2 数据模型

#### 2.2.1 系统公告实体 (Notice)

**文件**: `model/entity/Notice.java`

```java
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Notice {
    private Long id;                    // 公告ID
    private String title;               // 公告标题
    private NoticeType type;            // 公告类型 (SYSTEM/FEATURE/MAINTENANCE/OTHER)
    private String content;             // 公告内容（支持Markdown）
    private PublishType publishType;    // 发布方式 (IMMEDIATE/SCHEDULED)
    private LocalDateTime publishTime;  // 发布时间
    private NoticeStatus status;        // 公告状态 (PUBLISHED/PENDING)
    private Boolean isTop;              // 是否置顶
    private Long authorId;              // 发布人ID
    private LocalDateTime createdAt;    // 创建时间
    private LocalDateTime updatedAt;    // 更新时间
}
```

#### 2.2.2 法律文档实体 (LawDocument)

**文件**: `model/entity/LawDocument.java`

```java
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class LawDocument {
    private Long id;                    // 文档ID
    private String name;                // 文档名称
    private LawType type;               // 文档类型 (LAW/INTERPRETATION/TEMPLATE/OTHER)
    private String filePath;            // 文件存储路径
    private Long fileSize;              // 文件大小(字节)
    private String fileType;            // 文件类型 (pdf/doc/docx)
    private LocalDate effectiveDate;    // 生效日期
    private String description;         // 文档说明
    private Integer uploadUserId;       // 上传用户ID
    private LocalDateTime createAt;     // 创建时间
}
```

#### 2.2.3 系统文档实体 (SystemDocument) - 建议新增

```java
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SystemDocument {
    private Long id;                    // 文档ID
    private String name;                // 文档名称
    private SystemDocCategory category; // 文档分类 (MANUAL/GUIDE/FAQ/SYSTEM/OTHER)
    private String tags;                // 标签(JSON数组字符串)
    private String description;         // 文档说明
    private String filePath;            // 文件存储路径
    private Long fileSize;              // 文件大小
    private String fileType;            // 文件类型
    private String vectorCollection;    // 向量库集合名称
    private Integer chunkCount;         // 分块数量
    private SystemDocStatus status;     // 状态 (ACTIVE/DELETED)
    private Long createBy;              // 上传人ID
    private LocalDateTime createAt;     // 创建时间
    private LocalDateTime updateAt;     // 更新时间
}
```

### 2.3 DTO 定义

#### 2.3.1 公告发布 DTO

**文件**: `model/dto/NoticePublishDTO.java`

```java
@Data
@NoArgsConstructor
@AllArgsConstructor
public class NoticePublishDTO {
    @NotBlank(message = "公告标题不能为空")
    @Size(max = 100, message = "公告标题长度不能超过100字符")
    private String title;

    @NotNull(message = "公告类型不能为空")
    private NoticeType type;

    @NotBlank(message = "公告内容不能为空")
    @Size(max = 2000, message = "公告内容长度不能超过2000字符")
    private String content;

    @NotNull(message = "发布方式不能为空")
    private PublishType publishType;

    private LocalDateTime publishTime;  // 定时发布时必填
    private Boolean isTop;              // 是否置顶
}
```

#### 2.3.2 法律文档上传 DTO

**文件**: `model/dto/LawUploadDTO.java`

```java
@Data
@NoArgsConstructor
@AllArgsConstructor
public class LawUploadDTO {
    @NotNull(message = "文档类型不能为空")
    private LawType type;

    private LocalDate effectiveDate;

    @Size(max = 500, message = "文档说明长度不能超过500字符")
    private String description;
}
```

#### 2.3.3 系统文档上传 DTO - 建议新增

```java
@Data
@NoArgsConstructor
@AllArgsConstructor
public class SystemDocUploadDTO {
    @NotNull(message = "文档分类不能为空")
    private SystemDocCategory category;

    private List<String> tags;          // 文档标签

    @Size(max = 500, message = "文档说明长度不能超过500字符")
    private String description;
}
```

### 2.4 Controller 层 API

**文件**: `controller/AdminController.java`

#### 2.4.1 系统公告 API

| 接口 | 方法 | 说明 |
|------|------|------|
| `POST /admin/announcement` | 发布公告 | 发布系统公告，支持定时发布 |
| `GET /admin/announcement/list` | 获取公告列表 | 获取所有公告列表 |
| `PUT /admin/announcement/{id}` | 编辑公告 | 修改公告内容 |
| `DELETE /admin/announcement/{id}` | 删除公告 | 删除指定公告 |
| `PUT /admin/announcement/{id}/top` | 置顶/取消置顶 | 切换公告置顶状态 |

```java
/**
 * 系统公告发布
 */
@PostMapping("/announcement")
@Operation(summary = "系统公告发布")
public Result<Notice> announcement(@RequestHeader("Authorization") String authorization,
                                   @RequestBody @Valid NoticePublishDTO noticePublishDTO) {
    return adminService.publishNotice(authorization, noticePublishDTO);
}

/**
 * 获取公告列表
 */
@GetMapping("/announcement/list")
@Operation(summary = "获取公告列表")
public Result<List<NoticeVO>> announcementList() throws JsonProcessingException {
    return adminService.getAnnouncementList();
}

/**
 * 编辑公告
 */
@PutMapping("/announcement/{id}")
@Operation(summary = "编辑公告")
public Result<Notice> editAnnouncement(@RequestBody @Valid NoticePublishDTO noticePublishDTO,
                                       @PathVariable Integer id) {
    return adminService.editNotice(id, noticePublishDTO);
}

/**
 * 删除公告
 */
@DeleteMapping("/announcement/{id}")
@Operation(summary = "删除公告")
public Result<String> deleteAnnouncement(@PathVariable Integer id) {
    return adminService.deleteAnnouncement(id);
}

/**
 * 置顶/取消置顶
 */
@PutMapping("/announcement/{id}/top")
@Operation(summary = "置顶/取消置顶")
public Result<String> topAnnouncement(@PathVariable Integer id,
                              @RequestBody TopAnnounceDTO topAnnounceDTO) {
    return adminService.topAnnouncement(id, topAnnounceDTO);
}
```

#### 2.4.2 法律文档 API

| 接口 | 方法 | 说明 |
|------|------|------|
| `POST /admin/law/upload` | 上传法律文档 | 上传并解析法律文档 |
| `GET /admin/law/list` | 获取法律列表 | 获取所有法律文档 |
| `DELETE /admin/law/{id}` | 删除文档 | 删除指定文档 |
| `GET /admin/law/{id}/file` | 获取文件 | 预览/下载文档文件 |

```java
/**
 * 上传法律文档
 */
@PostMapping(value = "/law/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
@Operation(summary = "上传法律文档")
public Result<LawDocument> uploadLaw(
        @RequestParam("file") MultipartFile file,
        @RequestParam("type") String type,
        @RequestParam(required = false) String effectiveDate,
        @RequestParam(required = false) String description,
        @RequestHeader("Authorization") String authorization) {
    Integer userId = tokenUtils.getUserId(authorization);
    // ... 参数处理和调用Service
    return adminService.uploadLawDocument(userId, file, dto);
}

/**
 * 获取法律列表
 */
@GetMapping("/law/list")
@Operation(summary = "获取法律列表")
public Result<List<LawDocument>> lawList() throws JsonProcessingException {
    return adminService.getLawDocumentList();
}

/**
 * 删除文档
 */
@DeleteMapping("/law/{id}")
@Operation(summary = "删除文档")
public Result<String> deleteLaw(@PathVariable Long id) {
    return adminService.deleteLawDocument(id);
}

/**
 * 预览文档 - 获取文件内容
 */
@GetMapping("/law/{id}/file")
@Operation(summary = "获取法律文档文件")
public ResponseEntity<Resource> getLawFile(@PathVariable Long id) {
    // ... 文件读取和返回
}
```

#### 2.4.3 系统文档 API - 建议新增

| 接口 | 方法 | 说明 |
|------|------|------|
| `POST /admin/system-docs/upload` | 上传系统文档 | 上传系统操作文档 |
| `GET /admin/system-docs/list` | 获取文档列表 | 获取系统文档列表 |
| `DELETE /admin/system-docs/{id}` | 删除文档 | 删除指定文档 |
| `GET /admin/system-docs/{id}/file` | 获取文件 | 预览/下载文档 |

```java
/**
 * 上传系统文档
 */
@PostMapping(value = "/system-docs/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
@Operation(summary = "上传系统文档")
public Result<SystemDocument> uploadSystemDoc(
        @RequestParam("file") MultipartFile file,
        @RequestParam("category") String category,
        @RequestParam(required = false) String tags,
        @RequestParam(required = false) String description,
        @RequestHeader("Authorization") String authorization) {
    Integer userId = tokenUtils.getUserId(authorization);
    return adminService.uploadSystemDocument(userId, file, category, tags, description);
}

/**
 * 获取系统文档列表
 */
@GetMapping("/system-docs/list")
@Operation(summary = "获取系统文档列表")
public Result<List<SystemDocument>> systemDocList() {
    return adminService.getSystemDocumentList();
}

/**
 * 删除系统文档
 */
@DeleteMapping("/system-docs/{id}")
@Operation(summary = "删除系统文档")
public Result<String> deleteSystemDoc(@PathVariable Long id) {
    return adminService.deleteSystemDocument(id);
}

/**
 * 获取系统文档文件
 */
@GetMapping("/system-docs/{id}/file")
@Operation(summary = "获取系统文档文件")
public ResponseEntity<Resource> getSystemDocFile(@PathVariable Long id) {
    return adminService.getSystemDocumentFile(id);
}
```

### 2.5 Service 层实现

**文件**: `service/serviceImpl/AdminServiceImpl.java`

#### 2.5.1 公告发布流程

```java
@Override
@Transactional(rollbackFor = Exception.class)
public Result<Notice> publishNotice(String authorization, NoticePublishDTO dto) {
    // 1. 获取当前用户ID
    Integer userId = tokenUtils.getUserId(authorization);
    
    // 2. 验证发布时间（定时发布需指定时间）
    if (dto.getPublishType() == PublishType.SCHEDULED && dto.getPublishTime() == null) {
        return Result.error(ResultCode.BAD_REQUEST.getCode(), "定时发布时间不能为空");
    }
    
    // 3. 构建公告实体
    Notice notice = buildNoticeFromDTO(dto, userId.longValue());
    
    // 4. 保存到数据库
    noticeMapper.insert(notice);
    
    // 5. 清除缓存
    clearAnnouncementCache();
    
    return Result.success(notice);
}
```

#### 2.5.2 法律文档上传流程

```java
@Override
@Transactional(rollbackFor = Exception.class)
public Result<LawDocument> uploadLawDocument(Integer userId, MultipartFile file, LawUploadDTO dto) {
    // 1. 校验文件（类型、大小）
    validateLawFile(file);
    
    // 2. 调用FastAPI上传并解析文档
    FastApiResult<Map<String, Object>> fastApiResult = fastApiClient.uploadLawDocument(
        file, 
        dto.getType().name().toLowerCase(),
        dto.getEffectiveDate() != null ? dto.getEffectiveDate().toString() : null,
        dto.getDescription()
    );
    
    // 3. 解析返回的法规和法条数据
    List<LawFileParser.ParseResult> parseResults = LawFileParser.parseAll(file);
    
    // 4. 批量插入/更新法规数据
    processLawRegulations(parseResults);
    
    // 5. 保存文件到本地存储
    Path targetPath = saveLawFileToLocal(file, userId);
    
    // 6. 保存文档元数据到数据库
    LawDocument document = LawDocument.builder()
        .name(file.getOriginalFilename())
        .type(dto.getType())
        .filePath(targetPath.toString())
        .fileSize(file.getSize())
        .fileType(getFileExtension(file.getOriginalFilename()))
        .effectiveDate(dto.getEffectiveDate())
        .description(dto.getDescription())
        .uploadUserId(userId)
        .build();
    
    lawMapper.insertLawDocument(document);
    
    // 7. 清除缓存
    clearLawCache();
    
    return Result.success(document);
}
```

#### 2.5.3 系统文档上传流程 - 建议实现

```java
@Override
@Transactional(rollbackFor = Exception.class)
public Result<SystemDocument> uploadSystemDocument(
        Integer userId, 
        MultipartFile file, 
        String category,
        String tags,
        String description) {
    
    // 1. 校验文件
    validateSystemDocFile(file);
    
    // 2. 保存文件到本地存储
    Path targetPath = saveSystemDocFile(file, userId);
    
    // 3. 保存元数据到数据库
    SystemDocument document = SystemDocument.builder()
        .name(file.getOriginalFilename())
        .category(SystemDocCategory.valueOf(category.toUpperCase()))
        .tags(tags)
        .description(description)
        .filePath(targetPath.toString())
        .fileSize(file.getSize())
        .fileType(getFileExtension(file.getOriginalFilename()))
        .vectorCollection("system_ops_" + category.toLowerCase())
        .status(SystemDocStatus.ACTIVE)
        .createBy(userId.longValue())
        .build();
    
    systemDocMapper.insert(document);
    
    // 4. 异步调用FastAPI进行文档向量化
    asyncProcessSystemDocVector(document);
    
    // 5. 清除缓存
    clearSystemDocCache();
    
    return Result.success(document);
}

/**
 * 异步处理文档向量化
 */
@Async
public void asyncProcessSystemDocVector(SystemDocument document) {
    try {
        // 读取文件内容
        byte[] fileContent = Files.readAllBytes(Paths.get(document.getFilePath()));
        
        // 调用FastAPI进行向量化
        FastApiResult<Map<String, Object>> result = fastApiClient.uploadSystemDocument(
            document.getName(),
            fileContent,
            document.getCategory().name().toLowerCase(),
            document.getTags(),
            document.getDescription()
        );
        
        if (result.getCode() == 200) {
            // 更新文档分块数量
            Integer chunkCount = (Integer) result.getData().get("chunk_count");
            systemDocMapper.updateChunkCount(document.getId(), chunkCount);
            log.info("系统文档向量化成功, documentId: {}, chunkCount: {}", 
                document.getId(), chunkCount);
        } else {
            log.error("系统文档向量化失败, documentId: {}, error: {}", 
                document.getId(), result.getMessage());
        }
    } catch (Exception e) {
        log.error("系统文档向量化异常, documentId: {}", document.getId(), e);
    }
}
```

### 2.6 FastAPI 客户端

**文件**: `client/FastApiClient.java`

#### 2.6.1 现有方法

```java
/**
 * 上传法律文档到FastAPI
 */
public FastApiResult<Map<String, Object>> uploadLawDocument(
        MultipartFile file, 
        String documentType, 
        String effectiveDate, 
        String description) {
    
    MultiValueMap<String, Object> parts = new LinkedMultiValueMap<>();
    parts.add("file", file.getResource());
    parts.add("document_type", documentType);
    if (effectiveDate != null) parts.add("effective_date", effectiveDate);
    if (description != null) parts.add("description", description);

    return restClient.post()
        .uri("/laws/upload")
        .contentType(MediaType.MULTIPART_FORM_DATA)
        .body(parts)
        .retrieve()
        .body(new ParameterizedTypeReference<FastApiResult<Map<String, Object>>>() {});
}
```

#### 2.6.2 建议新增方法

```java
/**
 * 上传系统文档到FastAPI进行向量化
 */
public FastApiResult<Map<String, Object>> uploadSystemDocument(
        String fileName,
        byte[] fileContent,
        String category,
        String tags,
        String description) {
    
    MultiValueMap<String, Object> parts = new LinkedMultiValueMap<>();
    parts.add("file_name", fileName);
    parts.add("file_content", Base64.getEncoder().encodeToString(fileContent));
    parts.add("category", category);
    if (tags != null) parts.add("tags", tags);
    if (description != null) parts.add("description", description);

    return restClient.post()
        .uri("/system-docs/upload")
        .contentType(MediaType.MULTIPART_FORM_DATA)
        .body(parts)
        .retrieve()
        .body(new ParameterizedTypeReference<FastApiResult<Map<String, Object>>>() {});
}

/**
 * 删除系统文档向量
 */
public FastApiResult<Map<String, Object>> deleteSystemDocumentVectors(Long documentId) {
    return restClient.post()
        .uri("/system-docs/{id}/delete", documentId)
        .retrieve()
        .body(new ParameterizedTypeReference<FastApiResult<Map<String, Object>>>() {});
}

/**
 * 搜索系统文档
 */
public FastApiResult<List<Map<String, Object>>> searchSystemDocuments(
        String query, 
        Integer topK) {
    
    Map<String, Object> body = new HashMap<>();
    body.put("query", query);
    body.put("top_k", topK);

    return restClient.post()
        .uri("/system-docs/search")
        .body(body)
        .retrieve()
        .body(new ParameterizedTypeReference<FastApiResult<List<Map<String, Object>>>>() {});
}
```

---

## 三、FastAPI AI服务层

### 3.1 项目结构

```
合同审查/app/
├── services/
│   └── system_ops_upload_service.py    # 系统文档上传服务
├── rag/
│   ├── system_manual_loader.py         # Markdown加载器
│   ├── system_manual_splitter.py       # 文档分块器
│   ├── system_retriever.py             # 文档检索器
│   └── vector_store.py                 # 向量存储
└── api/v1/endpoints/
    └── system_docs.py                  # 系统文档API（建议新增）
```

### 3.2 系统文档上传服务

**文件**: `services/system_ops_upload_service.py`

```python
class SystemOpsUploadService:
    """系统操作文档上传异步处理服务（单例模式）"""
    
    SYSTEM_VECTOR_DB_DIR = "data/vector_db/system_operations"
    
    def __init__(self):
        self.tasks: Dict[str, SystemOpsUploadTask] = {}
        self.task_queue = Queue()
        self.document_loader = DocumentLoader()
        self.worker_thread = None
        self._running = False
    
    def create_task(self, file_name, file_content, file_ext, category, description) -> str:
        """创建上传任务"""
        task_id = str(uuid.uuid4())
        task = SystemOpsUploadTask(
            task_id=task_id,
            file_name=file_name,
            file_content=file_content,
            file_ext=file_ext,
            category=category,
            description=description,
            status="pending",
            progress=0,
            message="等待处理",
            created_at=datetime.now()
        )
        self.tasks[task_id] = task
        self.task_queue.put(task_id)
        return task_id
    
    def _process_task(self, task_id: str):
        """处理任务"""
        task = self.tasks[task_id]
        task.status = "processing"
        task.started_at = datetime.now()
        
        try:
            # 1. 加载文档
            task.progress = 10
            chunks = self.document_loader.load_and_split(
                file_obj=io.BytesIO(task.file_content),
                file_name=task.file_name
            )
            
            # 2. 添加元数据
            task.progress = 30
            for i, chunk in enumerate(chunks):
                chunk.clause_id = f"sysops_{task_id}_chunk_{i}"
                chunk.metadata.update({
                    "knowledge_base": "system_operations",
                    "category": task.category,
                    "source": task.file_name,
                    "upload_time": datetime.now().isoformat()
                })
            
            # 3. 生成向量
            task.progress = 60
            texts = [chunk.clause_content for chunk in chunks]
            embeddings = embed_documents(texts)
            
            # 4. 存入向量库
            task.progress = 80
            collection_name = f"system_ops_{task.category}"
            vector_store = ChromaVectorStore(
                collection_name=collection_name,
                persist_directory=self.SYSTEM_VECTOR_DB_DIR
            )
            vector_store.add_documents(chunks, embeddings)
            
            # 5. 清除缓存
            invalidate_system_stores_cache()
            
            task.progress = 100
            task.status = "completed"
            task.message = f"处理完成，共 {len(chunks)} 个片段"
            task.result = {"chunk_count": len(chunks)}
            
        except Exception as e:
            task.status = "failed"
            task.message = f"处理失败: {str(e)}"
            task.error = str(e)
        finally:
            task.completed_at = datetime.now()
```

### 3.3 系统文档检索器

**文件**: `rag/system_retriever.py`

```python
class CachedSystemDocumentRetriever(BaseRetriever):
    """带缓存的系统操作文档检索器"""
    
    def __init__(self, cache_ttl=3600):
        self._cache = TTLCache(maxsize=1000, ttl=cache_ttl)
        self._stats = {"hits": 0, "misses": 0}
        self._embedding_model = None
        self._lock = threading.Lock()
    
    def _get_embedding_model(self):
        """延迟初始化嵌入模型"""
        if self._embedding_model is None:
            with self._lock:
                if self._embedding_model is None:
                    from app.core.config import settings
                    from app.services.embeddings import get_embedding_model
                    self._embedding_model = get_embedding_model(
                        settings.EMBEDDING_TYPE,
                        settings.EMBEDDING_MODEL
                    )
        return self._embedding_model
    
    async def retrieve(self, query: str, top_k: int = 5, 
                       filter_dict=None, use_cache: bool = True) -> List[str]:
        """检索系统文档"""
        
        # 1. 检查缓存
        cache_key = f"{query}_{top_k}_{hash(str(filter_dict))}"
        if use_cache and cache_key in self._cache:
            self._stats["hits"] += 1
            return self._cache[cache_key]
        
        self._stats["misses"] += 1
        
        # 2. 生成查询向量
        model = self._get_embedding_model()
        query_embedding = model.embed_query(query)
        
        # 3. 搜索向量库
        results = search_system_documents(query_embedding, top_k)
        
        # 4. 提取内容
        contents = [result[0].clause_content for result in results]
        
        # 5. 更新缓存
        if use_cache:
            self._cache[cache_key] = contents
        
        return contents
```

### 3.4 建议新增的 FastAPI 接口

**文件**: `api/v1/endpoints/system_docs.py`

```python
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.services.system_ops_upload_service import system_ops_upload_service

router = APIRouter()

@router.post("/system-docs/upload")
async def upload_system_document(
    file_name: str = Form(...),
    file_content: str = Form(...),  # Base64编码
    category: str = Form(...),
    tags: str = Form(None),
    description: str = Form(None)
):
    """
    上传系统文档进行向量化处理
    
    - **file_name**: 原始文件名
    - **file_content**: Base64编码的文件内容
    - **category**: 文档分类 (manual/guide/faq/system/other)
    - **tags**: 标签JSON字符串
    - **description**: 文档描述
    """
    import base64
    
    # 解码文件内容
    file_bytes = base64.b64decode(file_content)
    file_ext = file_name.split('.')[-1]
    
    # 创建异步任务
    task_id = system_ops_upload_service.create_task(
        file_name=file_name,
        file_content=file_bytes,
        file_ext=file_ext,
        category=category,
        description=description
    )
    
    # 启动服务
    system_ops_upload_service.start()
    
    return {"code": 200, "data": {"task_id": task_id}}

@router.get("/system-docs/task/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
    task = system_ops_upload_service.get_task(task_id)
    if not task:
        raise HTTPException(404, "任务不存在")
    return {"code": 200, "data": task.to_dict()}

@router.post("/system-docs/search")
async def search_system_docs(
    query: str,
    top_k: int = 5,
    category: str = None
):
    """搜索系统文档"""
    from app.rag.system_retriever import CachedSystemDocumentRetriever
    
    retriever = CachedSystemDocumentRetriever()
    filter_dict = {"category": category} if category else None
    
    results = await retriever.retrieve(query, top_k, filter_dict)
    
    return {"code": 200, "data": results}

@router.post("/system-docs/{doc_id}/delete")
async def delete_system_document_vectors(doc_id: str):
    """删除文档向量"""
    # 根据doc_id找到并删除对应向量
    # 清除缓存
    invalidate_system_stores_cache()
    
    return {"code": 200, "message": "删除成功"}
```

---

## 四、数据库存储

### 4.1 现有表结构

#### 4.1.1 公告表 (notice)

```sql
CREATE TABLE notice (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(100) NOT NULL COMMENT '公告标题',
    type VARCHAR(20) NOT NULL COMMENT '类型: system/feature/maintenance/other',
    content TEXT NOT NULL COMMENT '公告内容',
    publish_type VARCHAR(20) NOT NULL COMMENT '发布方式: immediate/scheduled',
    publish_time DATETIME COMMENT '发布时间',
    status VARCHAR(20) NOT NULL COMMENT '状态: published/pending',
    is_top TINYINT(1) DEFAULT 0 COMMENT '是否置顶',
    author_id BIGINT COMMENT '发布人ID',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_status (status),
    INDEX idx_is_top (is_top)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统公告表';
```

#### 4.1.2 法律文档表 (law_document)

```sql
CREATE TABLE law_document (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL COMMENT '文档名称',
    type VARCHAR(20) NOT NULL COMMENT '类型: law/interpretation/template/other',
    file_path VARCHAR(500) COMMENT '文件路径',
    file_size BIGINT COMMENT '文件大小(字节)',
    file_type VARCHAR(20) COMMENT '文件类型: pdf/doc/docx',
    effective_date DATE COMMENT '生效日期',
    description TEXT COMMENT '文档说明',
    upload_user_id INT COMMENT '上传用户ID',
    create_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_type (type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='法律文档表';
```

### 4.2 建议新增表

#### 4.2.1 系统文档表 (system_document)

```sql
CREATE TABLE system_document (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL COMMENT '文档名称',
    category VARCHAR(50) NOT NULL COMMENT '分类: manual/guide/faq/system/other',
    tags JSON COMMENT '标签数组',
    description TEXT COMMENT '文档描述',
    file_path VARCHAR(500) COMMENT '文件存储路径',
    file_size BIGINT COMMENT '文件大小(字节)',
    file_type VARCHAR(20) COMMENT '文件类型: pdf/docx/md/txt',
    vector_collection VARCHAR(100) COMMENT '向量库集合名称',
    chunk_count INT DEFAULT 0 COMMENT '分块数量',
    status VARCHAR(20) DEFAULT 'active' COMMENT '状态: active/deleted',
    create_by BIGINT COMMENT '上传人ID',
    create_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_category (category),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统文档表';
```

---

## 五、接口调用流程

### 5.1 系统公告发布流程

```
前端 ──POST /admin/announcement──▶ SpringBoot ──▶ MySQL
                                        │
                                        ▼
                                   清除Redis缓存
```

### 5.2 法律文档上传流程

```
前端 ──POST /admin/law/upload──▶ SpringBoot ──▶ FastAPI (/laws/upload)
                                     │              │
                                     ▼              ▼
                                  MySQL        向量化存储
                                     │
                                     ▼
                                本地文件存储
```

### 5.3 系统文档上传流程（建议）

```
前端 ──POST /admin/system-docs/upload──▶ SpringBoot
                                              │
                                              ├──▶ MySQL (保存元数据)
                                              │
                                              ├──▶ 本地文件存储
                                              │
                                              └──▶ FastAPI (/system-docs/upload)
                                                        │
                                                        ▼
                                                  异步向量化处理
                                                        │
                                                        ▼
                                                  向量库存储
```

---

## 六、枚举定义

### 6.1 公告类型 (NoticeType)

```java
public enum NoticeType {
    SYSTEM("system", "系统公告"),
    FEATURE("feature", "功能更新"),
    MAINTENANCE("maintenance", "维护通知"),
    OTHER("other", "其他");
}
```

### 6.2 法律文档类型 (LawType)

```java
public enum LawType {
    LAW("law", "法律法规"),
    INTERPRETATION("interpretation", "司法解释"),
    TEMPLATE("template", "合同范本"),
    OTHER("other", "其他");
}
```

### 6.3 系统文档分类 (SystemDocCategory) - 建议新增

```java
public enum SystemDocCategory {
    MANUAL("manual", "用户手册"),
    GUIDE("guide", "操作指南"),
    FAQ("faq", "常见问题"),
    SYSTEM("system", "系统说明"),
    OTHER("other", "其他文档");
}
```

---

## 七、配置参数

### 7.1 SpringBoot 配置

```yaml
# application.yml
fastapi:
  base-url: http://localhost:8000
  api-prefix: /api/v1
  timeout: 300000
  connect-timeout: 10000

storage:
  base-path: ${user.home}/contract-review/storage

file:
  max-size: 52428800  # 50MB
  allowed-types: pdf,doc,docx,md,txt
```

### 7.2 FastAPI 配置

```python
# app/core/config.py
class Settings:
    EMBEDDING_TYPE = "dashscope"
    EMBEDDING_MODEL = "text-embedding-v3"
    VECTOR_DB_TYPE = "chroma"
    SYSTEM_VECTOR_DB_DIR = "data/vector_db/system_operations"
```

---

## 八、注意事项

1. **文件大小限制**: 统一限制 50MB，SpringBoot 和 FastAPI 需保持一致
2. **异步处理**: 系统文档向量化是耗时操作，建议使用异步任务
3. **缓存策略**: 公告列表、法律文档列表使用 Redis 缓存，更新时清除
4. **错误处理**: FastAPI 调用失败时，SpringBoot 应回滚数据库事务
5. **向量维度**: 更换嵌入模型时需清空向量库重建
6. **文件存储**: 建议同时存储原始文件用于预览和下载
