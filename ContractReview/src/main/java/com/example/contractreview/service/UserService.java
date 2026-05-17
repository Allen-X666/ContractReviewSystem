package com.example.contractreview.service;

import com.example.contractreview.common.Result;
import com.example.contractreview.model.dto.UpdateUserDTO;
import com.example.contractreview.model.vo.AvatarVO;
import com.example.contractreview.model.vo.GetNotificationSettings;
import com.fasterxml.jackson.core.JsonProcessingException;
import org.springframework.web.multipart.MultipartFile;

public interface UserService {
    // 更新用户信息
    Result<String> updateProfile(String authorization, UpdateUserDTO updateUserDTO);

    // 更新头像
    Result<AvatarVO> uploadAvatar(String authorization, MultipartFile file);

    // 获取通知设置
    Result<GetNotificationSettings> getNotificationSettings(String authorization) throws JsonProcessingException;

    // 更新通知设置
    Result<String> updateNotificationSettings(String authorization, GetNotificationSettings getNotificationSettings);
}
