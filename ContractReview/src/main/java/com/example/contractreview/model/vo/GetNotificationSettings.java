package com.example.contractreview.model.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class GetNotificationSettings {
    /**
     * {
     *   "code": 200,
     *   "message": "success",
     *   "data": {
     *     "reviewComplete": true,
     *     "riskAlert": true,
     *     "systemNotice": true,
     *     "emailNotification": false
     *   }
     * }
     */
    private Boolean reviewComplete;
    private Boolean riskAlert;
    private Boolean systemNotice;
    private Boolean emailNotification;
}
