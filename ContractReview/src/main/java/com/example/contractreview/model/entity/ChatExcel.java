package com.example.contractreview.model.entity;

import com.alibaba.excel.annotation.ExcelProperty;
import lombok.Builder;
import lombok.Data;

import java.time.LocalDate;
import java.time.LocalDateTime;

@Data
@Builder
public class ChatExcel {

    @ExcelProperty("编号")
    private Integer id;

    @ExcelProperty("角色")
    private String role;

    @ExcelProperty("内容")
    private String content;

    @ExcelProperty("时间")
    private LocalDateTime createTime;
}
