package com.example.contractreview.model.vo.fastapi;

import lombok.Data;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@Data
public class ReviewResultVO {

    private Long reviewId;
    private String reviewNo;
    private Integer contractId;
    private String contractName;
    private String status;
    private Integer overallScore;
    private String conclusion;
    private Map<String, Integer> riskSummary;
    private List<RiskItemVO> risks;
    private LocalDateTime completedAt;
}
