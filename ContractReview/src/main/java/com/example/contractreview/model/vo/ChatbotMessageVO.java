package com.example.contractreview.model.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 智能客服消息VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ChatbotMessageVO {

    /**
     * 消息ID
     */
    private Long id;

    /**
     * 角色：user/assistant/system
     */
    private String role;

    /**
     * 消息内容（支持Markdown）
     */
    private String content;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;
}
