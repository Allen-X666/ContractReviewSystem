package com.example.contractreview.model.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 报告VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ReportVO {

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
     * 合同ID
     */
    private Long contractId;

    /**
     * 合同名称
     */
    private String contractName;

    /**
     * 报告标题
     */
    private String reportTitle;

    /**
     * 下载次数
     */
    private Integer downloadCount;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;
}
