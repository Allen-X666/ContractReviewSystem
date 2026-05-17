package com.example.contractreview.model.vo;

import com.example.contractreview.model.vo.fastapi.RiskItemVO;
import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

/**
 * 最新审查记录VO
 * 用于 /review/contract/{contractId}/latest 接口返回
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class LatestReviewVO {

    /**
     * 审查记录ID (数字)
     */
    private Integer reviewId;

    /**
     * 审查编号 (字符串，如 "38")
     */
    private String reviewNo;

    /**
     * 合同ID
     */
    private Integer contractId;

    /**
     * 合同名称
     */
    private String contractName;

    /**
     * 审查状态 (processing/completed/failed)
     */
    private String status;

    /**
     * 开始时间
     */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime startedAt;

    /**
     * 完成时间 (未完成时为null)
     */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime completedAt;

    /**
     * 创建时间
     */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime createdAt;

    /**
     * 综合评分
     */
    private Integer overallScore;

    /**
     * 风险等级 (high/medium/low/none)
     */
    private String riskLevel;

    /**
     * 审查状态消息
     */
    private String message;

    /**
     * 审查结论
     */
    private String conclusion;

    /**
     * 风险摘要
     */
    private Map<String, Integer> riskSummary;

    /**
     * 风险项列表
     */
    private List<RiskItemVO> risks;
}
