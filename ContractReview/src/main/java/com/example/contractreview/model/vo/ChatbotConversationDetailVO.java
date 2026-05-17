package com.example.contractreview.model.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 智能客服对话详情VO（含消息列表）
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ChatbotConversationDetailVO {

    /**
     * 对话ID
     */
    private Long id;

    /**
     * 对话名称
     */
    private String name;

    /**
     * 消息列表
     */
    private List<ChatbotMessageVO> messages;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;

    /**
     * 更新时间
     */
    private LocalDateTime updatedAt;
}
