package com.example.contractreview.model.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 生成报告DTO
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class GenerateReportDTO {

    /**
     * 审查ID
     */
    private Long reviewId;

    /**
     * 报告选项
     */
    private ReportOptionsDTO reportOptions;

    /**
     * 报告选项DTO
     */
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ReportOptionsDTO {

        /**
         * 包含封面
         */
        private Boolean includeCover;

        /**
         * 包含概览
         */
        private Boolean includeOverview;

        /**
         * 包含风险详情
         */
        private Boolean includeRiskDetails;

        /**
         * 包含法条引用
         */
        private Boolean includeLawReferences;

        /**
         * 包含修改建议
         */
        private Boolean includeSuggestions;
    }
}
