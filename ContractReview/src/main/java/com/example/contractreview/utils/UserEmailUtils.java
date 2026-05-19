package com.example.contractreview.utils;

import com.example.contractreview.enums.NotificationType;
import com.example.contractreview.service.AsyncMailService;
import com.fasterxml.jackson.core.JsonProcessingException;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.stereotype.Service;

import java.util.Map;

@Component
@Slf4j
@RequiredArgsConstructor
public class UserEmailUtils {

    private final GetUserSystemConfigUtils getUserSystemConfigUtils;
    private final AsyncMailService asyncMailService;

    public void userEmailUtils(Integer userId, String title, String messages) throws JsonProcessingException {
        Map<String, String> userSystemConfig = getUserSystemConfigUtils.getUserSystemConfig(userId);
        String message = userSystemConfig.get("message");
        log.info("用户系统配置：{}", message);
        if (message.equals("获取用户系统配置成功")) {
            String email = userSystemConfig.get("emailNotification");
            log.info("用户邮箱通知：{}", email);
            if (email.equals("true")) {
                log.info("开始发送邮件");
                String userEmail = getUserSystemConfigUtils.getUserEmail(userId);
                asyncMailService.sendNotificationEmail(
                        userEmail,
                        NotificationType.EMAIL_NOTIFICATION,
                        title,
                        messages);
                log.info("发送邮件成功");
            }
            else {
                log.info("用户未开启邮件通知");
            }
        }
    }
}
