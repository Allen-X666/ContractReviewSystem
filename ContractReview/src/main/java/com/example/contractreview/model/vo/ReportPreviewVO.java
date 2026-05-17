package com.example.contractreview.model.vo;

import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

/**
 * 报告预览 VO
 * 用于前端直接渲染审查报告页面
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ReportPreviewVO {

    /**
     * 报告标题
     */
    private String title;

    /**
     * 合同名称
     */
    private String contractName;

    /**
     * 审查ID
     */
    private Integer reviewId;

    /**
     * 审查编号
     */
    private String reviewNo;

    /**
     * 审查时间
     */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime reviewTime;

    /**
     * 审查机构
     */
    private String reviewAgency;

    /**
     * 综合评分
     */
    private Integer overallScore;

    /**
     * 审查结论
     */
    private String conclusion;

    /**
     * 风险摘要
     */
    private RiskSummary riskSummary;

    /**
     * 风险列表
     */
    private List<RiskPreviewVO> risks;

    /**
     * 法条依据汇总
     */
    private List<LawReferenceVO> lawReferences;

    /**
     * 风险摘要内部类
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class RiskSummary {
        private Integer high;
        private Integer medium;
        private Integer low;
        private Integer none;
    }

    /**
     * 风险项预览 VO
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class RiskPreviewVO {
        private String id;
        private String level;
        private String clause;
        private String description;
        private String location;
        private String suggestion;
        private List<LawReferenceVO> lawReferences;
    }

    /**
     * 法条引用 VO
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class LawReferenceVO {
        private String id;
        private String name;
        private String article;
        private String content;
        private String interpretation;
        private Integer citationCount;
    }
}
