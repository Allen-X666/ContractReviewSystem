package com.example.contractreview.model.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 智能客服重命名对话请求DTO
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class ChatbotRenameDTO {

    /**
     * 新的对话名称
     */
    @NotBlank(message = "名称不能为空")
    @Size(max = 100, message = "对话名称不能超过100字")
    private String name;
}
