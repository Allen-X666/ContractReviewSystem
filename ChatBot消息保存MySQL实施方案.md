# ChatBot 消息保存到 MySQL 实施方案

## 一、需求分析

在 `ChatBotServiceImpl.java` 中，当调用 FastAPI 获取 AI 回复后，需要将以下内容保存到 MySQL 数据库：

1. **用户消息** - 用户发送的问题
2. **AI 回复** - FastAPI 返回的 AI 回答

## 二、现有数据结构

### 2.1 数据库表结构

#### chatbot_conversation 表（对话表）
```sql
CREATE TABLE chatbot_conversation (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '对话ID',
    user_id BIGINT NOT NULL COMMENT '所属用户ID',
    name VARCHAR(255) COMMENT '对话名称',
    status TINYINT DEFAULT 1 COMMENT '状态：1-正常 0-已删除',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
);
```

#### chatbot_message 表（消息表）
```sql
CREATE TABLE chatbot_message (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '消息ID',
    conversation_id BIGINT NOT NULL COMMENT '所属对话ID',
    role VARCHAR(20) NOT NULL COMMENT '角色：user/assistant/system',
    content TEXT COMMENT '消息内容',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间'
);
```

### 2.2 实体类

#### ChatbotConversation.java
```java
package com.example.contractreview.model.entity;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.time.LocalDateTime;

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

#### ChatbotMessage.java
```java
package com.example.contractreview.model.entity;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.time.LocalDateTime;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ChatbotMessage {
    private Long id;
    private Long conversationId;
    private String role;
    private String content;
    private LocalDateTime createdAt;
}
```

## 三、实施方案

### 方案一：同步调用 + 数据库存储（推荐用于 sendMessage 方法）

适用于非流式接口，可以完整获取 AI 回复后统一保存。

#### 3.1 新增 Mapper 接口方法

**ChatMapper.java** 新增以下方法：

```java
package com.example.contractreview.mapper;

import com.example.contractreview.model.entity.ChatbotConversation;
import com.example.contractreview.model.entity.ChatbotMessage;
import com.example.contractreview.model.vo.ChatDetailVO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface ChatMapper {

    // 获取聊天详情
    List<ChatDetailVO> getChatDetail(@Param("id") Integer id, @Param("userId") Integer userId);
    
    // ==================== 新增方法 ====================
    
    /**
     * 插入对话
     * @param conversation 对话实体
     * @return 影响行数
     */
    int insertConversation(@Param("conversation") ChatbotConversation conversation);
    
    /**
     * 插入消息
     * @param message 消息实体
     * @return 影响行数
     */
    int insertMessage(@Param("message") ChatbotMessage message);
    
    /**
     * 更新对话名称
     * @param conversationId 对话ID
     * @param name 对话名称
     * @return 影响行数
     */
    int updateConversationName(@Param("conversationId") Long conversationId, @Param("name") String name);
    
    /**
     * 根据ID查询对话
     * @param conversationId 对话ID
     * @return 对话实体
     */
    ChatbotConversation selectConversationById(@Param("conversationId") Long conversationId);
}
```

#### 3.2 新增 Mapper XML

**ChatMapper.xml** 新增以下 SQL：

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE mapper PUBLIC "-//mybatis.org//DTD Mapper 3.0//EN" "http://mybatis.org/dtd/mybatis-3.0-mapper.dtd">
<mapper namespace="com.example.contractreview.mapper.ChatMapper">

    <select id="getChatDetail" resultType="com.example.contractreview.model.vo.ChatDetailVO">
        select
            cm.id, cm.role, cm.content, cm.created_at as createTime
        from
            chatbot_message cm
        left join chatbot_conversation cc on cm.conversation_id = cc.id
        where cm.conversation_id = #{id} and cc.user_id = #{userId}
    </select>
    
    <!-- ==================== 新增SQL ==================== -->
    
    <!-- 插入对话 -->
    <insert id="insertConversation" useGeneratedKeys="true" keyProperty="conversation.id">
        INSERT INTO chatbot_conversation (
            user_id, name, status, created_at, updated_at
        ) VALUES (
            #{conversation.userId},
            #{conversation.name},
            #{conversation.status},
            #{conversation.createdAt},
            #{conversation.updatedAt}
        )
    </insert>
    
    <!-- 插入消息 -->
    <insert id="insertMessage" useGeneratedKeys="true" keyProperty="message.id">
        INSERT INTO chatbot_message (
            conversation_id, role, content, created_at
        ) VALUES (
            #{message.conversationId},
            #{message.role},
            #{message.content},
            #{message.createdAt}
        )
    </insert>
    
    <!-- 更新对话名称 -->
    <update id="updateConversationName">
        UPDATE chatbot_conversation
        SET name = #{name}, updated_at = NOW()
        WHERE id = #{conversationId}
    </update>
    
    <!-- 根据ID查询对话 -->
    <select id="selectConversationById" resultType="com.example.contractreview.model.entity.ChatbotConversation">
        SELECT * FROM chatbot_conversation WHERE id = #{conversationId}
    </select>

</mapper>
```

