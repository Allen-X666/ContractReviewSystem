package com.example.contractreview.model.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 智能客服对话列表项VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ChatbotConversationVO {

    /**
     * 对话ID
     */
    private Long id;

    /**
     * 对话名称
     */
    private String name;

    /**
     * 消息数量
     */
    private Integer messageCount;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;

    /**
     * 更新时间
     */
    private LocalDateTime updatedAt;
}
