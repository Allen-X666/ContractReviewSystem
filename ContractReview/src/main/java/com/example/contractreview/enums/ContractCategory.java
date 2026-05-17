package com.example.contractreview.enums;

/**
 * 合同分类枚举
 */
public enum ContractCategory {

    /**
     * 采购合同
     */
    PURCHASE("采购合同", "采购合同"),

    /**
     * 服务协议
     */
    SERVICE("服务协议", "服务协议"),

    /**
     * 劳动合同
     */
    LABOR("劳动合同", "劳动合同"),

    /**
     * 租赁合同
     */
    LEASE("租赁合同", "租赁合同"),

    /**
     * 保密协议
     */
    CONFIDENTIALITY("保密协议", "保密协议"),

    /**
     * 合作协议
     */
    COOPERATION("合作协议", "合作协议");

    private final String code;
    private final String description;

    ContractCategory(String code, String description) {
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
    public static ContractCategory getByCode(String code) {
        for (ContractCategory category : values()) {
            if (category.getCode().equals(code)) {
                return category;
            }
        }
        return null;
    }
}
