package com.example.contractreview.enums;

/**
 * 法规分类枚举
 */
public enum LawCategory {

    /**
     * 合同法
     */
    CONTRACT("contract", "合同法"),

    /**
     * 劳动法
     */
    LABOR("labor", "劳动法"),

    /**
     * 知识产权
     */
    INTELLECTUAL_PROPERTY("intellectual_property", "知识产权"),

    /**
     * 公司法
     */
    COMPANY("company", "公司法"),

    /**
     * 民法
     */
    CIVIL("civil", "民法"),

    /**
     * 刑法
     */
    CRIMINAL("criminal", "刑法");

    private final String code;
    private final String description;

    LawCategory(String code, String description) {
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
    public static LawCategory getByCode(String code) {
        for (LawCategory category : values()) {
            if (category.getCode().equals(code)) {
                return category;
            }
        }
        return null;
    }
}
