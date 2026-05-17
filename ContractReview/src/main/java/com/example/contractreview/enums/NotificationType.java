package com.example.contractreview.enums;

import lombok.Getter;

/**
 * 通知类型枚举
 */
@Getter
public enum NotificationType {

    /**
     * 审查完成
     */
    REVIEW_COMPLETE("review_complete", "审查完成"),

    /**
     * 高风险预警
     */
    HIGH_RISK_WARNING("high_risk_warning", "高风险预警"),

    /**
     * 系统公告
     */
    SYSTEM_ANNOUNCEMENT("system_announcement", "系统公告"),

    /**
     * 邮件通知
     */
    EMAIL_NOTIFICATION("email_notification", "邮件通知");

    private final String code;
    private final String description;

    NotificationType(String code, String description) {
        this.code = code;
        this.description = description;
    }

    /**
     * 根据code获取枚举
     */
    public static NotificationType fromCode(String code) {
        for (NotificationType type : values()) {
            if (type.getCode().equals(code)) {
                return type;
            }
        }
        return null;
    }
}
