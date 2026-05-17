package com.example.contractreview.model.entity;

import com.example.contractreview.enums.NotificationType;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 通知实体类
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Notification {

    /**
     * 通知ID
     */
    private Long id;

    /**
     * 用户ID
     */
    private Long userId;

    /**
     * 通知类型
     */
    private NotificationType type;

    /**
     * 通知标题
     */
    private String title;

    /**
     * 通知内容
     */
    private String content;

    /**
     * 关联数据（JSON格式）
     */
    private String data;

    /**
     * 是否已读: 0-未读, 1-已读
     */
    private Integer isRead;

    /**
     * 创建时间
     */
    private LocalDateTime createTime;

    /**
     * 更新时间
     */
    private LocalDateTime updateTime;
}