#### 3.3 修改 ChatBotServiceImpl.java

**sendMessage 方法改造**：

```java
@Service
@Slf4j
@RequiredArgsConstructor
public class ChatBotServiceImpl implements ChatBotService {

    private final ChatBotClient chatBotClient;
    private final StringRedisTemplate stringRedisTemplate;
    private final ChatMapper chatMapper;
    private final ObjectMapper objectMapper;
    private final TokenUtils tokenUtils;  // 需要注入TokenUtils获取userId

    /**
     * 发送消息（同步版本）- 改造后
     */
    @Override
    @Transactional  // 添加事务注解
    public Result<ChatbotReplyVO> sendMessage(String authorization, ChatbotCreateDTO chatbotCreateDTO) {
        log.info("发送消息：{}", chatbotCreateDTO);
        
        // 1. 获取当前用户ID
        Integer userId = tokenUtils.getUserId(authorization);
        if (userId == null) {
            return Result.error(ResultCode.UNAUTHORIZED.getCode(), "用户认证信息无效");
        }
        
        Integer conversationId = chatbotCreateDTO.getConversationId();
        String userMessage = chatbotCreateDTO.getContent();
        
        // 2. 处理对话ID（如果是新对话，需要创建）
        Long finalConversationId;
        boolean isNewConversation = false;
        
        if (conversationId == null) {
            // 2.1 创建新对话
            ChatbotConversation conversation = ChatbotConversation.builder()
                    .userId(userId.longValue())
                    .name(userMessage.length() > 20 ? userMessage.substring(0, 20) + "..." : userMessage)
                    .status(1)
                    .createdAt(LocalDateTime.now())
                    .updatedAt(LocalDateTime.now())
                    .build();
            
            chatMapper.insertConversation(conversation);
            finalConversationId = conversation.getId();
            isNewConversation = true;
            log.info("创建新对话，conversationId: {}", finalConversationId);
        } else {
            finalConversationId = conversationId.longValue();
            // 验证对话是否属于当前用户
            ChatbotConversation conversation = chatMapper.selectConversationById(finalConversationId);
            if (conversation == null || !conversation.getUserId().equals(userId.longValue())) {
                return Result.error(ResultCode.FORBIDDEN.getCode(), "无权访问该对话");
            }
        }
        
        // 3. 保存用户消息到数据库
        ChatbotMessage userChatMessage = ChatbotMessage.builder()
                .conversationId(finalConversationId)
                .role("user")
                .content(userMessage)
                .createdAt(LocalDateTime.now())
                .build();
        chatMapper.insertMessage(userChatMessage);
        log.info("保存用户消息，messageId: {}", userChatMessage.getId());
        
        // 4. 调用 FastAPI 获取 AI 回复
        String aiResponse;
        try {
            aiResponse = chatBotClient.sendMessage(userMessage);
        } catch (Exception e) {
            log.error("调用 FastAPI 失败: {}", e.getMessage(), e);
            return Result.error(ResultCode.SERVICE_ERROR.getCode(), "AI 服务调用失败");
        }
        
        // 5. 保存 AI 回复到数据库
        ChatbotMessage aiChatMessage = ChatbotMessage.builder()
                .conversationId(finalConversationId)
                .role("assistant")
                .content(aiResponse)
                .createdAt(LocalDateTime.now())
                .build();
        chatMapper.insertMessage(aiChatMessage);
        log.info("保存AI回复，messageId: {}", aiChatMessage.getId());
        
        // 6. 更新对话时间
        if (!isNewConversation) {
            chatMapper.updateConversationName(finalConversationId, null);  // 只更新时间
        }
        
        // 7. 清除 Redis 缓存（如果存在）
        String cacheKey = UserConstant.CHAT_DETAIL + finalConversationId;
        stringRedisTemplate.delete(cacheKey);
        
        // 8. 构建返回结果
        ChatbotReplyVO replyVO = new ChatbotReplyVO();
        replyVO.setConversationId(finalConversationId.intValue());
        replyVO.setContent(aiResponse);
        replyVO.setMessageId(aiChatMessage.getId().intValue());
        
        return Result.success(replyVO);
    }
}
```

---

### 方案二：流式调用 + 数据库存储（适用于 streamMessage 方法）

流式接口需要特殊处理，因为 AI 回复是分段返回的。

#### 4.1 新增用于收集流式响应的包装类

