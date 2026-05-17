package com.example.contractreview.model.vo;

import com.example.contractreview.enums.LawCategory;
import com.example.contractreview.enums.LawStatus;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;

/**
 * 法律法规详情VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class LawRegulationDetailVO {

    /**
     * 法规ID
     */
    private Long id;

    /**
     * 法规名称
     */
    private String name;

    /**
     * 分类
     */
    private LawCategory category;

    /**
     * 发布机关
     */
    private String issuer;

    /**
     * 发布日期
     */
    private LocalDate publishDate;

    /**
     * 施行日期
     */
    private LocalDate effectiveDate;

    /**
     * 状态
     */
    private LawStatus status;

    /**
     * 法规简介
     */
    private String description;

    /**
     * 是否最新
     */
    private Boolean isNew;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;

    /**
     * 法条列表
     */
    private List<LawArticleVO> articles;

    /**
     * 法条VO
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class LawArticleVO {
        /**
         * 条款ID
         */
        private Long id;

        /**
         * 条款编号
         */
        private String articleNo;

        /**
         * 条款标题
         */
        private String title;

        /**
         * 条款内容
         */
        private String content;

        /**
         * 司法解释
         */
        private String interpretation;
    }
}
