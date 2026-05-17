package com.example.contractreview.model.dto;

import com.example.contractreview.enums.LawType;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 法律文档查询DTO
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class LawQueryDTO {

    /**
     * 页码，默认1
     */
    private Integer pageNum = 1;

    /**
     * 每页大小，默认10
     */
    private Integer pageSize = 10;

    /**
     * 文档类型筛选
     */
    private LawType type;

    /**
     * 文档名称关键字搜索
     */
    private String keyword;
}
