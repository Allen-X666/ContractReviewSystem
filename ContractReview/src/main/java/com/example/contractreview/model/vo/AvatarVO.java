package com.example.contractreview.model.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 头像VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AvatarVO {

    /**
     * 头像URL
     */
    private String avatarUrl;
}
