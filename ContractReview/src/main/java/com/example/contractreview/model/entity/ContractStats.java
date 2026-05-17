package com.example.contractreview.model.entity;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 合同统计实体
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ContractStats {

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
}
