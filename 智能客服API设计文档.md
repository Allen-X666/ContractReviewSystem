# 智能客服后端 API 设计文档

## 一、整体设计说明

### 1.1 设计目标

将现有纯前端实现的智能客服功能迁移为前后端分离架构：
- **对话数据**持久化存储到数据库（MySQL），支持多端同步
- **AI 回复**由后端统一处理，便于后续接入 LLM 大模型
- **浮动按钮位置**等 UI 状态仍保留在前端 sessionStorage
- **直接对话体验**：用户发送消息时自动创建对话，无需手动创建

### 1.2 技术栈

| 层级 | 技术方案 |
|------|----------|
| 后端框架 | SpringBoot 3.x |
| 持久层 | MyBatis + MySQL |
| 缓存层 | Redis（可选，用于会话消息缓存和频控） |
| AI 接入 | SpringBoot 关键词匹配（初期）→ FastAPI LLM 服务（后续） |
| 前端框架 | Vue3 + Pinia + Element Plus |
| 请求工具 | `@/utils/request`（Axios 封装） |

### 1.3 项目约定

- 接口前缀：`/api/chatbot`（SpringBoot context-path 为 `/api`）
- 统一响应格式：`Result<T>`（code / message / data / total / timestamp）
- 认证方式：`Authorization: Bearer {token}`（复用现有 JWT 认证体系）
- 数据库表命名：`chatbot_conversation`、`chatbot_message`，字段小写下划线

---

## 二、数据模型设计

### 2.1 数据库表结构

#### 2.1.1 对话表 `chatbot_conversation`

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | BIGINT | PK, AUTO_INCREMENT | 对话ID |
| user_id | BIGINT | NOT NULL, FK → user.id | 所属用户ID |
| name | VARCHAR(100) | NOT NULL, DEFAULT '新对话' | 对话名称 |
| status | TINYINT | NOT NULL, DEFAULT 1 | 状态：1-正常 0-已删除 |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP ON UPDATE | 最后更新时间 |

**索引设计：**
- `idx_chatbot_conv_user_id`：`user_id` — 按用户查询对话列表
- `idx_chatbot_conv_updated_at`：`updated_at` — 按更新时间排序

```sql
CREATE TABLE chatbot_conversation (
    id          BIGINT       NOT NULL AUTO_INCREMENT COMMENT '对话ID',
    user_id     BIGINT       NOT NULL COMMENT '所属用户ID',
    name        VARCHAR(100) NOT NULL DEFAULT '新对话' COMMENT '对话名称',
    status      TINYINT      NOT NULL DEFAULT 1 COMMENT '状态：1-正常 0-已删除',
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (id),
    INDEX idx_chatbot_conv_user_id (user_id),
    INDEX idx_chatbot_conv_updated_at (updated_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='智能客服对话表';
```

#### 2.1.2 消息表 `chatbot_message`

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | BIGINT | PK, AUTO_INCREMENT | 消息ID |
| conversation_id | BIGINT | NOT NULL, FK → chatbot_conversation.id | 所属对话ID |
| role | VARCHAR(20) | NOT NULL | 角色：user / assistant / system |
| content | TEXT | NOT NULL | 消息内容（支持 Markdown） |
| created_at | DATETIME | NOT NULL, DEFAULT CURRENT_TIMESTAMP | 创建时间 |

**索引设计：**
- `idx_chatbot_msg_conv_id`：`conversation_id` — 按对话查询消息列表
- `idx_chatbot_msg_created_at`：`created_at` — 按时间排序

```sql
CREATE TABLE chatbot_message (
    id              BIGINT      NOT NULL AUTO_INCREMENT COMMENT '消息ID',
    conversation_id BIGINT      NOT NULL COMMENT '所属对话ID',
    role            VARCHAR(20) NOT NULL COMMENT '角色：user/assistant/system',
    content         TEXT        NOT NULL COMMENT '消息内容',
    created_at      DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (id),
    INDEX idx_chatbot_msg_conv_id (conversation_id),
    INDEX idx_chatbot_msg_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='智能客服消息表';
```

### 2.2 后端实体类（参考）

#### ChatbotConversation

```java
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ChatbotConversation {
    private Long id;
    private Long userId;
    private String name;
    private Integer status;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
```

#### ChatbotMessage

```java
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ChatbotMessage {
    private Long id;
    private Long conversationId;
    private String role;       // "user" | "assistant" | "system"
    private String content;
    private LocalDateTime createdAt;
}
```

### 2.3 VO / DTO 定义

#### ChatbotConversationVO（对话列表项）

