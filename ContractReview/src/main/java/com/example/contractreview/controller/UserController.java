package com.example.contractreview.controller;

import com.example.contractreview.common.Result;
import com.example.contractreview.model.dto.UpdateUserDTO;
import com.example.contractreview.model.vo.AvatarVO;
import com.example.contractreview.model.vo.GetNotificationSettings;
import com.example.contractreview.service.UserService;
import com.fasterxml.jackson.core.JsonProcessingException;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@Slf4j
@RestController
@RequestMapping("/user")
@Tag(name = "用户接口")
@RequiredArgsConstructor
public class UserController {

    private final UserService userService;

    /**
     * 更新用户信息
     */
    @PutMapping("/profile")
    @Operation(summary = "更新用户信息")
    public Result<String> updateProfile(@RequestHeader("Authorization") String authorization,
                                        @RequestBody UpdateUserDTO updateUserDTO) {
        return userService.updateProfile(authorization, updateUserDTO);
    }

    /**
     * 上传头像
     */
    @PutMapping("/avatar")
    @Operation(summary = "上传头像")
    public Result<AvatarVO> uploadAvatar(@RequestHeader("Authorization") String authorization,
                                         @RequestBody MultipartFile file){
        return userService.uploadAvatar(authorization, file);
    }

    /**
     * 获取通知设置
     */
    @GetMapping("/notification-settings")
    @Operation(summary = "获取通知设置")
    public Result<GetNotificationSettings> getNotificationSettings(@RequestHeader("Authorization") String authorization) throws JsonProcessingException {
        return userService.getNotificationSettings(authorization);
    }

    /**
     * 更新通知设置
     */
    @PutMapping("/notification-settings")
    @Operation(summary = "更新通知设置")
    public Result<String> updateNotificationSettings(@RequestHeader("Authorization") String authorization,
                                                     @RequestBody GetNotificationSettings getNotificationSettings){
        return userService.updateNotificationSettings(authorization, getNotificationSettings);
    }
}
