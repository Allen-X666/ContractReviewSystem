package com.example.contractreview.model.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 用户注册DTO
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class RegisterDTO {

    /**
     * 用户名
     */
    private String username;

    /**
     * 密码
     */
    @NotBlank(message = "密码不能为空")
    private String password;

    /**
     * 确认密码
     */
    @NotBlank(message = "确认密码不能为空")
    private String confirmPassword;

    /**
     * 邮箱
     */
    @Email(message = "邮箱格式不正确")
    private String email;

    /**
     * 手机号
     */
    @Pattern(regexp = "^1[3-9]\\d{9}$", message = "手机号格式不正确")
    private String phone;

    /**
     * 验证码
     */
    @NotBlank(message = "验证码不能为空")
    private String code;

    /**
     * 验证码ID（图形验证码需要，邮箱/手机验证码不需要）
     */
    private String captchaId;

    /**
     * 注册类型: account/phone/email
     */
    @NotBlank(message = "注册类型不能为空")
    @Pattern(regexp = "^(account|phone|email)$", message = "注册类型必须是account、phone或email")
    private String registerType;
}