```java
@Data
public class ChatbotConversationVO {
    private Long id;
    private String name;
    private Integer messageCount;
    private String lastMessage;      // 最后一条消息预览（截取前50字符）
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
```

#### ChatbotConversationDetailVO（对话详情，含消息列表）

```java
@Data
public class ChatbotConversationDetailVO {
    private Long id;
    private String name;
    private List<ChatbotMessageVO> messages;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
```

#### ChatbotMessageVO（消息）

```java
@Data
public class ChatbotMessageVO {
    private Long id;
    private String role;
    private String content;
    private LocalDateTime createdAt;
}
```

#### ChatbotSendDTO（发送消息请求）

```java
@Data
public class ChatbotSendDTO {
    private Long conversationId;  // 可选，为空时自动创建新对话

    @NotBlank(message = "消息内容不能为空")
    @Size(max = 2000, message = "消息内容不能超过2000字")
    private String content;
}
```

#### ChatbotCreateDTO（创建对话请求）

```java
@Data
public class ChatbotCreateDTO {
    @Size(max = 100, message = "对话名称不能超过100字")
    private String name;  // 可选，默认"新对话"
}
```

#### ChatbotRenameDTO（重命名对话请求）

```java
@Data
public class ChatbotRenameDTO {
    @NotBlank(message = "名称不能为空")
    @Size(max = 100, message = "对话名称不能超过100字")
    private String name;
}
```

#### ChatbotReplyVO（AI 回复结果）

```java
@Data
public class ChatbotReplyVO {
    private Long conversationId;       // 对话ID（新建时返回新ID）
    private String conversationName;   // 对话名称（新建时返回默认名）
    private ChatbotMessageVO userMessage;
    private ChatbotMessageVO assistantMessage;
}
```

---

## 三、后端 API 接口设计

### 3.1 接口总览

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/chatbot/conversations` | 获取对话列表 | 需要 |
| GET | `/chatbot/conversations/{id}` | 获取对话详情（含消息） | 需要 |
| PUT | `/chatbot/conversations/{id}/name` | 重命名对话 | 需要 |
| DELETE | `/chatbot/conversations/{id}` | 删除对话 | 需要 |
| POST | `/chatbot/messages` | 发送消息并获取 AI 回复（支持自动创建对话） | 需要 |
| GET | `/chatbot/conversations/{id}/export` | 导出对话记录为 Excel 文件 | 需要 |

> **使用方式**：前端直接使用 `POST /chatbot/messages` 发送消息，无需先创建对话。当 `conversationId` 为空时，后端会自动创建新对话并在响应中返回 `conversationId` 和 `conversationName`。

### 3.2 接口详细定义

#### 3.2.1 获取对话列表

**GET** `/api/chatbot/conversations`

**请求头：**
```
Authorization: Bearer {token}
```

**查询参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | Integer | 否 | 1 | 页码 |
| pageSize | Integer | 否 | 50 | 每页条数 |

**响应（200）：**
```json
{
    "code": 200,
    "message": "success",
    "data": [
        {
            "id": 2,
            "name": "合同审查问题",
            "messageCount": 5,
            "lastMessage": "好的，我了解了...",
            "createdAt": "2026-05-10T11:00:00",
            "updatedAt": "2026-05-10T11:30:00"
        },
        {
            "id": 1,
            "name": "新对话",
            "messageCount": 1,
            "lastMessage": "您好！我是智能客服助手...",
            "createdAt": "2026-05-10T10:30:00",
            "updatedAt": "2026-05-10T10:30:00"
        }
    ],
    "total": 2,
    "timestamp": 1746863400000
}
```

**业务逻辑：**
1. 根据当前用户 ID 查询对话列表
2. 按 `updated_at` 降序排列
3. 关联查询每个对话的消息数量和最后一条消息预览

---

#### 3.2.2 获取对话详情

**GET** `/api/chatbot/conversations/{id}`

**请求头：**
```
Authorization: Bearer {token}
```

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | Long | 对话ID |

**查询参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | Integer | 否 | 1 | 消息页码 |
| pageSize | Integer | 否 | 100 | 每页消息条数 |

**响应（200）：**
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "id": 1,
        "name": "合同审查问题",
        "messages": [
            {
                "id": 1,
                "role": "assistant",
                "content": "您好！我是智能客服助手，可以为您解答关于合同审查系统的各种问题。请问有什么可以帮助您的？",
                "createdAt": "2026-05-10T10:30:00"
            },
            {
                "id": 2,
                "role": "user",
                "content": "合同审查的流程是什么？",
                "createdAt": "2026-05-10T10:31:00"
            },
            {
                "id": 3,
                "role": "assistant",
                "content": "您好！关于合同审查，系统支持以下功能：\n\n1. **上传合同** - 支持 PDF、Word 格式\n2. **风险识别** - 自动检测合同中的风险条款\n...",
                "createdAt": "2026-05-10T10:31:05"
            }
        ],
        "createdAt": "2026-05-10T10:30:00",
        "updatedAt": "2026-05-10T10:31:05"
    },
    "total": 3,
    "timestamp": 1746863400000
}
```

