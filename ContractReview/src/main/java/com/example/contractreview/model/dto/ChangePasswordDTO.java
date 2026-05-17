package com.example.contractreview.model.dto;

import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 修改密码DTO
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class ChangePasswordDTO {

    /**
     * 原密码
     */
    @NotNull(message = "原密码不能为空")
    private String oldPassword;

    /**
     * 新密码
     */
    @NotNull(message = "新密码不能为空")
    private String newPassword;

    /**
     * 确认新密码
     */
    @NotNull(message = "确认新密码不能为空")
    private String confirmPassword;
}
