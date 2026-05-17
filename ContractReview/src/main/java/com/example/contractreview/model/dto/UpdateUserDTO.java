package com.example.contractreview.model.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 更新用户信息DTO
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class UpdateUserDTO {

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
}
