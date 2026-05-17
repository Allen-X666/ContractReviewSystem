package com.example.contractreview.enums;

/**
 * 法规状态枚举
 */
public enum LawStatus {

    /**
     * 有效
     */
    EFFECTIVE("有效", "有效"),

    /**
     * 已废止
     */
    REPEALED("已废止", "已废止"),

    /**
     * 已修订
     */
    AMENDED("已修订", "已修订");

    private final String code;
    private final String description;

    LawStatus(String code, String description) {
        this.code = code;
        this.description = description;
    }

    public String getCode() {
        return code;
    }

    public String getDescription() {
        return description;
    }

    /**
     * 根据code获取枚举
     */
    public static LawStatus getByCode(String code) {
        for (LawStatus status : values()) {
            if (status.getCode().equals(code)) {
                return status;
            }
        }
        return null;
    }
}
