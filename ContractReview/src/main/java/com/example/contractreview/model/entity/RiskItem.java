package com.example.contractreview.model.entity;

import com.example.contractreview.enums.RiskLevel;
import com.example.contractreview.enums.RiskType;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 风险项实体类
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RiskItem {

    /**
     * 风险ID
     */
    private Long id;

    /**
     * 审查ID
     */
    private Long reviewId;

    /**
     * 合同ID
     */
    private Long contractId;

    /**
     * 风险类型
     */
    private RiskType riskType;

    /**
     * 风险等级
     */
    private RiskLevel riskLevel;

    /**
     * 条款标题
     */
    private String clauseTitle;

    /**
     * 条款原文
     */
    private String clauseContent;

    /**
     * 风险描述
     */
    private String riskDescription;

    /**
     * 修改建议
     */
    private String suggestion;

    /**
     * 关联法条(JSON数组)
     */
    private String relatedLaws;

    /**
     * 段落索引
     */
    private Integer paragraphIndex;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;
}
