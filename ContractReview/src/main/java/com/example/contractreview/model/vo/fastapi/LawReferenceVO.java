package com.example.contractreview.model.vo.fastapi;

import lombok.Data;

@Data
public class LawReferenceVO {

    private Long id;
    private String name;
    private String article;
    private String content;
    private String interpretation;
}
