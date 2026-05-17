package com.example.contractreview.model.vo.fastapi;

import lombok.Data;

import java.util.List;

@Data
public class RiskItemVO {

    private Long id;
    private String level;
    private String clause;
    private String description;
    private LocationVO location;
    private List<LawReferenceVO> lawReferences;
    private String suggestion;
}
