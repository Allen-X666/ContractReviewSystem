package com.example.contractreview.model.vo;

import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 用户VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UserVO {

    /**
     * 用户ID
     */
    private Long id;

    /**
     * 用户名
     */
    private String username;

    /**
     * 真实姓名
     */
    private String nickName;

    /**
     * 邮箱
     */
    private String email;

    /**
     * 手机号
     */
    private String phone;

    /**
     * 头像URL
     */
    private String avatar;

    /**
     * 角色（admin/user）
     */
    private String role;

    /**
     * 创建时间
     */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss",  timezone = "GMT+8")
    private LocalDateTime createdAt;
}
