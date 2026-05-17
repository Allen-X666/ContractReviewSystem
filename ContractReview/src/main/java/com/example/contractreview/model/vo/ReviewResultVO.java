package com.example.contractreview.model.vo;

import com.example.contractreview.enums.ReviewStatus;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.Map;

/**
 * 审查结果VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ReviewResultVO {

    /**
     * 审查ID
     */
    private Long reviewId;

    /**
     * 审查编号
     */
    private String reviewNo;

    /**
     * 合同ID
     */
    private Long contractId;

    /**
     * 状态
     */
    private ReviewStatus status;

    /**
     * 总体评分
     */
    private Integer overallScore;

    /**
     * 审查结论
     */
    private String conclusion;

    /**
     * 风险摘要
     */
    private Map<String, Integer> riskSummary;

    /**
     * 完成时间
     */
    private LocalDateTime completedAt;
}