**业务逻辑：**
1. 验证对话归属当前用户
2. 查询对话基本信息和消息列表
3. 消息按 `created_at` 升序排列

---

#### 3.2.4 重命名对话

**PUT** `/api/chatbot/conversations/{id}/name`

**请求头：**
```
Authorization: Bearer {token}
```

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | Long | 对话ID |

**请求体：**
```json
{
    "name": "关于合同审查流程的讨论"
}
```

**响应（200）：**
```json
{
    "code": 200,
    "message": "success",
    "data": null,
    "timestamp": 1746863400000
}
```

**业务逻辑：**
1. 验证对话归属当前用户
2. 更新对话名称

---

#### 3.2.5 删除对话

**DELETE** `/api/chatbot/conversations/{id}`

**请求头：**
```
Authorization: Bearer {token}
```

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | Long | 对话ID |

**响应（200）：**
```json
{
    "code": 200,
    "message": "success",
    "data": null,
    "timestamp": 1746863400000
}
```

**业务逻辑：**
1. 验证对话归属当前用户
2. 逻辑删除对话（status 设为 0）
3. 关联消息无需单独处理（查询时通过 status 过滤）

---

#### 3.2.6 导出对话记录为 Excel

**GET** `/api/chatbot/conversations/{id}/export`

**请求头：**
```
Authorization: Bearer {token}
```

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | Long | 对话ID |

**响应（200）：**

直接返回 Excel 文件流（`.xlsx` 格式），响应头如下：

```
Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
Content-Disposition: attachment; filename="对话记录_{对话名称}.xlsx"
```

**Excel 表格结构：**

| 列名 | 说明 | 数据来源 |
|------|------|----------|
| 序号 | 消息序号，从 1 开始 | 自增 |
| 角色 | 用户 / AI助手 / 系统 | `role` 字段映射 |
| 消息内容 | 完整消息文本 | `content` 字段 |
| 发送时间 | 格式化时间 `yyyy-MM-dd HH:mm:ss` | `created_at` 字段 |

**业务逻辑：**
1. 验证对话归属当前用户
2. 查询该对话下所有消息（按 `created_at` 升序）
3. 生成 Excel 文件并以流式响应返回
4. 文件名为 `对话记录_{对话名称}.xlsx`，中文名需 URL 编码

**前端调用方式：**
```javascript
// 前端使用 Blob + <a> 下载
const blob = await fetch(`/api/chatbot/conversations/${id}/export`, {
  headers: { 'Authorization': `Bearer ${token}` }
}).then(res => res.blob())
const url = URL.createObjectURL(blob)
const a = document.createElement('a')
a.href = url
a.download = `对话记录.xlsx`
a.click()
URL.revokeObjectURL(url)
```

---

#### 3.2.7 发送消息并获取 AI 回复（支持自动创建对话）

**POST** `/api/chatbot/messages`

**请求头：**
```
Authorization: Bearer {token}
```

