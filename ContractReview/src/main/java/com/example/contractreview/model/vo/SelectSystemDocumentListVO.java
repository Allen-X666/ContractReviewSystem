package com.example.contractreview.model.vo;

import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.List;

@Data
public class SelectSystemDocumentListVO {
    private Integer id;
    private String name;
    private String category;
    private List<String> tags;
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime createAt;
}
