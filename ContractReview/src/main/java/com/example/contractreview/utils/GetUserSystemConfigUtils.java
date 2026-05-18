package com.example.contractreview.utils;

import com.example.contractreview.common.Result;
import com.example.contractreview.constant.UserConstant;
import com.example.contractreview.model.vo.GetNotificationSettings;
import com.example.contractreview.model.vo.UserVO;
import com.example.contractreview.service.AuthService;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;

import java.util.Map;

@Component
@RequiredArgsConstructor
public class GetUserSystemConfigUtils {

    private StringRedisTemplate stringRedisTemplate;
    private ObjectMapper objectMapper;
    private AuthService authService;

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
        Result<UserVO> userInfo = authService.getUserInfo(userId);
        return userInfo.getData().getEmail();
    }
}
