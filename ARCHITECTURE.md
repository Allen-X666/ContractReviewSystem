# 合同审查系统架构说明

## 目录

- [系统概述](#系统概述)
- [架构设计](#架构设计)
- [请求链路](#请求链路)
- [技术实现](#技术实现)
- [数据流转](#数据流转)
- [部署架构](#部署架构)
- [安全设计](#安全设计)
- [性能优化](#性能优化)

## 系统概述

### 设计目标

- **高可用**: 支持水平扩展，单点故障不影响整体服务
- **高性能**: AI 审查响应时间 < 30 秒，普通 API 响应 < 200ms
- **安全性**: 多层安全防护，数据加密传输和存储
- **可维护**: 模块化设计，便于功能迭代和问题排查

### 核心模块

```
┌─────────────────────────────────────────────────────────────┐
│                         前端层                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   合同管理   │  │   审查中心   │  │     知识库         │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      SpringBoot 网关层                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   用户认证   │  │   业务逻辑   │  │     数据访问       │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI AI 服务层                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   文档解析   │  │   AI 推理   │  │     向量检索       │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 架构设计

### 三层架构详解

#### 1. 前端层 (Vue 3)

**技术选型**:
- **框架**: Vue 3 + Composition API
- **UI 组件**: Element Plus
- **状态管理**: Pinia
- **构建工具**: Vite
- **HTTP 客户端**: Axios

**核心功能模块**:

| 模块 | 功能 | 技术实现 |
|------|------|----------|
| 用户中心 | 登录/注册/权限管理 | JWT + RBAC |
| 合同管理 | 上传/列表/详情/删除 | 文件分片上传 |
| 审查中心 | 发起审查/进度查看/报告下载 | SSE 实时推送 |
| 知识库 | 法规查询/模板下载 | 全文检索 |
| 智能客服 | AI 对话/历史记录 | WebSocket |

**项目结构**:

```
frontend/src/
├── api/                    # API 接口封装
│   ├── auth.js            # 认证相关
│   ├── contract.js        # 合同管理
│   ├── review.js          # 审查任务
│   ├── knowledge.js       # 知识库
│   └── chat.js            # 智能客服
├── components/            # 公共组件
│   ├── common/           # 通用组件
│   ├── contract/         # 合同相关
│   └── review/           # 审查相关
├── views/                # 页面视图
│   ├── auth/             # 认证页面
│   ├── contract/         # 合同管理
│   ├── review/           # 审查中心
│   ├── knowledge/        # 知识库
│   └── chat/             # 智能客服
├── store/                # Pinia 状态管理
│   ├── user.js           # 用户状态
│   ├── contract.js       # 合同状态
│   └── review.js         # 审查状态
├── router/               # 路由配置
└── utils/                # 工具函数
```

#### 2. SpringBoot 网关层 (Java)

**技术选型**:
- **框架**: Spring Boot 4.0.5
- **数据访问**: MyBatis + MySQL
- **缓存**: Redis + Caffeine
- **安全**: Spring Security + JWT
- **文档**: SpringDoc OpenAPI

**核心职责**:

1. **统一入口**: 前端所有请求通过 SpringBoot 转发
2. **认证鉴权**: JWT Token 验证，RBAC 权限控制
3. **业务逻辑**: 用户管理、合同管理、审查任务管理
4. **数据持久化**: MySQL 数据存储，Redis 缓存
5. **服务转发**: 将 AI 相关请求转发到 FastAPI

**项目结构**:

```
ContractReview/src/main/java/com/example/contractreview/
├── config/               # 配置类
│   ├── CorsConfig.java              # 跨域配置
│   ├── WebMvcConfig.java            # Web 配置
│   ├── FastApiConfig.java           # FastAPI 配置
│   ├── RedisConfig.java             # Redis 配置
│   └── SecurityConfig.java          # 安全配置
├── controller/           # 控制器层
│   ├── AuthController.java          # 认证接口
│   ├── UserController.java          # 用户接口
│   ├── ContractController.java      # 合同接口
│   ├── ReviewController.java        # 审查接口
│   ├── KnowledgeController.java     # 知识库接口
│   └── ChatBotController.java       # 客服接口
├── service/              # 业务层
│   ├── AuthService.java
│   ├── UserService.java
│   ├── ContractService.java
│   ├── ReviewService.java
│   └── impl/             # 实现类
├── mapper/               # 数据访问层
│   ├── UserMapper.java
│   ├── ContractMapper.java
│   └── ReviewMapper.java
├── entity/               # 实体类
│   ├── User.java
│   ├── Contract.java
│   └── ReviewTask.java
├── dto/                  # 数据传输对象
│   ├── LoginDTO.java
│   ├── ContractDTO.java
│   └── ReviewDTO.java
├── vo/                   # 视图对象
│   ├── UserVO.java
│   ├── ContractVO.java
│   └── ReviewVO.java
├── client/               # HTTP 客户端
│   └── FastApiClient.java           # FastAPI 调用客户端
├── common/               # 公共类
│   ├── Result.java                  # 统一响应
│   ├── PageResult.java              # 分页响应
│   └── exception/                   # 异常处理
└── utils/                # 工具类
    ├── JwtUtils.java
    ├── FileUtils.java
    └── DateUtils.java
```

#### 3. FastAPI AI 服务层 (Python)

**技术选型**:
- **框架**: FastAPI 0.135.3
- **AI 框架**: LangChain
- **向量库**: Chroma / FAISS
- **模型调用**: DashScope (通义千问)
- **文档解析**: PyPDF2, python-docx

**核心职责**:

1. **文档解析**: PDF/DOCX 文本提取
2. **向量检索**: 法律知识库 RAG 检索
3. **AI 推理**: 合同风险分析
4. **报告生成**: Word/PDF 报告生成

**项目结构**:

```
合同审查/app/
├── api/                  # API 路由
│   └── v1/
│       ├── router.py                # 路由聚合
│       └── endpoints/
│           ├── auth.py              # 认证接口
│           ├── review.py            # 审查接口
│           ├── chat.py              # 对话接口
│           ├── laws.py              # 法规接口
│           └── health.py            # 健康检查
├── core/                 # 核心配置
│   ├── config.py                    # 应用配置
│   ├── database.py                  # 数据库连接
│   └── security.py                  # 安全工具
├── models/               # 数据模型
│   ├── user.py
│   ├── contract.py
│   └── review.py
├── services/             # 业务逻辑
│   ├── contract_service.py          # 合同服务
│   ├── review_service.py            # 审查服务
│   ├── chat_service.py              # 对话服务
│   └── law_service.py               # 法规服务
├── llm/                  # AI 模型相关
│   ├── llm_factory.py               # LLM 工厂
│   ├── qwen_llm.py                  # 通义千问
│   ├── deepseek_llm.py              # DeepSeek
│   ├── embeddings.py                # 向量模型
│   ├── review_chains.py             # 审查链
│   └── prompts.py                   # 提示词模板
├── rag/                  # RAG 检索
│   ├── vector_store.py              # 向量存储
│   ├── retriever.py                 # 检索器
│   ├── document_loader.py           # 文档加载
│   ├── text_splitter.py             # 文本分割
│   └── rag_chain.py                 # RAG 链
├── agent/                # AI Agent
│   ├── tools.py                     # 工具定义
│   ├── tools_helper.py              # 工具辅助
│   └── prompts.py                   # Agent 提示词
└── utils/                # 工具函数
    ├── file_utils.py
    ├── jwt_utils.py
    └── conversation_stopper.py
```

## 请求链路

### 典型请求流程

```
┌─────────────┐      POST /api/review/start       ┌──────────────┐
│   前端页面   │ ─────────────────────────────────> │  SpringBoot  │
│  (Vue3)     │                                   │   (Java)     │
└─────────────┘                                   └──────┬───────┘
                                                         │
                                                         │ HTTP 转发
                                                         ▼
                                                  ┌──────────────┐
                                                  │   FastAPI    │
                                                  │   (Python)   │
                                                  └──────────────┘
```

### 详细链路说明

#### 1. 用户认证流程

```
前端 ──POST /api/auth/login──> SpringBoot
                                  │
                                  ├── 验证用户名密码
                                  ├── 生成 JWT Token
                                  └── 缓存用户信息到 Redis
                                  │
前端 <────返回 Token──────────────┘
```

#### 2. 合同审查流程

```
前端 ──POST /api/review/start──> SpringBoot
                                    │
                                    ├── 验证用户权限
                                    ├── 保存审查任务到数据库
                                    ├── 调用 FastAPI 创建审查
                                    └── 返回 reviewId
                                    │
前端 <────返回 reviewId─────────────┘
     
前端 ──GET /api/review/{id}/progress──> SpringBoot (SSE)
                                          │
                                          ├── 创建 SseEmitter
                                          ├── 轮询 FastAPI 进度
                                          ├── 推送进度到前端
                                          └── 完成后关闭连接
```

#### 3. AI 对话流程

```
前端 ──POST /api/chat/send──> SpringBoot
                                │
                                ├── 验证用户权限
                                ├── 保存用户消息
                                ├── 转发到 FastAPI
                                │       │
                                │       ├── RAG 检索相关知识
                                │       ├── 调用 LLM 生成回复
                                │       └── 返回 AI 回复
                                │
                                ├── 保存 AI 回复
                                └── 返回给前端
```

## 技术实现

### 1. 前端实现

**文件**: `frontend/src/api/review.js`

```javascript
// 发起审查
export const startReview = (contractId) => {
  return request.post('/review/start', { contractId })
}

// SSE 进度监听
export const getReviewProgress = (reviewId) => {
  const eventSource = new EventSource(
    `${baseURL}/review/${reviewId}/progress`
  )
  
  eventSource.onmessage = (event) => {
    const progress = JSON.parse(event.data)
    // 更新进度条
  }
  
  return eventSource
}
```

### 2. SpringBoot 实现

#### 新增/修改的文件：

| 文件 | 说明 |
|------|------|
| `application.yml` | 添加 FastAPI 服务配置 |
| `FastApiConfig.java` | FastAPI 配置类 |
| `FastApiClient.java` | FastAPI HTTP 客户端 |
| `ReviewController.java` | 审查相关 REST 接口 |
| `ReviewService.java` | 服务接口定义 |
| `ReviewServiceImpl.java` | 服务实现，负责转发到 FastAPI |
| `FastApiResult.java` | FastAPI 统一响应包装 |
| `ReviewProgressVO.java` | 审查进度 VO |
| `ReviewResultVO.java` | 审查结果 VO |
| `RiskItemVO.java` | 风险项 VO |

#### 核心接口：

```java
// ReviewController.java
@RestController
@RequestMapping("/review")
public class ReviewController {
    
    @Autowired
    private ReviewService reviewService;
    
    // 发起审查
    @PostMapping("/start")
    public Result<ReviewVO> startReview(@RequestBody StartReviewDTO dto) {
        return Result.success(reviewService.startReview(dto));
    }
    
    // 获取审查进度 (SSE)
    @GetMapping("/{reviewId}/progress")
    public SseEmitter getProgress(@PathVariable Long reviewId) {
        return reviewService.getProgressEmitter(reviewId);
    }
    
    // 获取审查结果
    @GetMapping("/{reviewId}/result")
    public Result<ReviewResultVO> getResult(@PathVariable Long reviewId) {
        return Result.success(reviewService.getResult(reviewId));
    }
    
    // 获取风险列表
    @GetMapping("/{reviewId}/risks")
    public Result<List<RiskItemVO>> getRisks(@PathVariable Long reviewId) {
        return Result.success(reviewService.getRisks(reviewId));
    }
    
    // 重新审查
    @PostMapping("/{reviewId}/re-review")
    public Result<Void> reReview(@PathVariable Long reviewId) {
        reviewService.reReview(reviewId);
        return Result.success();
    }
    
    // 取消审查
    @PostMapping("/{reviewId}/cancel")
    public Result<Void> cancelReview(@PathVariable Long reviewId) {
        reviewService.cancelReview(reviewId);
        return Result.success();
    }
}
```

#### FastAPI 客户端：

```java
// FastApiClient.java
@Component
public class FastApiClient {
    
    @Value("${fastapi.base-url}")
    private String baseUrl;
    
    private final RestTemplate restTemplate;
    
    public FastApiResult<ReviewTask> createReview(ReviewRequest request) {
        String url = baseUrl + "/api/v1/review";
        ResponseEntity<FastApiResult> response = restTemplate.postForEntity(
            url, request, FastApiResult.class
        );
        return response.getBody();
    }
    
    public ReviewProgress getProgress(String reviewId) {
        String url = baseUrl + "/api/v1/review/" + reviewId + "/progress";
        ResponseEntity<ReviewProgress> response = restTemplate.getForEntity(
            url, ReviewProgress.class
        );
        return response.getBody();
    }
}
```

### 3. FastAPI 实现

**文件**: `合同审查/app/api/v1/endpoints/review.py`

```python
from fastapi import APIRouter, BackgroundTasks
from app.services.review_service import ReviewService
from app.schemas.review import ReviewRequest, ReviewResponse

router = APIRouter()
review_service = ReviewService()

@router.post("/review", response_model=ReviewResponse)
async def create_review(
    request: ReviewRequest,
    background_tasks: BackgroundTasks
):
    """创建审查任务"""
    review_id = await review_service.create_review(request)
    # 后台执行审查
    background_tasks.add_task(
        review_service.execute_review, review_id
    )
    return ReviewResponse(review_id=review_id)

@router.get("/review/{review_id}/progress")
async def get_progress(review_id: str):
    """获取审查进度"""
    return await review_service.get_progress(review_id)

@router.get("/review/{review_id}/result")
async def get_result(review_id: str):
    """获取审查结果"""
    return await review_service.get_result(review_id)
```

## 配置说明

### SpringBoot 配置 (`application.yml`)

```yaml
server:
  port: 8080
  servlet:
    context-path: /api

spring:
  datasource:
    url: jdbc:mysql://localhost:3306/contract_review?useUnicode=true&characterEncoding=utf8&serverTimezone=Asia/Shanghai
    username: root
    password: ${MYSQL_PASSWORD}
    driver-class-name: com.mysql.cj.jdbc.Driver
    hikari:
      minimum-idle: 5
      maximum-pool-size: 20
      connection-timeout: 30000
  
  redis:
    host: localhost
    port: 6379
    database: 0
    password: ${REDIS_PASSWORD}
    timeout: 6000ms
    lettuce:
      pool:
        max-active: 8
        max-idle: 8
        min-idle: 0

# FastAPI 服务配置
fastapi:
  base-url: ${FASTAPI_BASE_URL:http://localhost:8001}
  api-prefix: /api/v1
  timeout: 30000
  connect-timeout: 5000

# JWT 配置
jwt:
  secret: ${JWT_SECRET}
  expiration: 86400000  # 24小时

# 文件上传配置
upload:
  max-file-size: 50MB
  max-request-size: 100MB
  allowed-types: pdf,docx,doc
  storage-path: ./uploads
```

可以通过环境变量配置：
- `FASTAPI_BASE_URL`: FastAPI 服务地址
- `MYSQL_PASSWORD`: MySQL 密码
- `REDIS_PASSWORD`: Redis 密码
- `JWT_SECRET`: JWT 密钥

## 数据流转

### 发起审查流程

```
1. 前端点击"开始审查"按钮
   │
2. 前端发送 POST /api/review/start 到 SpringBoot
   │
3. SpringBoot 调用 ReviewService.startReview()
   │
4. SpringBoot 通过 FastApiClient 转发请求到 FastAPI
   │
5. FastAPI 创建审查任务，返回 reviewId
   │
6. SpringBoot 保存审查记录到数据库
   │
7. SpringBoot 返回结果给前端
```

### 进度推送流程

```
1. 前端建立 SSE 连接 GET /api/review/{reviewId}/progress
   │
2. SpringBoot 创建 SseEmitter，启动定时任务轮询 FastAPI
   │
3. SpringBoot 每 2 秒调用 FastAPI 获取进度
   │
4. SpringBoot 将进度通过 SSE 推送给前端
   │
5. 前端实时更新进度条
   │
6. 审查完成后关闭 SSE 连接
```

### 数据实体关系

```
User (1) ───< (N) Contract (1) ───< (N) ReviewTask
                                            │
                                            ├──> (N) RiskItem
                                            │
                                            └──> (1) Report
```

## 部署架构

### 开发环境

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Vue Dev   │      │  SpringBoot │      │   FastAPI   │
│   :3000     │<────>│   :8080     │<────>│   :8001     │
└─────────────┘      └──────┬──────┘      └─────────────┘
                            │
                     ┌──────┴──────┐
                     │   MySQL     │
                     │   Redis     │
                     └─────────────┘
```

### 生产环境

```
                              ┌─────────────┐
                              │    CDN      │
                              │  (静态资源)  │
                              └──────┬──────┘
                                     │
┌─────────────┐      ┌───────────────┼───────────────┐      ┌─────────────┐
│   Nginx     │      │               │               │      │   Nginx     │
│  (负载均衡)  │<────>│  SpringBoot   │<─────────────>│<────>│  (反向代理)  │
│             │      │   Cluster     │               │      │             │
└─────────────┘      └───────┬───────┘               │      └──────┬──────┘
                             │                       │             │
                      ┌──────┴──────┐               │      ┌──────┴──────┐
                      │   MySQL     │               │      │   FastAPI   │
                      │   (主从)     │               │      │   Cluster   │
                      │   Redis     │               │      │             │
                      │  (Sentinel) │               │      │  ChromaDB   │
                      └─────────────┘               │      └─────────────┘
                                                    │
                                            ┌───────┴───────┐
                                            │  阿里云 OSS   │
                                            │  (文件存储)   │
                                            └───────────────┘
```

### Docker 部署

```yaml
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: contract_review
    volumes:
      - mysql_data:/var/lib/mysql
    networks:
      - contract-network

  redis:
    image: redis:7.0-alpine
    volumes:
      - redis_data:/data
    networks:
      - contract-network

  springboot:
    build: ./ContractReview
    environment:
      SPRING_PROFILES_ACTIVE: prod
      SPRING_DATASOURCE_URL: jdbc:mysql://mysql:3306/contract_review
      SPRING_REDIS_HOST: redis
      FASTAPI_BASE_URL: http://fastapi:8001
    depends_on:
      - mysql
      - redis
    networks:
      - contract-network

  fastapi:
    build: ./合同审查
    environment:
      MYSQL_HOST: mysql
      REDIS_HOST: redis
      DASHSCOPE_API_KEY: ${DASHSCOPE_API_KEY}
    volumes:
      - ./uploads:/app/uploads
      - ./vector_store:/app/vector_store
    depends_on:
      - mysql
      - redis
    networks:
      - contract-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./frontend/dist:/usr/share/nginx/html
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - springboot
      - fastapi
    networks:
      - contract-network

volumes:
  mysql_data:
  redis_data:

networks:
  contract-network:
    driver: bridge
```

## 安全设计

### 认证流程

```
1. 用户登录
   └── 验证用户名密码
   └── 生成 JWT Token (包含用户ID、角色、过期时间)
   └── 返回 Token 给前端

2. 请求验证
   └── 前端在 Header 中携带 Token
   └── SpringBoot 拦截器验证 Token 有效性
   └── 解析 Token 获取用户信息
   └── 检查用户权限
   └── 允许或拒绝请求

3. Token 刷新
   └── Token 过期前自动刷新
   └── 刷新 Token 和 Access Token 双 Token 机制
```

### 数据安全

| 层面 | 措施 |
|------|------|
| 传输安全 | HTTPS/TLS 加密传输 |
| 密码安全 | BCrypt 哈希存储 |
| 数据脱敏 | 敏感字段脱敏展示 |
| SQL 注入 | MyBatis 参数化查询 |
| XSS 攻击 | 输入过滤、输出转义 |
| CSRF 防护 | Token 验证、SameSite Cookie |
| 文件安全 | 类型检查、大小限制、病毒扫描 |

## 性能优化

### 前端优化

- **代码分割**: 路由懒加载
- **资源压缩**: Gzip/Brotli 压缩
- **缓存策略**: 静态资源长期缓存
- **CDN 加速**: 静态资源 CDN 分发

### 后端优化

- **连接池**: HikariCP 数据库连接池
- **缓存策略**:
  - Redis 缓存热点数据
  - Caffeine 本地缓存配置信息
- **异步处理**:
  - @Async 异步方法
  - 消息队列处理耗时任务
- **分页查询**: 大数据量分页加载

### AI 服务优化

- **向量索引**: HNSW 近似最近邻搜索
- **批处理**: 批量向量计算
- **缓存**: 相似查询结果缓存
- **流式响应**: SSE 实时推送进度

## 监控与日志

### 日志收集

```yaml
# 日志级别
logging:
  level:
    root: INFO
    com.example.contractreview: DEBUG
    org.springframework.web: WARN
  pattern:
    console: "%d{yyyy-MM-dd HH:mm:ss} [%thread] %-5level %logger{36} - %msg%n"
  file:
    name: logs/application.log
```

### 监控指标

| 指标 | 说明 |
|------|------|
| JVM 内存使用 | 堆内存、非堆内存 |
| 数据库连接池 | 活跃连接数、空闲连接数 |
| API 响应时间 | P50、P95、P99 |
| 错误率 | 5xx 错误占比 |
| AI 服务响应 | 审查耗时、成功率 |

## 扩展性设计

### 水平扩展

- **无状态设计**: SpringBoot 服务无状态，支持多实例部署
- **负载均衡**: Nginx 轮询或一致性哈希
- **Session 共享**: Redis 分布式会话

### 功能扩展

- **插件化设计**: AI 模型可插拔，支持多种 LLM
- **模块化架构**: 各模块独立开发、独立部署
- **配置化**: 功能开关通过配置控制

## 待完善项

1. **高可用**: 
   - [ ] MySQL 主从复制
   - [ ] Redis Sentinel 集群
   - [ ] 服务健康检查

2. **性能优化**:
   - [ ] 审查结果缓存
   - [ ] 热点数据预热
   - [ ] 数据库读写分离

3. **安全增强**:
   - [ ] API 限流防刷
   - [ ] 敏感数据加密
   - [ ] 操作审计日志

4. **运维支持**:
   - [ ] 分布式链路追踪
   - [ ] 自动化部署流水线
   - [ ] 监控告警系统
