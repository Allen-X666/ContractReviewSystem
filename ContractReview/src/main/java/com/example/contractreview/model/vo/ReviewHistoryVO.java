package com.example.contractreview.model.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.Map;

/**
 * 审查历史VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ReviewHistoryVO {

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
     * 合同名称
     */
    private String contractName;

    /**
     * 文件大小
     */
    private Long fileSize;

    /**
     * 状态
     */
    private String status;

    /**
     * 风险摘要
     */
    private Map<String, Integer> riskSummary;

    /**
     * 总体评分
     */
    private Integer overallScore;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;

    /**
     * 完成时间
     */
    private LocalDateTime completedAt;
}
