package com.example.contractreview.enums;

/**
 * 审查阶段枚举
 */
public enum ReviewStage {

    /**
     * 解析文档
     */
    PARSING("parsing", "解析文档"),

    /**
     * 检索法条
     */
    RETRIEVING("retrieving", "检索法条"),

    /**
     * AI分析
     */
    ANALYZING("analyzing", "AI分析"),

    /**
     * 生成报告
     */
    GENERATING("generating", "生成报告");

    private final String code;
    private final String description;

    ReviewStage(String code, String description) {
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
    public static ReviewStage getByCode(String code) {
        for (ReviewStage stage : values()) {
            if (stage.getCode().equals(code)) {
                return stage;
            }
        }
        return null;
    }
}
