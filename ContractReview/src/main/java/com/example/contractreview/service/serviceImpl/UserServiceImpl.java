package com.example.contractreview.service.serviceImpl;

import com.example.contractreview.common.Result;
import com.example.contractreview.common.ResultCode;
import com.example.contractreview.constant.UserConstant;
import com.example.contractreview.mapper.UserMapper;
import com.example.contractreview.model.dto.UpdateUserDTO;
import com.example.contractreview.model.vo.AvatarVO;
import com.example.contractreview.model.vo.GetNotificationSettings;
import com.example.contractreview.service.UserService;
import com.example.contractreview.utils.AliyunOSSUtils;
import com.example.contractreview.utils.TokenUtils;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

@Service
@Slf4j
@RequiredArgsConstructor
public class UserServiceImpl implements UserService {

    private final UserMapper userMapper;
    private final TokenUtils tokenUtils;
    private final AliyunOSSUtils aliyunOSSUtils;
    private final StringRedisTemplate stringRedisTemplate;
    private final ObjectMapper objectMapper;

    /**
     * 更新用户信息
     *
     * @param authorization 认证令牌
     * @param updateUserDTO 用户信息DTO
     * @return 更新结果
     */
    @Override
    public Result<String> updateProfile(String authorization,
                                        UpdateUserDTO updateUserDTO) {
        Integer userId = tokenUtils.getUserId(authorization);
        log.info("更新用户信息, userId: {}", userId);
        if (userId == null) {
            return Result.error(ResultCode.UNAUTHORIZED, "用户未登录或登录已过期");
        }
        try {
            userMapper.update(updateUserDTO, userId);
            stringRedisTemplate.delete(UserConstant.USER_INFO + userId);
            return Result.success("更新成功");
        } catch (Exception e) {
            log.error("更新用户信息失败, userId: {}, error: {}", userId, e.getMessage());
            return Result.error("更新用户信息失败");
        }
    }

    /**
     * 上传用户头像
     *
     * @param authorization 认证令牌
     * @param file 头像文件
     * @return 头像URL
     */
    @Override
    public Result<AvatarVO> uploadAvatar(String authorization,
                                         MultipartFile file) {
        Integer userId = tokenUtils.getUserId(authorization);

        try {
            String avatarUrl = aliyunOSSUtils.asyncUploadAvatar(file, userId);
            userMapper.updateAvatar(avatarUrl, userId);

            AvatarVO avatarVO = AvatarVO.builder()
                    .avatarUrl(avatarUrl)
                    .build();
            return Result.success(avatarVO);

        } catch (IllegalArgumentException e) {
            log.warn("头像上传参数校验失败, userId: {}, error: {}", userId, e.getMessage());
            return Result.error("头像上传参数校验失败");
        } catch (Exception e) {
            log.error("头像上传失败, userId: {}, error: {}", userId, e.getMessage());
            return Result.error("头像上传失败，请稍后重试");
        }
    }

    /**
     * 获取用户通知设置
     *
     * @param authorization 认证令牌
     * @return 通知设置
     */
    @Override
    public Result<GetNotificationSettings> getNotificationSettings(String authorization) throws JsonProcessingException {
        Integer userId = tokenUtils.getUserId(authorization);
        String key = UserConstant.USER_NOTIFICATION_SETTINGS + userId;
        String cachNotification = stringRedisTemplate.opsForValue().get(key);
        if (cachNotification != null){
            GetNotificationSettings getNotificationSettings = objectMapper.readValue(cachNotification, GetNotificationSettings.class);
            return Result.success(getNotificationSettings);
        }
        try {
            GetNotificationSettings settings = userMapper.getNotificationSettings(userId);
            // 如果没有设置记录，返回默认设置
            if (settings == null) {
                settings = GetNotificationSettings.builder()
                        .reviewComplete(true)
                        .riskAlert(true)
                        .systemNotice(true)
                        .emailNotification(false)
                        .build();
            }
            stringRedisTemplate.opsForValue().set(key, objectMapper.writeValueAsString(settings));
            return Result.success(settings);
        } catch (Exception e) {
            log.error("获取用户通知设置失败, userId: {}, error: {}", userId, e.getMessage());
            return Result.error("获取通知设置失败");
        }
    }

    /**
     * 更新用户通知设置
     * @param authorization 认证令牌
     * @param notificationSettings 通知设置
     * @return 更新结果
     */
    @Override
    public Result<String> updateNotificationSettings(String authorization,
                                                     GetNotificationSettings notificationSettings) {
        Integer userId = tokenUtils.getUserId(authorization);
        if (userId == null) {
            return Result.error(ResultCode.UNAUTHORIZED, "用户未登录或登录已过期");
        }

        if (notificationSettings == null) {
            return Result.error(ResultCode.PARAM_ERROR, "通知设置不能为空");
        }

        try {
            String key = UserConstant.USER_NOTIFICATION_SETTINGS + userId;
            userMapper.updateNotificationSettings(notificationSettings, userId);
            stringRedisTemplate.delete(key);
            return Result.success("设置已保存");

        } catch (Exception e) {
            log.error("更新用户通知设置失败, userId: {}, error: {}", userId, e.getMessage());
            return Result.error("更新通知设置失败");
        }
    }
}
