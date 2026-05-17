package com.example.contractreview.model.vo;

import com.fasterxml.jackson.annotation.JsonValue;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 合同VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ContractVO {

    /**
     * 合同ID
     */
    private Integer id;

    /**
     * 文件名
     */
    private String fileName;

    /**
     * 文件大小
     */
    private Long fileSize;

    /**
     * 文件类型
     */
    private String fileType;

    /**
     * 审查状态
     */
    private String reviewStatus;

    /**
     * 风险等级
     */
    private String riskLevel;

    /**
     * 审查得分
     */
    private Integer reviewScore;

    /**
     * 最新审查记录ID
     */
    private Integer lastReviewId;

    /**
     * 最新审查编号
     */
    private String lastReviewNo;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;
}