**请求体：**
```json
{
    "conversationId": null,
    "content": "合同审查的流程是什么？"
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| conversationId | Long | 否 | 对话ID，为空或不传时自动创建新对话 |
| content | String | 是 | 消息内容（不超过2000字） |

**响应（200）：**
```json
{
    "code": 200,
    "message": "success",
    "data": {
        "conversationId": 1,
        "conversationName": "合同审查的流程是什么",
        "userMessage": {
            "id": 1,
            "role": "user",
            "content": "合同审查的流程是什么？",
            "createdAt": "2026-05-10T12:00:00"
        },
        "assistantMessage": {
            "id": 2,
            "role": "assistant",
            "content": "您好！关于合同审查，系统支持以下功能：\n\n1. **上传合同** - 支持 PDF、Word 格式\n2. **风险识别** - 自动检测合同中的风险条款\n3. **合规检查** - 对照法律法规进行合规性分析\n4. **审查报告** - 生成详细的审查报告\n\n您可以通过顶部的\"上传合同\"按钮开始使用。",
            "createdAt": "2026-05-10T12:00:01"
        }
    },
    "timestamp": 1746863400000
}
```

**业务逻辑：**
1. 从 Token 解析当前用户 ID
2. **若 conversationId 为空**：自动创建新对话，name 默认以用户消息前 20 字符命名
3. 验证对话归属当前用户
4. 插入用户消息记录
5. 更新对话的 `updated_at`
6. 若对话名称仍为"新对话"且消息数 ≤ 3，则以用户消息截取前 20 字符更新对话名称
7. 调用 AI 回复服务生成回复内容（关键词匹配 → 后续可替换为 LLM）
8. 插入 AI 回复消息记录
9. 返回 `conversationId`、`conversationName`、用户消息和 AI 回复的完整信息

---

## 四、AI 回复策略

### 4.1 初期方案：后端关键词匹配

在 SpringBoot Service 层实现关键词匹配逻辑，规则与现有前端一致：

| 关键词 | 回复主题 |
|--------|----------|
| 合同、审查、审核 | 系统功能介绍（上传、风险识别、合规检查、审查报告） |
| 上传、文件、格式 | 文件上传要求说明 |
| 风险、风险项、风险等级 | 风险等级说明（高/中/低） |
| 知识库、法律、法规 | 法律知识库介绍 |
| 报告、导出、下载 | 报告导出说明 |
| 密码、修改、设置 | 个人信息修改指引 |
| 你好、您好、hi、hello | 欢迎语 |
| 谢谢、感谢、thanks | 礼貌回复 |
| （无匹配） | 默认功能指引 |

### 4.2 后续升级方案：接入 LLM

当需要将关键词匹配升级为真正的 AI 对话时，改造方案如下：

1. **新建 FastAPI 接口** `/api/v1/chatbot/reply`
2. **SpringBoot 调用** FastAPI 接口获取 AI 回复
3. **LLM 输入**：系统提示词 + 对话历史（取最近 N 条消息） + 用户当前消息
4. **流式响应**（可选）：通过 SSE 实现打字机效果

```java
// 后续 LLM 接入示意
public ChatbotMessageVO generateAIReply(Long conversationId, String userMessage) {
    // 1. 获取最近 10 条对话历史
    List<ChatbotMessage> history = chatbotMessageMapper.selectRecentByConversationId(conversationId, 10);
    
    // 2. 构造 LLM 请求
    String systemPrompt = "你是智能合同审查助手，专门解答关于合同审查系统使用的问题...";
    
    // 3. 调用 FastAPI
    FastApiResult<String> result = fastApiClient.chatCompletion(systemPrompt, history, userMessage);
    
    // 4. 返回 AI 回复
    return result.getData();
}
```

---

## 五、频率控制（可选）

为防止用户恶意刷接口，可在 Redis 中增加频率控制：

- **发送消息接口**：同一用户 10 秒内最多 10 条消息
- **创建对话接口**：同一用户 1 分钟内最多创建 5 个对话

```java
// Redis Key 设计
chatbot:rate:{userId}:messages    → 滑动窗口计数，10秒过期
chatbot:rate:{userId}:conversations → 滑动窗口计数，60秒过期
```

---

## 六、前端改造方案

### 6.1 核心理念：直接对话

用户打开智能客服面板后，直接在输入框输入消息即可开始对话，无需手动创建对话。首次发送消息时，前端调用 `POST /chatbot/messages`（不传 `conversationId`），后端自动创建对话并返回 `conversationId`，前端记录该 ID 用于后续消息。

**用户流程**：
```
打开面板 → 直接输入消息 → 发送（自动创建对话）→ 收到回复 → 继续对话
                                    ↑
                          后端返回 conversationId，前端记住
```

### 6.2 变更范围

| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `frontend/src/api/chatbot.js` | **改造** | `sendMessage` 的 `conversationId` 改为可选 |
| `frontend/src/stores/chatbot.js` | **改造** | 移除自动创建对话逻辑，首次发消息时直接调用 sendMessage |
| `frontend/src/components/ChatBot/ChatPanel.vue` | **改造** | 发送消息时无需确保对话存在 |
| `frontend/src/components/ChatBot/ChatBot.vue` | **改造** | 打开面板时无需自动创建对话，加载历史列表即可 |

### 6.3 前端 API 封装（chatbot.js）

```javascript
import { get, post, put, del } from '@/utils/request'

// 创建新对话（保留，供历史记录中手动创建使用）
export function createConversation(name) {
  return post('/chatbot/conversations', { name })
}

// 获取对话列表
export function getConversationList(params) {
  return get('/chatbot/conversations', params)
}

