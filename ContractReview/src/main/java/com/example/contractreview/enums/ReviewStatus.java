package com.example.contractreview.enums;

import lombok.Getter;

/**
 * 审查状态枚举
 */
@Getter
public enum ReviewStatus {

    /**
     * 待处理
     */
    PENDING("pending", "待处理"),

    /**
     * 审查中
     */
    PROCESSING("processing", "审查中"),

    /**
     * 已完成
     */
    COMPLETED("completed", "已完成"),

    /**
     * 审查失败
     */
    FAILED("failed", "审查失败"),

    /**
     * 已取消
     */
    CANCELLED("cancelled", "已取消");

    private final String code;
    private final String description;

    ReviewStatus(String code, String description) {
        this.code = code;
        this.description = description;
    }

    /**
     * 根据code获取枚举
     */
    public static ReviewStatus getByCode(String code) {
        for (ReviewStatus status : values()) {
            if (status.getCode().equals(code)) {
                return status;
            }
        }
        return null;
    }
}
