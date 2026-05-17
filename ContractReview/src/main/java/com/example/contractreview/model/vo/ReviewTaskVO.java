package com.example.contractreview.model.vo;

import com.example.contractreview.enums.ReviewStage;
import com.example.contractreview.enums.ReviewStatus;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 审查任务VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ReviewTaskVO {

    /**
     * 审查ID
     */
    private Long reviewId;

    /**
     * 审查编号
     */
    private String reviewNo;

    /**
     * 合同ID
     */
    private Long contractId;

    /**
     * 状态
     */
    private ReviewStatus status;

    /**
     * 当前阶段
     */
    private ReviewStage stage;

    /**
     * 进度(0-100)
     */
    private Integer progress;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;
}
