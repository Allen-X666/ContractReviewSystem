package com.example.contractreview.utils;

import com.example.contractreview.constant.UserConstant;
import com.example.contractreview.mapper.AuthMapper;
import com.example.contractreview.model.entity.User;
import com.example.contractreview.model.vo.GetNotificationSettings;
import com.example.contractreview.model.vo.UserVO;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;

import java.util.Map;

@Component
@RequiredArgsConstructor
public class GetUserSystemConfigUtils {

    private final StringRedisTemplate stringRedisTemplate;
    private final ObjectMapper objectMapper;
    private final AuthMapper authMapper;

    public Map<String, String> getUserSystemConfig(Integer userId) {
        String key = UserConstant.USER_NOTIFICATION_SETTINGS + userId;
        String userSystemConfig = stringRedisTemplate.opsForValue().get(key);
        Map<String, String> userSystemConfigMap = new java.util.HashMap<>(Map.of());
        try {
            GetNotificationSettings getNotificationSettings = objectMapper.readValue(userSystemConfig, GetNotificationSettings.class);
            userSystemConfigMap.put("message", "获取用户系统配置成功");
            userSystemConfigMap.put("reviewComplete", getNotificationSettings.getReviewComplete().toString());
            userSystemConfigMap.put("riskAlert", getNotificationSettings.getRiskAlert().toString());
            userSystemConfigMap.put("systemNotice", getNotificationSettings.getSystemNotice().toString());
            userSystemConfigMap.put("emailNotification", getNotificationSettings.getEmailNotification().toString());
        } catch (Exception e) {
            userSystemConfigMap.put("message", "获取用户系统配置失败");
        }
        return userSystemConfigMap;
    }

    public String getUserEmail(Integer userId) throws JsonProcessingException {
        String key = UserConstant.USER_INFO + userId;
        String cacheUserInfo = stringRedisTemplate.opsForValue().get(key);
        if (cacheUserInfo != null){
            UserVO userVO = objectMapper.readValue(cacheUserInfo, UserVO.class);
            return userVO.getEmail();
        }
        // 使用 AuthMapper 直接查询，避免循环依赖
        User user = authMapper.selectById(userId);
        return user != null ? user.getEmail() : null;
    }
}
