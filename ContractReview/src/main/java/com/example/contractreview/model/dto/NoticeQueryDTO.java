package com.example.contractreview.model.dto;

import com.example.contractreview.enums.NoticeStatus;
import com.example.contractreview.enums.NoticeType;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 公告列表查询DTO
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class NoticeQueryDTO {

    /**
     * 页码，默认1
     */
    private Integer pageNum = 1;

    /**
     * 每页大小，默认10
     */
    private Integer pageSize = 10;

    /**
     * 公告类型筛选
     */
    private NoticeType type;

    /**
     * 公告状态筛选
     */
    private NoticeStatus status;

    /**
     * 公告标题关键字搜索
     */
    private String keyword;
}
