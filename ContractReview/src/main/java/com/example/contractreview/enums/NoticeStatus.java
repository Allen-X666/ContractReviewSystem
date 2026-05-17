package com.example.contractreview.enums;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;

/**
 * 公告状态枚举
 */
public enum NoticeStatus {

    /**
     * 待发布
     */
    PENDING("pending", "待发布"),

    /**
     * 已发布
     */
    PUBLISHED("published", "已发布");

    private final String code;
    private final String description;

    NoticeStatus(String code, String description) {
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
    public static NoticeStatus getByCode(String code) {
        if (code == null) {
            return null;
        }
        for (NoticeStatus status : values()) {
            if (status.code.equals(code)) {
                return status;
            }
        }
        return null;
    }
}
