package com.example.contractreview.model.entity;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 智能客服消息实体类
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ChatbotMessage {

    /**
     * 消息ID
     */
    private Long id;

    /**
     * 所属对话ID
     */
    private Long conversationId;

    /**
     * 角色：user/assistant/system
     */
    private String role;

    /**
     * 消息内容
     */
    private String content;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;
}
