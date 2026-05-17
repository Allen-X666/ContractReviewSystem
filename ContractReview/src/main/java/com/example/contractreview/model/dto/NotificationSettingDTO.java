package com.example.contractreview.model.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 通知设置DTO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class NotificationSettingDTO {

    /**
     * 审查完成通知
     */
    private Boolean reviewComplete;

    /**
     * 高风险预警
     */
    private Boolean riskAlert;

    /**
     * 系统公告
     */
    private Boolean systemNotice;

    /**
     * 邮件通知
     */
    private Boolean emailNotification;
}
