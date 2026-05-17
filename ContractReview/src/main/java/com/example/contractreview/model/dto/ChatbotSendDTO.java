package com.example.contractreview.model.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 智能客服发送消息请求DTO
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class ChatbotSendDTO {

    /**
     * 对话ID
     */
    @NotNull(message = "对话ID不能为空")
    private Long conversationId;

    /**
     * 消息内容
     */
    @NotBlank(message = "消息内容不能为空")
    @Size(max = 2000, message = "消息内容不能超过2000字")
    private String content;
}