```java
/**
 * 流式响应收集器
 * 用于收集 SSE 流式响应的完整内容
 */
@Component
public class StreamingResponseCollector {
    
    private final StringBuilder contentBuilder = new StringBuilder();
    
    /**
     * 处理 SSE 数据行
     * @param line SSE 数据行
     */
    public void processLine(String line) {
        if (line.startsWith("data: ")) {
            String data = line.substring(6);
            if (!"[DONE]".equals(data)) {
                try {
                    // 解析 JSON 提取 content
                    JsonNode node = new ObjectMapper().readTree(data);
                    if (node.has("content")) {
                        contentBuilder.append(node.get("content").asText());
                    }
                } catch (Exception e) {
                    // 如果不是 JSON 格式，直接追加
                    contentBuilder.append(data);
                }
            }
        }
    }
    
    /**
     * 获取完整内容
     */
    public String getFullContent() {
        return contentBuilder.toString();
    }
}
```

#### 4.2 改造 ChatBotClient 支持回调

```java
@Component
public class ChatBotClient {

    // ... 原有代码 ...

    /**
     * 流式发送消息（带回调版本）
     * @param content 用户消息
     * @param outputStream 输出流（给前端）
     * @param onComplete 完成回调，接收完整 AI 回复
     */
    public void streamMessageWithCallback(
            String content, 
            OutputStream outputStream,
            Consumer<String> onComplete
    ) {
        StringBuilder fullResponse = new StringBuilder();
        
        if (content != null) {
            try (InputStream responseStream = streamingRestClient.post()
                    .uri("/chatbot/send")
                    .contentType(MediaType.TEXT_PLAIN)
                    .body(content)
                    .retrieve()
                    .body(InputStream.class)) {
                
                if (responseStream == null) {
                    log.error("FastAPI 返回空响应流");
                    writeSseError(outputStream, "AI 服务返回空响应");
                    return;
                }
                
                BufferedReader reader = new BufferedReader(
                        new InputStreamReader(responseStream, StandardCharsets.UTF_8));
                String line;
                
                while ((line = reader.readLine()) != null) {
                    // 写入前端
                    outputStream.write((line + "\n").getBytes(StandardCharsets.UTF_8));
                    outputStream.flush();
                    
                    // 收集完整回复
                    if (line.startsWith("data: ")) {
                        String data = line.substring(6);
                        if (!"[DONE]".equals(data) && !data.contains("error")) {
                            try {
                                JsonNode node = objectMapper.readTree(data);
                                if (node.has("content")) {
                                    fullResponse.append(node.get("content").asText());
                                }
                            } catch (Exception e) {
                                // 忽略解析错误
                            }
                        }
                    }
                }
                
                outputStream.flush();
                
                // 调用完成回调
                if (onComplete != null) {
                    onComplete.accept(fullResponse.toString());
                }
                
            } catch (Exception e) {
                log.error("流式调用 FastAPI 失败: {}", e.getMessage(), e);
                try {
                    writeSseError(outputStream, "AI 服务流式调用失败: " + e.getMessage());
                } catch (Exception writeEx) {
                    log.error("写入错误 SSE 失败: {}", writeEx.getMessage());
                }
                throw new RuntimeException("AI 服务流式调用失败: " + e.getMessage());
            }
        }
    }
}
```

#### 4.3 改造 ChatBotServiceImpl 的 streamMessage 方法

