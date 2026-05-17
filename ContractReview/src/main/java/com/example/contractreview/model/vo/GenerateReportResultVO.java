package com.example.contractreview.model.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 生成报告结果VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class GenerateReportResultVO {

    /**
     * 报告ID
     */
    private Long reportId;

    /**
     * 报告编号
     */
    private String reportNo;

    /**
     * 审查ID
     */
    private Long reviewId;

    /**
     * 报告标题
     */
    private String reportTitle;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;
}
