package com.example.contractreview.model.dto;

import com.example.contractreview.enums.UserRole;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 管理员更新用户信息DTO
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class AdminUpdateUserDTO {

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
     * 角色
     */
    private UserRole role;
}
