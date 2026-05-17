package com.example.contractreview.model.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 合同统计VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ContractStatsVO {

    /**
     * 合同总数
     */
    private Long total;

    /**
     * 待审查数量
     */
    private Long pending;

    /**
     * 已审查数量
     */
    private Long completed;

    /**
     * 高风险合同数量
     */
    private Long highRisk;

    /**
     * 中风险合同数量
     */
    private Long mediumRisk;

    /**
     * 低风险合同数量
     */
    private Long lowRisk;

    /**
     * 无风险合同数量
     */
    private Long noRisk;

    /**
     * 平均得分
     */
    private Integer avgScore;

    /**
     * 最高得分
     */
    private Integer maxScore;

    /**
     * 最低得分
     */
    private Integer minScore;

    /**
     * 本周合同数量
     */
    private Long thisWeekCount;

    /**
     * 上周合同数量
     */
    private Long lastWeekCount;

    /**
     * 周增长率（百分比，如 10.5 表示增长 10.5%）
     */
    private Double weekGrowthRate;

    /**
     * 合同总数趋势（百分比）
     */
    private Integer totalTrend;

    /**
     * 待审查数量趋势（百分比）
     */
    private Integer pendingTrend;

    /**
     * 已审查数量趋势（百分比）
     */
    private Integer completedTrend;

    /**
     * 高风险合同数量趋势（百分比）
     */
    private Integer highRiskTrend;

    /**
     * 中风险合同数量趋势（百分比）
     */
    private Integer mediumRiskTrend;

    /**
     * 低风险合同数量趋势（百分比）
     */
    private Integer lowRiskTrend;

    /**
     * 无风险合同数量趋势（百分比）
     */
    private Integer noRiskTrend;

    /**
     * 平均得分趋势（百分比）
     */
    private Integer avgScoreTrend;

    /**
     * 最高得分趋势（百分比）
     */
    private Integer maxScoreTrend;

    /**
     * 最低得分趋势（百分比）
     */
    private Integer minScoreTrend;
}
