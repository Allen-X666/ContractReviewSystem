package com.example.contractreview.controller;

import com.example.contractreview.common.Result;
import com.example.contractreview.model.dto.*;
import com.example.contractreview.model.vo.AuthVOPackage.SendCodeVO;
import com.example.contractreview.model.vo.CaptchaVO;
import com.example.contractreview.model.vo.LoginVO;
import com.example.contractreview.model.vo.RegisterVO;
import com.example.contractreview.model.vo.UserVO;
import com.example.contractreview.service.AuthService;
import com.example.contractreview.utils.TokenUtils;
import com.fasterxml.jackson.core.JsonProcessingException;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

@RestController
@Slf4j
@Tag(name = "用户认证接口")
@RequestMapping("/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;
    private final TokenUtils tokenUtils;

    /**
     * 用户注册
     */
    @RequestMapping("/register")
    @Operation(summary = "用户注册")
    public Result<RegisterVO> register(@Valid @RequestBody RegisterDTO registerDTO) {
        return authService.register(registerDTO);
    }

    /**
     * 用户登录
     */
    @PostMapping("/login")
    @Operation(summary = "用户登录")
    public Result<LoginVO> login(@RequestBody LoginDTO loginDTO) {
        return authService.login(loginDTO);
    }

    /**
     * 获取图形验证码
     */
    @GetMapping("/captcha")
    @Operation(summary = "获取图形验证码")
    public Result<CaptchaVO> captcha(@RequestParam String source) {
        return authService.generateCaptcha(source);
    }

    /**
     * 发送验证码
     */
    @PostMapping("/send-code")
    @Operation(summary = "发送验证码")
    public Result<SendCodeVO> sendCode(@RequestBody SendCodeDTO sendCodeDTO) {
        return authService.sendCode(sendCodeDTO);
    }

    /**
     * 退出登录
     */
    @PostMapping("/logout")
    @Operation(summary = "退出登录")
    public Result<Void> logout(@RequestHeader("Authorization") String authorization) {
        return authService.logout(authorization);
    }

    /**
     * 获取用户信息
     */
    @GetMapping("/user-info")
    @Operation(summary = "获取用户信息")
    public Result<UserVO> getUserInfo(@RequestHeader("Authorization") String authorization) throws JsonProcessingException {
        Integer userId = tokenUtils.getUserId(authorization);
        return authService.getUserInfo(userId);
    }

    /**
     * 修改密码
     */
    @PostMapping("/change-password")
    @Operation(summary = "修改密码")
    public Result<String> changePassword(@RequestHeader("Authorization") String authorization,
                                         @RequestBody @Valid ChangePasswordDTO changePasswordDTO) throws JsonProcessingException {
        return authService.changePassword(authorization, changePasswordDTO);
    }

    /**
     * 刷新Token
     */
    @PostMapping("/refresh-token")
    @Operation(summary = "刷新Token")
    public Result<LoginVO> refreshToken(@RequestHeader("Authorization") String authorization) {
        return authService.refreshToken(authorization);
    }

    /**
     * 重置密码（忘记密码）
     */
    @PostMapping("/reset-password")
    @Operation(summary = "重置密码（忘记密码）")
    public Result<String> resetPassword(@RequestBody @Valid ResetPasswordDTO resetPasswordDTO) {
        return authService.resetPassword(resetPasswordDTO);
    }
}
