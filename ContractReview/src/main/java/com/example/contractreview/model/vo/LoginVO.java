package com.example.contractreview.model.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 登录响应VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class LoginVO {

    /**
     * Token
     */
    private String token;

    /**
     * 过期时间(秒)
     */
    private Long expiresIn;

    /**
     * 用户信息
     */
    private UserVO userInfo;
}
