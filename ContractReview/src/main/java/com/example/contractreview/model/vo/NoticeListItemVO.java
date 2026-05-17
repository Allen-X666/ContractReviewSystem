package com.example.contractreview.model.vo;

import com.example.contractreview.enums.NoticeStatus;
import com.example.contractreview.enums.NoticeType;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 公告列表项VO
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class NoticeListItemVO {

    /**
     * 公告ID
     */
    private Long id;

    /**
     * 公告标题
     */
    private String title;

    /**
     * 公告类型
     */
    private NoticeType type;

    /**
     * 公告状态
     */
    private NoticeStatus status;

    /**
     * 发布时间
     */
    private LocalDateTime publishTime;

    /**
     * 发布人
     */
    private String author;

    /**
     * 是否置顶
     */
    private Boolean isTop;

    /**
     * 浏览次数
     */
    private Integer viewCount;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;
}
