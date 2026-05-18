package com.example.contractreview.service;

import com.example.contractreview.common.Result;
import com.example.contractreview.model.dto.ChangePasswordDTO;
import com.example.contractreview.model.dto.LoginDTO;
import com.example.contractreview.model.dto.RegisterDTO;
import com.example.contractreview.model.dto.ResetPasswordDTO;
import com.example.contractreview.model.dto.SendCodeDTO;
import com.example.contractreview.model.vo.CaptchaVO;
import com.example.contractreview.model.vo.LoginVO;
import com.example.contractreview.model.vo.RegisterVO;
import com.example.contractreview.model.vo.UserVO;
import com.example.contractreview.model.vo.AuthVOPackage.SendCodeVO;
import com.fasterxml.jackson.core.JsonProcessingException;
import jakarta.validation.Valid;

public interface AuthService {
    // 用户注册
    Result<RegisterVO> register(@Valid RegisterDTO registerDTO);

    // 生成图形验证码
    Result<CaptchaVO> generateCaptcha(String source);

    // 发送验证码
    Result<SendCodeVO> sendCode(SendCodeDTO sendCodeDTO);

    // 用户登录
    Result<LoginVO> login(LoginDTO loginDTO);

    // 退出登录
    Result<Void> logout(String token);

    // 获取用户信息
    Result<UserVO> getUserInfo(Integer userId) throws JsonProcessingException;

    // 修改密码
    Result<String> changePassword(String authorization, @Valid ChangePasswordDTO changePasswordDTO) throws JsonProcessingException;

    // 刷新Token
    Result<LoginVO> refreshToken(String authorization);

    // 重置密码（忘记密码）
    Result<String> resetPassword(ResetPasswordDTO resetPasswordDTO);
}
