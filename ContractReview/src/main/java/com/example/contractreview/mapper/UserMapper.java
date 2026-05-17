package com.example.contractreview.mapper;

import com.example.contractreview.model.dto.UpdateUserDTO;
import com.example.contractreview.model.vo.GetNotificationSettings;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

@Mapper
public interface UserMapper {

    /**
     * 更新用户信息
     *
     * @param updateUserDTO 用户信息DTO
     * @param userId 用户ID
     */
    void update(@Param("updateUserDTO") UpdateUserDTO updateUserDTO, @Param("userId") Integer userId);

    /**
     * 更新用户头像
     *
     * @param avatarUrl 头像URL
     * @param userId 用户ID
     */
    void updateAvatar(@Param("avatarUrl") String avatarUrl, @Param("userId") Integer userId);

    /**
     * 获取用户通知设置
     *
     * @param userId 用户ID
     * @return 通知设置
     */
    GetNotificationSettings getNotificationSettings(@Param("userId") Integer userId);

    /**
     * 更新用户通知设置
     *
     * @param notificationSettings 通知设置
     * @param userId 用户ID
     */
    void updateNotificationSettings(@Param("notificationSettings") GetNotificationSettings notificationSettings,
                                    @Param("userId") Integer userId);
}
