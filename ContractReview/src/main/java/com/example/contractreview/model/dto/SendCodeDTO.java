package com.example.contractreview.model.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 发送验证码DTO
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class SendCodeDTO {

    /**
     * {
     *   "target": "string",        // 手机号或邮箱
     *   "type": "string",          // 类型: login/register/reset_password
     *   "targetType": "phone"      // 目标类型: phone/email
     * }
     */

    /**
     * 手机号或邮箱
     */
    private String target;

    /**
     * 类型
     */
    private String type;

    /**
     * 目标类型
     */
    private String targetType;
}
