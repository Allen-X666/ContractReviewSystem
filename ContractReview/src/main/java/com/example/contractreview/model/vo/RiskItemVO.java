package com.example.contractreview.model.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * 风险项VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RiskItemVO {

    /**
     * 风险ID
     */
    private Long id;

    /**
     * 风险类型
     */
    private String riskType;

    /**
     * 风险等级
     */
    private String riskLevel;

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
     * 关联法条
     */
    private List<RelatedLawVO> relatedLaws;

    /**
     * 段落索引
     */
    private Integer paragraphIndex;

    /**
     * 关联法条VO
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class RelatedLawVO {

        /**
         * 法规ID
         */
        private Long lawId;

        /**
         * 法规名称
         */
        private String lawName;

        /**
         * 条款编号
         */
        private String articleNo;

        /**
         * 条款内容
         */
        private String content;
    }
}
