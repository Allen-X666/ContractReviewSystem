package com.example.contractreview.model.vo;

import lombok.Builder;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@Builder
public class ChatDetailVO {
    private Integer id;
    private String role;
    private String content;
    private LocalDateTime createTime;
}
