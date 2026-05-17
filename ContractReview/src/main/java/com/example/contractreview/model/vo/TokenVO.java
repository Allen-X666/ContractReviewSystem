package com.example.contractreview.model.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Token响应VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class TokenVO {

    /**
     * Token
     */
    private String token;

    /**
     * 过期时间(秒)
     */
    private Long expiresIn;
}
