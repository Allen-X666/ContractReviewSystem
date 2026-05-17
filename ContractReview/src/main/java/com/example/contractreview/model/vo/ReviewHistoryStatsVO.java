package com.example.contractreview.model.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 审查历史统计VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ReviewHistoryStatsVO {

    /**
     * 总数
     */
    private Integer total;

    /**
     * 本月数量
     */
    private Integer thisMonth;

    /**
     * 平均得分
     */
    private Integer avgScore;

    /**
     * 总问题数
     */
    private Integer totalIssues;
}