// 获取对话详情（含消息列表）
export function getConversationDetail(id, params) {
  return get(`/chatbot/conversations/${id}`, params)
}

// 重命名对话
export function renameConversation(id, name) {
  return put(`/chatbot/conversations/${id}/name`, { name })
}

// 删除对话
export function deleteConversation(id) {
  return del(`/chatbot/conversations/${id}`)
}

// 发送消息并获取 AI 回复（conversationId 可选，为空时自动创建对话）
export function sendMessage(content, conversationId) {
  const data = { content }
  if (conversationId) {
    data.conversationId = conversationId
  }
  return post('/chatbot/messages', data)
}
```

### 6.4 Store 改造要点

| 原有逻辑 | 改造后 |
|----------|--------|
| 打开面板时自动调用 `createConversation()` | 打开面板时仅加载对话列表，不自动创建 |
| `sendMessage()` 先确保有对话再发送 | `sendMessage()` 直接发送，`conversationId` 可为空 |
| `sendMessage()` 内存 push 消息 | 调用 `POST /chatbot/messages`，返回 userMessage + assistantMessage + conversationId |
| `simulateAIReply()` 前端关键词匹配 | 已集成在 sendMessage 的后端响应中，无需单独调用 |
| `conversations` 从 localStorage 加载 | 首次加载调用 `GET /chatbot/conversations` |
| `currentConversation` 内存查询 | 切换时调用 `GET /chatbot/conversations/{id}` 获取消息列表 |
| `exportConversationToExcel()` 纯前端 | 保持前端导出（数据已从 API 加载到内存） |
| `buttonPosition` sessionStorage | 保持不变（纯 UI 状态） |

### 6.5 前端关键改造点

#### 6.5.1 Store - sendMessage 方法

```javascript
async function sendMessage(content) {
  try {
    sending.value = true
    const res = await chatbotApi.sendMessage(content, currentConversationId.value)
    const replyData = res.data

    const userMsg = normalizeMessage(replyData.userMessage)
    const assistantMsg = normalizeMessage(replyData.assistantMessage)

    // 后端自动创建了对话，更新本地 conversationId
    if (!currentConversationId.value) {
      currentConversationId.value = replyData.conversationId
    }

    // 确保 conversations 列表中有该对话
    let conv = conversations.value.find(c => c.id === replyData.conversationId)
    if (!conv) {
      conv = {
        id: replyData.conversationId,
        name: replyData.conversationName || '新对话',
        messages: [],
        createdAt: assistantMsg.timestamp,
        updatedAt: assistantMsg.timestamp
      }
      conversations.value.unshift(conv)
    }
    conv.messages.push(userMsg, assistantMsg)
    conv.updatedAt = assistantMsg.timestamp
    if (replyData.conversationName) {
      conv.name = replyData.conversationName
    }

    return { userMsg, assistantMsg }
  } finally {
    sending.value = false
  }
}
```

#### 6.5.2 Store - 移除 ensureActiveConversation

不再需要在打开面板时自动创建对话，删除 `ensureActiveConversation` 方法。用户首次发消息时后端自动创建。

#### 6.5.3 ChatBot.vue - 打开面板

```javascript
async function onFabClick() {
  if (hasMoved) return
  panelVisible.value = !panelVisible.value
  if (panelVisible.value) {
    currentView.value = 'chat'
    // 仅加载历史列表，不创建对话
    if (store.conversations.length === 0) {
      await store.loadConversations()
    }
  }
}
```

#### 6.5.4 ChatPanel.vue - 发送消息

```javascript
async function handleSend() {
  const text = inputText.value.trim()
  if (!text || store.sending) return
  inputText.value = ''
  typing.value = true
  await nextTick(scrollToBottom)
  try {
    await store.sendMessage(text)
  } catch {
    /* request.js 统一处理错误提示 */
  } finally {
    typing.value = false
    await nextTick(scrollToBottom)
  }
}
```

---

## 七、后续可扩展方向

| 方向 | 说明 |
|------|------|
| LLM 接入 | 将关键词匹配替换为 FastAPI LLM 服务调用 |
| 流式回复 | SSE 实现打字机效果，提升用户体验 |
| 多轮对话上下文 | 利用消息表中的历史记录作为 LLM 上下文 |
| 会话导出到服务端 | 导出为 PDF 存储到 OSS，生成分享链接 |
| 满意度评价 | 每轮对话结束后用户可评价，用于优化 AI 回复质量 |
| 转人工客服 | 当 AI 无法解答时，支持转接人工客服 |
