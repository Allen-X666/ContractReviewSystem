package com.example.contractreview.model.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 注册响应VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RegisterVO {

    /**
     * 用户ID
     */
    private Long userId;

    /**
     * 用户名
     */
    private String username;

    /**
     * Token
     */
    private String token;

    /**
     * 过期时间(秒)
     */
    private Long expiresIn;
}
