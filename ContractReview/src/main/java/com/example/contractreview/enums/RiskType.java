package com.example.contractreview.enums;

import lombok.Getter;

/**
 * 风险类型枚举
 */
@Getter
public enum RiskType {

    /**
     * 无效条款
     */
    INVALID_CLAUSE("无效条款", "无效条款"),

    /**
     * 缺失条款
     */
    MISSING_CLAUSE("缺失条款", "缺失条款"),

    /**
     * 不合理条款
     */
    UNREASONABLE_CLAUSE("不合理条款", "不合理条款"),

    /**
     * 法律风险
     */
    LEGAL_RISK("法律风险", "法律风险");

    private final String code;
    private final String description;

    RiskType(String code, String description) {
        this.code = code;
        this.description = description;
    }

    /**
     * 根据code获取枚举
     */
    public static RiskType getByCode(String code) {
        for (RiskType type : values()) {
            if (type.getCode().equals(code)) {
                return type;
            }
        }
        return null;
    }
}
