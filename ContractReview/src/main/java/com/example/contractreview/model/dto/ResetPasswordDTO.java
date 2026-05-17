package com.example.contractreview.model.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 重置密码DTO（忘记密码）
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class ResetPasswordDTO {

    /**
     * 邮箱
     */
    @Email(message = "邮箱格式不正确")
    @NotNull(message = "邮箱不能为空")
    private String email;

    /**
     * 验证码
     */
    @NotNull(message = "验证码不能为空")
    private String code;

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
