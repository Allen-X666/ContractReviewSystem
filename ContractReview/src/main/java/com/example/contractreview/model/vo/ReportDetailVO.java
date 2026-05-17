package com.example.contractreview.model.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

/**
 * 报告详情VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ReportDetailVO {

    /**
     * 报告ID
     */
    private Long reportId;

    /**
     * 报告编号
     */
    private String reportNo;

    /**
     * 审查ID
     */
    private Long reviewId;

    /**
     * 合同ID
     */
    private Long contractId;

    /**
     * 合同名称
     */
    private String contractName;

    /**
     * 报告标题
     */
    private String reportTitle;

    /**
     * 总体评分
     */
    private Integer overallScore;

    /**
     * 风险摘要
     */
    private Map<String, Integer> riskSummary;

    /**
     * 审查结论
     */
    private String conclusion;

    /**
     * 风险列表
     */
    private List<RiskItemVO> risks;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;
}
