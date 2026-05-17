package com.example.contractreview.model.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDate;

/**
 * 知识库统计VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class KnowledgeStatsVO {

    /**
     * 法规总数
     */
    private Integer totalLaws;

    /**
     * 法条总数
     */
    private Integer totalArticles;

    /**
     * 模板总数
     */
    private Integer totalTemplates;

    /**
     * 最后更新时间
     */
    private LocalDate lastUpdate;
}
