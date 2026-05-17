package com.example.contractreview.model.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.Map;

/**
 * 仪表盘统计VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class DashboardStatsVO {

    /**
     * 总合同数
     */
    private Integer totalContracts;

    /**
     * 本月新增合同数
     */
    private Integer newContractsThisMonth;

    /**
     * 待审查合同数
     */
    private Integer pendingReviews;

    /**
     * 已完成审查数
     */
    private Integer completedReviews;

    /**
     * 平均审查得分
     */
    private Double avgReviewScore;

    /**
     * 风险分布
     */
    private Map<String, Integer> riskDistribution;

    /**
     * 最近活动
     */
    private List<RecentActivityVO> recentActivities;

    /**
     * 最近活动VO
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class RecentActivityVO {

        /**
         * 活动类型
         */
        private String type;

        /**
         * 描述
         */
        private String description;

        /**
         * 时间
         */
        private String time;
    }
}
