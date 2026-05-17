package com.example.contractreview.enums;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;

/**
 * 公告发布类型枚举
 */
public enum PublishType {

    /**
     * 立即发布
     */
    IMMEDIATE("immediate", "立即发布"),

    /**
     * 定时发布
     */
    SCHEDULED("scheduled", "定时发布");

    private final String code;
    private final String description;

    PublishType(String code, String description) {
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
     * 根据code获取枚举
     */
    @JsonCreator
    public static PublishType getByCode(String code) {
        if (code == null) {
            return null;
        }
        for (PublishType type : values()) {
            if (type.code.equals(code)) {
                return type;
            }
        }
        return null;
    }
}
