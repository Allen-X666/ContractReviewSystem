package com.example.contractreview.model.vo;

import com.example.contractreview.enums.NoticeStatus;
import com.example.contractreview.enums.NoticeType;
import com.example.contractreview.enums.PublishType;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 公告详情VO
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class NoticeVO {

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
     * 公告内容（支持Markdown）
     */
    private String content;

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
}
