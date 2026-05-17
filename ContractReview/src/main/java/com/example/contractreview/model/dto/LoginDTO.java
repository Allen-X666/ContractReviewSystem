package com.example.contractreview.model.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 用户登录DTO
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class LoginDTO {

    /**
     * {
     *   "username": "string",      // 用户名/手机号/邮箱
     *   "password": "string",      // 密码
     *   "loginType": "account",    // 登录类型: account/phone/email
     *   "code": "string",          // 验证码（手机号/邮箱登录时必填）
     *   "captchaId": "string"      // 图形验证码ID
     * }
     */

    /**
     * 用户名/手机号/邮箱
     */
    private String username;

    /**
     * 密码
     */
    private String password;

    /**
     * 登录类型
     */
    private String loginType;

    /**
     * 验证码
     */
    private String code;

    /**
     * 图形验证码ID
     */
    private String captchaId;
}
