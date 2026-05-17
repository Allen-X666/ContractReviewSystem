package com.example.contractreview.model.vo;

import com.example.contractreview.enums.ReviewStage;
import com.example.contractreview.enums.ReviewStatus;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 审查进度VO (SSE推送)
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ReviewProgressVO {

    /**
     * 进度(0-100)
     */
    private Integer progress;

    /**
     * 当前阶段
     */
    private ReviewStage stage;

    /**
     * 状态
     */
    private ReviewStatus status;

    /**
     * 消息
     */
    private String message;
}