```java
@Service
@Slf4j
@RequiredArgsConstructor
public class ChatBotServiceImpl implements ChatBotService {

    private final ChatBotClient chatBotClient;
    private final StringRedisTemplate stringRedisTemplate;
    private final ChatMapper chatMapper;
    private final ObjectMapper objectMapper;
    private final TokenUtils tokenUtils;
    private final ExecutorService executorService = Executors.newFixedThreadPool(10);  // 异步保存线程池

    /**
     * 流式发送消息 - 改造后
     */
    @Override
    public StreamingResponseBody streamMessage(String authorization, ChatbotCreateDTO chatbotCreateDTO) {
        String content = chatbotCreateDTO.getContent();
        Integer conversationId = chatbotCreateDTO.getConversationId();
        
        // 获取用户ID
        Integer userId = tokenUtils.getUserId(authorization);
        if (userId == null) {
            throw new RuntimeException("用户认证信息无效");
        }
        
        log.info("流式发送消息，userId: {}, conversationId: {}, content: {}", 
                userId, conversationId, content);
        
        // 处理对话ID
        Long finalConversationId = prepareConversation(conversationId, userId, content);
        
        // 保存用户消息
        saveUserMessage(finalConversationId, content);
        
        // 获取对话ID的副本用于lambda
        final Long convId = finalConversationId;
        
        try {
            return outputStream -> {
                // 使用带回调的流式方法
                chatBotClient.streamMessageWithCallback(content, outputStream, aiResponse -> {
                    // 流式响应完成后，异步保存 AI 回复
                    executorService.submit(() -> {
                        try {
                            saveAiResponse(convId, aiResponse);
                            // 清除缓存
                            stringRedisTemplate.delete(UserConstant.CHAT_DETAIL + convId);
                            log.info("流式响应保存完成，conversationId: {}", convId);
                        } catch (Exception e) {
                            log.error("保存流式响应失败: {}", e.getMessage(), e);
                        }
                    });
                });
            };
        } catch (Exception e) {
            log.error("流式消息处理失败: {}", e.getMessage(), e);
            throw new RuntimeException("流式消息处理失败: " + e.getMessage());
        }
    }
    
    /**
     * 准备对话（创建或验证）
     */
    private Long prepareConversation(Integer conversationId, Integer userId, String firstMessage) {
        if (conversationId == null) {
            // 创建新对话
            ChatbotConversation conversation = ChatbotConversation.builder()
                    .userId(userId.longValue())
                    .name(firstMessage.length() > 20 ? firstMessage.substring(0, 20) + "..." : firstMessage)
                    .status(1)
                    .createdAt(LocalDateTime.now())
                    .updatedAt(LocalDateTime.now())
                    .build();
            
            chatMapper.insertConversation(conversation);
            log.info("创建新对话，conversationId: {}", conversation.getId());
            return conversation.getId();
        } else {
            // 验证对话权限
            ChatbotConversation conversation = chatMapper.selectConversationById(conversationId.longValue());
            if (conversation == null || !conversation.getUserId().equals(userId.longValue())) {
                throw new RuntimeException("无权访问该对话");
            }
            return conversationId.longValue();
        }
    }
    
    /**
     * 保存用户消息
     */
    private void saveUserMessage(Long conversationId, String content) {
        ChatbotMessage message = ChatbotMessage.builder()
                .conversationId(conversationId)
                .role("user")
                .content(content)
                .createdAt(LocalDateTime.now())
                .build();
        chatMapper.insertMessage(message);
        log.info("保存用户消息，messageId: {}", message.getId());
    }
    
    /**
     * 保存 AI 回复
     */
    private void saveAiResponse(Long conversationId, String content) {
        ChatbotMessage message = ChatbotMessage.builder()
                .conversationId(conversationId)
                .role("assistant")
                .content(content)
                .createdAt(LocalDateTime.now())
                .build();
        chatMapper.insertMessage(message);
        log.info("保存AI回复，messageId: {}", message.getId());
        
        // 更新对话时间
        chatMapper.updateConversationName(conversationId, null);
    }
}
```

---

## 四、数据库初始化脚本

```sql
-- 创建对话表
CREATE TABLE IF NOT EXISTS chatbot_conversation (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '对话ID',
    user_id BIGINT NOT NULL COMMENT '所属用户ID',
    name VARCHAR(255) COMMENT '对话名称',
    status TINYINT DEFAULT 1 COMMENT '状态：1-正常 0-已删除',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_user_id (user_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='智能客服对话表';

-- 创建消息表
CREATE TABLE IF NOT EXISTS chatbot_message (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '消息ID',
    conversation_id BIGINT NOT NULL COMMENT '所属对话ID',
    role VARCHAR(20) NOT NULL COMMENT '角色：user/assistant/system',
    content TEXT COMMENT '消息内容',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_conversation_id (conversation_id),
    INDEX idx_role (role),
    FOREIGN KEY (conversation_id) REFERENCES chatbot_conversation(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='智能客服消息表';
```

---

## 五、关键要点总结

### 5.1 事务处理
- `sendMessage` 方法使用 `@Transactional` 注解，确保用户消息和 AI 回复要么都保存成功，要么都回滚

### 5.2 流式处理
- `streamMessage` 采用异步保存策略，不阻塞前端响应
- 使用线程池处理保存操作，避免影响主流程

### 5.3 缓存处理
- 每次保存消息后，清除对应的 Redis 缓存，确保下次查询从数据库获取最新数据

### 5.4 权限验证
- 每次操作前验证用户是否有权访问该对话
- 新对话自动关联当前用户

### 5.5 对话命名
- 新对话默认使用用户第一条消息的前20个字符作为名称

---

## 六、注意事项

1. **TokenUtils 注入**：确保 `ChatBotServiceImpl` 中注入了 `TokenUtils` 用于获取当前用户ID
2. **事务管理器**：确保 Spring Boot 配置了事务管理器
3. **线程池配置**：流式保存使用的线程池需要根据实际并发量调整大小
4. **异常处理**：保存失败不应影响前端响应，需要做好异常捕获和日志记录
