package com.example.contractreview.model.entity;

import com.example.contractreview.enums.ReviewStage;
import com.example.contractreview.enums.ReviewStatus;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 审查任务实体类
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ReviewTask {

    /**
     * 审查ID
     */
    private Long id;

    /**
     * 审查编号
     */
    private String reviewNo;

    /**
     * 合同ID
     */
    private Long contractId;

    /**
     * 用户ID
     */
    private Long userId;

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
     * 总体评分
     */
    private Integer overallScore;

    /**
     * 审查结论
     */
    private String conclusion;

    /**
     * 开始时间
     */
    private LocalDateTime startedAt;

    /**
     * 完成时间
     */
    private LocalDateTime completedAt;

    /**
     * 错误信息
     */
    private String errorMsg;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;

    /**
     * 更新时间
     */
    private LocalDateTime updatedAt;
}
