package com.example.contractreview.utils;

import com.example.contractreview.enums.NotificationType;
import com.example.contractreview.service.AsyncMailService;
import com.fasterxml.jackson.core.JsonProcessingException;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;

import java.util.Map;

@Component
@RequiredArgsConstructor
public class UserEmailUtils {

    private final GetUserSystemConfigUtils getUserSystemConfigUtils;
    private final AsyncMailService asyncMailService;

    public void userEmailUtils(Integer userId, String title, String messages) throws JsonProcessingException {
        Map<String, String> userSystemConfig = getUserSystemConfigUtils.getUserSystemConfig(userId);
        String message = userSystemConfig.get("message");
        if (message.equals("获取用户系统配置成功")) {
            String email = userSystemConfig.get("emailNotification");
            if (email.equals("true")) {
                String userEmail = getUserSystemConfigUtils.getUserEmail(userId);
                asyncMailService.sendNotificationEmail(
                        userEmail,
                        NotificationType.EMAIL_NOTIFICATION,
                        title,
                        messages);
            }
        }
    }
}
