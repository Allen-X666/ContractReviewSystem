package com.example.contractreview.model.entity;

import com.example.contractreview.enums.NoticeStatus;
import com.example.contractreview.enums.NoticeType;
import com.example.contractreview.enums.PublishType;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 系统公告实体类
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Notice {

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
     * 公告内容
     */
    private String content;

    /**
     * 发布方式
     */
    private PublishType publishType;

    /**
     * 发布时间
     */
    private LocalDateTime publishTime;

    /**
     * 公告状态
     */
    private NoticeStatus status;

    /**
     * 是否置顶
     */
    private Boolean isTop;

    /**
     * 发布人ID
     */
    private Long authorId;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;

    /**
     * 更新时间
     */
    private LocalDateTime updatedAt;
}
