package com.example.contractreview.enums;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;

/**
 * 用户状态枚举
 */
public enum UserStatus {

    /**
     * 禁用
     */
    DISABLED(0, "禁用"),

    /**
     * 启用
     */
    ENABLED(1, "启用");

    private final Integer code;
    private final String description;

    UserStatus(Integer code, String description) {
        this.code = code;
        this.description = description;
    }

    @JsonValue
    public Integer getCode() {
        return code;
    }

    public String getDescription() {
        return description;
    }

    /**
     * 根据code获取枚举（支持Integer和String）
     */
    @JsonCreator
    public static UserStatus getByCode(Object code) {
        if (code == null) {
            return null;
        }
        Integer codeValue;
        if (code instanceof Integer) {
            codeValue = (Integer) code;
        } else if (code instanceof String) {
            try {
                codeValue = Integer.parseInt((String) code);
            } catch (NumberFormatException e) {
                // 尝试按名称解析（忽略大小写）
                try {
                    return UserStatus.valueOf(((String) code).toUpperCase());
                } catch (IllegalArgumentException ex) {
                    return null;
                }
            }
        } else {
            return null;
        }

        for (UserStatus status : values()) {
            if (status.getCode().equals(codeValue)) {
                return status;
            }
        }
        return null;
    }
}
