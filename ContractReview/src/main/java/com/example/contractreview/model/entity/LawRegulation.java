package com.example.contractreview.model.entity;

import com.example.contractreview.enums.LawCategory;
import com.example.contractreview.enums.LawStatus;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 法律法规实体类
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class LawRegulation {

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
     * 条款数量（非数据库字段，用于查询统计）
     */
    private Integer articleCount;

    /**
     * 是否最新
     */
    private Boolean isNew;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;
}
