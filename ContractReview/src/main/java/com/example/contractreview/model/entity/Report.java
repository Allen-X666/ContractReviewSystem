package com.example.contractreview.model.entity;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 报告实体类
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Report {

    /**
     * 报告ID
     */
    private Long id;

    /**
     * 报告编号
     */
    private String reportNo;

    /**
     * 审查ID
     */
    private Long reviewId;

    /**
     * 合同ID
     */
    private Long contractId;

    /**
     * 用户ID
     */
    private Long userId;

    /**
     * 报告标题
     */
    private String reportTitle;

    /**
     * 报告内容(JSON)
     */
    private String content;

    /**
     * Word文件路径
     */
    private String wordPath;

    /**
     * PDF文件路径
     */
    private String pdfPath;

    /**
     * 下载次数
     */
    private Integer downloadCount;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;

    /**
     * 更新时间
     */
    private LocalDateTime updatedAt;
}
