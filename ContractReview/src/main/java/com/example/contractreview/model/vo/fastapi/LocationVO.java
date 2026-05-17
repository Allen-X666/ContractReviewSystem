package com.example.contractreview.model.vo.fastapi;

import lombok.Data;

@Data
public class LocationVO {

    private Integer paragraphIndex;
    private Integer startOffset;
    private Integer endOffset;
    private String text;
}
