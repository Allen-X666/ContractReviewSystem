package com.example.contractreview.model.vo.fastapi;

import lombok.Data;

import java.util.Map;

@Data
public class ReviewProgressVO {

    private Integer progress;
    private String stage;
    private String status;
    private String message;
    private Map<String, Integer> stageProgress;
}
