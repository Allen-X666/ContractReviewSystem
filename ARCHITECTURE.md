# 合同审查系统架构说明

## 请求链路

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

## 实现说明

### 1. 前端层 (Vue3)

**文件**: `frontend/src/api/review.js`

- 所有审查相关 API 请求发送到 `/api` (SpringBoot)
- SSE 实时进度推送通过 SpringBoot 转发

### 2. SpringBoot 层 (Java)

#### 新增/修改的文件：

| 文件 | 说明 |
|------|------|
| `application.yml` | 添加 FastAPI 服务配置 |
| `FastApiConfig.java` | FastAPI 配置类 |
| `FastApiClient.java` | FastAPI HTTP 客户端 |
| `ReviewController.java` | 添加审查相关 REST 接口 |
| `ReviewService.java` | 服务接口定义 |
| `ReviewServiceImpl.java` | 服务实现，负责转发到 FastAPI |
| `FastApiResult.java` | FastAPI 统一响应包装 |
| `ReviewProgressVO.java` | 审查进度 VO |
| `ReviewResultVO.java` | 审查结果 VO |
| `RiskItemVO.java` | 风险项 VO |

#### 核心接口：

```java
// 发起审查
POST /api/review/start

// 获取审查进度 (SSE)
GET /api/review/{reviewId}/progress

// 获取审查结果
GET /api/review/{reviewId}/result

// 获取风险列表
GET /api/review/{reviewId}/risks

// 重新审查
POST /api/review/{reviewId}/re-review

// 取消审查
POST /api/review/{reviewId}/cancel
```

### 3. FastAPI 层 (Python)

**文件**: `合同审查/app/api/v1/endpoints/review.py`

提供实际的 AI 审查服务：
- 文本解析
- 风险分析
- 结果生成

## 配置说明

### SpringBoot 配置 (`application.yml`)

```yaml
fastapi:
  base-url: ${FASTAPI_BASE_URL:http://localhost:8000}
  api-prefix: /api/v1
  timeout: 30000
  connect-timeout: 5000
```

可以通过环境变量 `FASTAPI_BASE_URL` 配置 FastAPI 服务地址。

## 数据流转

### 发起审查流程

1. **前端** 点击"开始审查"按钮
2. **前端** 发送 POST `/api/review/start` 到 SpringBoot
3. **SpringBoot** 调用 `ReviewService.startReview()`
4. **SpringBoot** 通过 `FastApiClient` 转发请求到 FastAPI
5. **FastAPI** 创建审查任务，返回 reviewId
6. **SpringBoot** 保存审查记录到数据库
7. **SpringBoot** 返回结果给前端

### 进度推送流程

1. **前端** 建立 SSE 连接 `GET /api/review/{reviewId}/progress`
2. **SpringBoot** 创建 `SseEmitter`，启动定时任务轮询 FastAPI
3. **SpringBoot** 每 2 秒调用 FastAPI 获取进度
4. **SpringBoot** 将进度通过 SSE 推送给前端
5. **前端** 实时更新进度条

## 优势

1. **统一入口**: 前端只与 SpringBoot 交互，简化配置
2. **安全控制**: SpringBoot 统一处理认证鉴权
3. **日志追踪**: 可以在 SpringBoot 层记录完整请求链路
4. **服务解耦**: FastAPI 可以独立部署和扩展
5. **数据持久化**: SpringBoot 负责审查记录的持久化存储

## 待完善项

1. 完善 `ReviewMapper` 的数据库操作方法
2. 实现 JWT Token 解析获取用户ID
3. 添加更多的异常处理和重试机制
4. 实现审查结果的缓存机制
