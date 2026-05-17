package com.example.contractreview.enums;

import lombok.Getter;

/**
 * 风险等级枚举
 */
@Getter
public enum RiskLevel {

    /**
     * 高风险
     */
    HIGH("high", "高风险"),

    /**
     * 中风险
     */
    MEDIUM("medium", "中风险"),

    /**
     * 低风险
     */
    LOW("low", "低风险"),

    /**
     * 默认：无
     */
    EMPTY("none", "无风险");

    private final String code;
    private final String description;

    RiskLevel(String code, String description) {
        this.code = code;
        this.description = description;
    }

    /**
     * 根据code获取枚举
     */
    public static RiskLevel getByCode(String code) {
        for (RiskLevel level : values()) {
            if (level.getCode().equals(code)) {
                return level;
            }
        }
        return null;
    }
}
