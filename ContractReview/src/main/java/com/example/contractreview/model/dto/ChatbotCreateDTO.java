package com.example.contractreview.model.dto;

import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 智能客服创建对话请求DTO
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class ChatbotCreateDTO {
    /**
     * {
     *     "conversationId": null,
     *     "content": "合同审查的流程是什么？"
     * }
     */
    private Integer conversationId;
    private String content;
}
