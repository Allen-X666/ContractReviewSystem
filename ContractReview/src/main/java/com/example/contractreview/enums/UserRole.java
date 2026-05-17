package com.example.contractreview.enums;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;

/**
 * 用户角色枚举
 */
public enum UserRole {

    /**
     * 管理员
     */
    ADMIN("admin", "管理员"),

    /**
     * 普通用户
     */
    USER("user", "普通用户");

    private final String code;
    private final String description;

    UserRole(String code, String description) {
        this.code = code;
        this.description = description;
    }

    @JsonValue
    public String getCode() {
        return code;
    }

    public String getDescription() {
        return description;
    }

    /**
     * 根据code获取枚举（忽略大小写）
     */
    @JsonCreator
    public static UserRole getByCode(String code) {
        if (code == null) {
            return null;
        }
        for (UserRole role : values()) {
            if (role.getCode().equalsIgnoreCase(code)) {
                return role;
            }
        }
        return null;
    }
}
