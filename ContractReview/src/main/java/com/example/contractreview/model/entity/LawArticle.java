package com.example.contractreview.model.entity;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 法条实体类
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class LawArticle {

    /**
     * 条款ID
     */
    private Long id;

    /**
     * 法规ID
     */
    private Long lawId;

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

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;
}
