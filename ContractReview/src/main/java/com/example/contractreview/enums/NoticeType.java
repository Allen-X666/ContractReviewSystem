package com.example.contractreview.enums;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;

/**
 * 公告类型枚举
 */
public enum NoticeType {

    /**
     * 系统公告
     */
    SYSTEM("system", "系统公告"),

    /**
     * 功能更新
     */
    FEATURE("feature", "功能更新"),

    /**
     * 维护通知
     */
    MAINTENANCE("maintenance", "维护通知"),

    /**
     * 其他
     */
    OTHER("other", "其他");

    private final String code;
    private final String description;

    NoticeType(String code, String description) {
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
    public static NoticeType getByCode(String code) {
        if (code == null) {
            return null;
        }
        for (NoticeType type : values()) {
            if (type.code.equals(code)) {
                return type;
            }
        }
        return null;
    }
}
