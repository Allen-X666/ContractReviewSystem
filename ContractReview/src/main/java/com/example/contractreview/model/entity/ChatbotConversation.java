package com.example.contractreview.model.entity;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 智能客服对话实体类
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ChatbotConversation {

    /**
     * 对话ID
     */
    private Long id;

    /**
     * 所属用户ID
     */
    private Long userId;

    /**
     * 对话名称
     */
    private String name;

    /**
     * 状态：1-正常 0-已删除
     */
    private Integer status;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;

    /**
     * 更新时间
     */
    private LocalDateTime updatedAt;
}
