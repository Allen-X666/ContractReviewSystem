package com.example.contractreview.model.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 通知设置DTO
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class NotificationSettingsDTO {

    /**
     * 审查完成通知
     */
    private Boolean reviewComplete;

    /**
     * 风险预警通知
     */
    private Boolean riskAlert;

    /**
     * 系统公告通知
     */
    private Boolean systemNotice;

    /**
     * 邮件通知
     */
    private Boolean emailNotification;
}
