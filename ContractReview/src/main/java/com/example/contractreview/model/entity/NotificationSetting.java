package com.example.contractreview.model.entity;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 通知设置实体类
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class NotificationSetting {

    /**
     * 主键ID
     */
    private Long id;

    /**
     * 用户ID
     */
    private Long userId;

    /**
     * 审查完成通知: 0-关闭, 1-开启
     */
    private Boolean reviewComplete;

    /**
     * 高风险预警: 0-关闭, 1-开启
     */
    private Boolean riskAlert;

    /**
     * 系统公告: 0-关闭, 1-开启
     */
    private Boolean systemNotice;

    /**
     * 邮件通知: 0-关闭, 1-开启
     */
    private Boolean emailNotification;

    /**
     * 创建时间
     */
    private LocalDateTime createTime;

    /**
     * 更新时间
     */
    private LocalDateTime updateTime;
}
