package com.example.contractreview.model.vo;

import com.example.contractreview.enums.LawCategory;
import com.example.contractreview.enums.LawStatus;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDate;

/**
 * 法律法规列表VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class LawRegulationVO {

    /**
     * 法规ID
     */
    private Long id;

    /**
     * 法规编号
     */
    private String lawNo;

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
     * 条款数量
     */
    private Integer articleCount;

    /**
     * 是否最新
     */
    private Boolean isNew;
}
