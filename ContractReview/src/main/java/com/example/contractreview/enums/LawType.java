package com.example.contractreview.enums;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonValue;

/**
 * 法律文档类型枚举
 */
public enum LawType {

    /**
     * 法律法规
     */
    LAW("law", "法律法规"),

    /**
     * 司法解释
     */
    INTERPRETATION("interpretation", "司法解释"),

    /**
     * 合同范本
     */
    TEMPLATE("template", "合同范本"),

    /**
     * 其他
     */
    OTHER("other", "其他");

    private final String code;
    private final String description;

    LawType(String code, String description) {
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
    public static LawType getByCode(String code) {
        if (code == null) {
            return null;
        }
        for (LawType type : values()) {
            if (type.code.equals(code)) {
                return type;
            }
        }
        return null;
    }
}
