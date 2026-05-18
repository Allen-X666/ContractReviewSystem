package com.example.contractreview.service.serviceImpl;

import com.example.contractreview.common.Result;
import com.example.contractreview.common.ResultCode;
import com.example.contractreview.common.exception.BusinessException;
import com.example.contractreview.constant.UserConstant;
import com.example.contractreview.enums.NotificationType;
import com.example.contractreview.enums.UserRole;
import com.example.contractreview.enums.UserStatus;
import com.example.contractreview.mapper.AuthMapper;
import com.example.contractreview.mapper.UserMapper;
import com.example.contractreview.model.dto.ChangePasswordDTO;
import com.example.contractreview.model.dto.LoginDTO;
import com.example.contractreview.model.dto.RegisterDTO;
import com.example.contractreview.model.dto.ResetPasswordDTO;
import com.example.contractreview.model.dto.SendCodeDTO;
import com.example.contractreview.model.entity.User;
import com.example.contractreview.model.vo.CaptchaVO;
import com.example.contractreview.model.vo.LoginVO;
import com.example.contractreview.model.vo.RegisterVO;
import com.example.contractreview.model.vo.UserVO;
import com.example.contractreview.model.vo.AuthVOPackage.SendCodeVO;
import com.example.contractreview.service.AsyncMailService;
import com.example.contractreview.service.AuthService;
import com.example.contractreview.service.RateLimitService;
import com.example.contractreview.utils.*;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.jsonwebtoken.Claims;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.BeanUtils;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.time.LocalDateTime;
import java.util.*;
import java.util.concurrent.TimeUnit;

@Service
@Slf4j
@RequiredArgsConstructor
public class AuthServiceImpl implements AuthService {

    private final StringRedisTemplate stringRedisTemplate;
    private final AuthMapper authMapper;
    private final JwtUtils jwtUtils;
    private final RandomCaptcha randomCaptcha;
    private final TokenUtils tokenUtils;
    private final ObjectMapper objectMapper;
    private final AsyncMailService asyncMailService;
    private final RateLimitService rateLimitService;
    private final UserEmailUtils userEmailUtils;
    private final GetUserSystemConfigUtils getUserSystemConfigUtils;

    /**
     * 用户注册
     * 注册方式优先级：
     * 1. email不为空 -> 邮箱注册，校验邮箱验证码
     * 2. phone不为空 -> 手机号注册，校验短信验证码
     * 3. 都为空 -> 用户名密码注册，校验图形验证码
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public Result<RegisterVO> register(RegisterDTO registerDTO) {
        String email = registerDTO.getEmail();
        String phone = registerDTO.getPhone();
        String captcha = registerDTO.getCode();
        String captchaId = registerDTO.getCaptchaId();

        // 1. 根据注册方式校验验证码
        String captchaKey;
        if (StringUtils.hasText(email)) {
            // 邮箱注册：校验邮箱验证码
            captchaKey = UserConstant.REGISTER_CAPTCHA_EMAIL + email;
        } else if (StringUtils.hasText(phone)) {
            // 手机号注册：校验短信验证码
            captchaKey = UserConstant.REGISTER_CAPTCHA_PHONE + phone;
        } else {
            // 用户名密码注册：校验图形验证码
            captchaKey = UserConstant.REGISTER_CAPTCHA_USERNAME + captchaId;
        }

        String cachedCaptcha = stringRedisTemplate.opsForValue().get(captchaKey);
        if (!StringUtils.hasText(cachedCaptcha)) {
            return Result.error(ResultCode.CAPTCHA_ERROR.getCode(), "验证码已过期");
        }
        if (!cachedCaptcha.equalsIgnoreCase(captcha)) {
            return Result.error(ResultCode.CAPTCHA_ERROR.getCode(), "验证码错误");
        }

        // 2. 校验密码一致性
        if (!registerDTO.getPassword().equals(registerDTO.getConfirmPassword())) {
            return Result.badRequest("两次输入的密码不一致");
        }

        // 3. 校验用户名是否已存在
        if (authMapper.existsByUsername(registerDTO.getUsername())) {
            return Result.error(ResultCode.USER_ALREADY_EXISTS);
        }

        // 4. 校验邮箱是否已注册（如果提供了邮箱）
        if (StringUtils.hasText(email) && authMapper.existsByEmail(email)) {
            return Result.error(ResultCode.USER_ALREADY_EXISTS.getCode(), "邮箱已被注册");
        }

        // 5. 校验手机号是否已注册（如果提供了手机号）
        if (StringUtils.hasText(phone) && authMapper.existsByPhone(phone)) {
            return Result.error(ResultCode.USER_ALREADY_EXISTS.getCode(), "手机号已被注册");
        }

        // 6. 创建用户实体
        // 前端已加密，后端进行二次MD5加密
        String frontendEncryptedPassword = registerDTO.getPassword();
        String finalEncryptedPassword = MD5Utils.md5(frontendEncryptedPassword);

        User user = User.builder()
                .username(registerDTO.getUsername())
                .password(finalEncryptedPassword)
                .nickName("暂未设置")
                .email(email)
                .phone(phone)
                .avatar(UserConstant.DEFAULT_AVATAR)
                .role(UserRole.USER)
                .status(UserStatus.ENABLED)
                .createdAt(LocalDateTime.now())
                .updatedAt(LocalDateTime.now())
                .build();

        // 7. 保存用户
        authMapper.insert(user);

        // 8. 删除已使用的验证码
        stringRedisTemplate.delete(captchaKey);

        // 9. 生成JWT Token
        Map<String, Object> claims = Map.of(
                "userId", user.getId(),
                "username", user.getUsername()
        );
        String token = jwtUtils.createJWT(claims);
        long expiresIn = jwtUtils.getExpiration();

        // 10. 构建响应
        RegisterVO registerVO = RegisterVO.builder()
                .userId(user.getId())
                .username(user.getUsername())
                .token(token)
                .expiresIn(expiresIn)
                .build();

        log.info("用户注册成功: username={}, userId={}", user.getUsername(), user.getId());

        return Result.success("注册成功", registerVO);
    }

    /**
     * 生成图形验证码
     */
    @Override
    public Result<CaptchaVO> generateCaptcha(String source) {
        // 1. 生成4位随机验证码
        String captchaCode = randomCaptcha.generateRandomCode(4);

        // 2. 生成唯一标识
        String captchaId = UUID.randomUUID().toString();

        // 3. 存入Redis，1分钟过期
        String redisKey;
        if (source.equals("register")) {
            redisKey = UserConstant.REGISTER_CAPTCHA_USERNAME + captchaId;
        } else {
            redisKey = UserConstant.LOGIN_CAPTCHA_USERNAME + captchaId;
        }
        stringRedisTemplate.opsForValue().set(redisKey, captchaCode, 1, TimeUnit.MINUTES);

        // 4. 生成验证码图片Base64
        String imageBase64 = generateCaptchaImageBase64(captchaCode);

        // 5. 构建响应
        CaptchaVO captchaVO = new CaptchaVO(captchaId, imageBase64);
        return Result.success(captchaVO);
    }

    /**
     * 发送验证码
     * 优化点：
     * 1. 限流防刷 - 60秒内只能发送一次，1小时内最多5次
     * 2. 异步发送 - 邮件/短信发送改为异步，立即返回响应
     * 3. 预生成响应 - 在发送前生成响应，减少用户等待时间
     */
    @Override
    public Result<SendCodeVO> sendCode(SendCodeDTO sendCodeDTO) {
        String target = sendCodeDTO.getTarget();
        String type = sendCodeDTO.getType();
        String targetType = sendCodeDTO.getTargetType();
        Integer expireSeconds = asyncMailService.getExpire();

        // 1. 限流检查
        if (!rateLimitService.canSendCode(target, targetType)) {
            long remainingSeconds = rateLimitService.getRemainingCooldown(target, targetType);
            if (remainingSeconds > 0) {
                return Result.error(ResultCode.TOO_MANY_REQUESTS.getCode(),
                        "发送过于频繁，请" + remainingSeconds + "秒后再试");
            }
            return Result.error(ResultCode.TOO_MANY_REQUESTS.getCode(),
                    "发送次数超限，请1小时后再试");
        }

        // 2. 生成验证码
        String code = randomCaptcha.generateRandomCode(4);

        // 3. 缓存验证码（使用Pipeline减少Redis往返）
        String key = buildCaptchaKey(targetType, type, target);
        stringRedisTemplate.opsForValue().set(key, code, expireSeconds, TimeUnit.SECONDS);

        // 4. 记录发送（限流计数）
        rateLimitService.recordSendCode(target, targetType);

        // 5. 异步发送验证码
        long startTime = System.currentTimeMillis();
        if ("email".equals(targetType)) {
            asyncMailService.sendVerifyCodeMailAsync(target, code, type, expireSeconds);
            log.info("邮箱验证码发送请求已提交, target={}, 耗时{}ms", target, System.currentTimeMillis() - startTime);
        } else if ("phone".equals(targetType)) {
            // 短信发送也改为异步
            sendSmsCodeAsync(target, code, type);
            log.info("短信验证码发送请求已提交, target={}, 耗时{}ms", target, System.currentTimeMillis() - startTime);
        }

        // 6. 立即返回响应（不等待发送完成）
        return Result.success("验证码已发送", SendCodeVO.builder()
                .expireSeconds(expireSeconds)
                .build());
    }

    /**
     * 异步发送短信验证码
     */
    private void sendSmsCodeAsync(String phone, String code, String type) {
        // 这里可以集成实际的短信服务商（阿里云、腾讯云等）
        // 目前仅记录日志，实际使用时需要替换为真实的短信发送逻辑
        log.info("异步发送短信验证码: phone={}, code={}, type={}", phone, code, type);
    }

    /**
     * 构建验证码缓存key
     */
    private String buildCaptchaKey(String targetType, String type, String target) {
        if ("email".equals(targetType)) {
            if ("register".equals(type)){
                return UserConstant.REGISTER_CAPTCHA_EMAIL + target;
            } else if ("login".equals(type)) {
                return UserConstant.LOGIN_CAPTCHA_EMAIL + target;
            } else {
                return UserConstant.RESETPASSWORD_CAPTCHA_EMAIL + target;
            }

        } else {
            return "register".equals(type)
                    ? UserConstant.REGISTER_CAPTCHA_PHONE + target
                    : UserConstant.LOGIN_CAPTCHA_PHONE + target;
        }
    }

    // 登录
    @Override
    @Transactional(rollbackFor = Exception.class)
    public Result<LoginVO> login(LoginDTO loginDTO) {
        String loginType = loginDTO.getLoginType();
        String username = loginDTO.getUsername();
        // 前端已加密，直接使用前端传来的加密密码进行验证
        String frontendEncryptedPassword = loginDTO.getPassword();
        String code = loginDTO.getCode();

        User user;
        switch (loginType) {
            case "account" ->
                    user = handleAccountLogin(username, frontendEncryptedPassword, code, loginDTO.getCaptchaId());
            case "phone" -> user = handlePhoneLogin(username, code);
            case "email" -> user = handleEmailLogin(username, code);
            case null, default -> {
                return Result.error("不支持的登录类型");
            }
        }

        if (user == null) {
            return Result.error(ResultCode.USER_NOT_FOUND);
        }

        return buildLoginResult(user);
    }

    /**
     * 处理账号密码登录
     */
    private User handleAccountLogin(String username, String frontendEncryptedPassword, String code, String captchaId) {
        // 验证图形验证码
        String captchaKey = UserConstant.LOGIN_CAPTCHA_USERNAME + captchaId;
        String captchaCode = stringRedisTemplate.opsForValue().get(captchaKey);
        if (captchaCode == null) {
            throw new BusinessException(ResultCode.CAPTCHA_EXPIRED.getCode(), "验证码已过期");
        }
        if (!captchaCode.equalsIgnoreCase(code)) {
            log.info("验证码错误:{},{}", stringRedisTemplate.opsForValue().get(captchaKey), code);
            throw new BusinessException(ResultCode.CAPTCHA_ERROR.getCode(), "验证码错误");
        }

        // 查询用户
        User user = authMapper.selectByUsername(username);
        if (user == null) {
            return null;
        }

        // 验证密码（前端已加密，后端用MD5二次加密存储，直接比较）
        String encryptedPassword = MD5Utils.md5(frontendEncryptedPassword);
        if (!encryptedPassword.equals(user.getPassword())) {
            throw new BusinessException(ResultCode.USERNAME_OR_PASSWORD_ERROR.getCode(), "用户名或密码错误");
        }

        return user;
    }

    /**
     * 处理手机号登录
     */
    private User handlePhoneLogin(String phone, String code) {
        // 验证短信验证码
        String captchaKey = UserConstant.LOGIN_CAPTCHA_PHONE + phone;
        String cachedCode = stringRedisTemplate.opsForValue().get(captchaKey);

        if (!StringUtils.hasText(cachedCode)) {
            throw new BusinessException(ResultCode.CAPTCHA_EXPIRED.getCode(), "验证码已过期");
        }
        if (!cachedCode.equalsIgnoreCase(code)) {
            throw new BusinessException(ResultCode.CAPTCHA_ERROR.getCode(), "验证码错误");
        }

        // 验证成功后删除验证码（防止重放攻击）
        stringRedisTemplate.delete(captchaKey);

        return authMapper.selectByPhone(phone);
    }

    /**
     * 处理邮箱登录
     */
    private User handleEmailLogin(String email, String code) {
        // 验证邮箱验证码
        String captchaKey = UserConstant.LOGIN_CAPTCHA_EMAIL + email;
        String cachedCode = stringRedisTemplate.opsForValue().get(captchaKey);

        if (!StringUtils.hasText(cachedCode)) {
            throw new BusinessException(ResultCode.CAPTCHA_EXPIRED.getCode(), "验证码已过期");
        }
        if (!cachedCode.equalsIgnoreCase(code)) {
            throw new BusinessException(ResultCode.CAPTCHA_ERROR.getCode(), "验证码错误");
        }

        // 验证成功后删除验证码（防止重放攻击）
        stringRedisTemplate.delete(captchaKey);

        return authMapper.selectByEmail(email);
    }

    /**
     * 构建登录结果
     * 单点登录：如果用户已在其他设备登录，阻止本次登录
     */
    private Result<LoginVO> buildLoginResult(User user) {
        // 单点登录检查：检查用户是否已在其他设备登录
        String userTokenKey = UserConstant.USER_TOKEN_MAP + user.getId();
        String oldToken = stringRedisTemplate.opsForValue().get(userTokenKey);
        if (StringUtils.hasText(oldToken)) {
            // 检查旧token是否仍然有效
            Long remainingTime = jwtUtils.getRemainingTime(oldToken);
            if (remainingTime != null && remainingTime > 0) {
                log.warn("用户 {} 尝试二次登录，已被阻止", user.getUsername());
                return Result.error(ResultCode.USER_ALREADY_LOGIN);
            }
        }

        // 生成新token
        String token = jwtUtils.createJWT(Map.of(
                "userId", user.getId(),
                "username", user.getUsername(),
                "role", user.getRole().name()
        ));

        // 存储新token到用户token映射
        long tokenExpireSeconds = jwtUtils.getExpiration() / 1000;
        stringRedisTemplate.opsForValue().set(userTokenKey, token, tokenExpireSeconds, TimeUnit.SECONDS);

        UserVO userVO = new UserVO();
        BeanUtils.copyProperties(user, userVO);
        userVO.setRole(String.valueOf(user.getRole()));

        LoginVO loginVO = LoginVO.builder()
                .token(token)
                .expiresIn(jwtUtils.getExpiration())
                .userInfo(userVO)
                .build();

        return Result.success(loginVO);
    }

    /**
     * 生成验证码图片并转为Base64
     */
    private String generateCaptchaImageBase64(String code) {
        int width = 120;
        int height = 40;

        // 创建图片
        BufferedImage image = new BufferedImage(width, height, BufferedImage.TYPE_INT_RGB);
        Graphics2D g = image.createGraphics();

        // 设置背景色
        g.setColor(new Color(240, 240, 240));
        g.fillRect(0, 0, width, height);

        // 添加干扰线
        Random random = new Random();
        g.setColor(new Color(200, 200, 200));
        for (int i = 0; i < 5; i++) {
            int x1 = random.nextInt(width);
            int y1 = random.nextInt(height);
            int x2 = random.nextInt(width);
            int y2 = random.nextInt(height);
            g.drawLine(x1, y1, x2, y2);
        }

        // 添加噪点
        for (int i = 0; i < 50; i++) {
            int x = random.nextInt(width);
            int y = random.nextInt(height);
            g.setColor(new Color(random.nextInt(255), random.nextInt(255), random.nextInt(255)));
            g.drawRect(x, y, 1, 1);
        }

        // 绘制验证码文字
        g.setFont(new Font("Arial", Font.BOLD, 24));
        for (int i = 0; i < code.length(); i++) {
            // 随机颜色
            g.setColor(new Color(random.nextInt(100), random.nextInt(100), random.nextInt(100)));
            // 随机旋转（减小角度避免遮挡）
            int x = 20 + i * 25;
            int y = 28;
            double rotation = (random.nextDouble() - 0.5) * 0.15; // 从0.3改为0.15，减小倾斜
            g.rotate(rotation, x, y);
            g.drawString(String.valueOf(code.charAt(i)), x, y);
            g.rotate(-rotation, x, y);
        }

        g.dispose();

        // 转为Base64
        try {
            ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
            ImageIO.write(image, "png", outputStream);
            byte[] imageBytes = outputStream.toByteArray();
            String base64 = Base64.getEncoder().encodeToString(imageBytes);
            return "data:image/png;base64," + base64;
        } catch (Exception e) {
            log.error("生成验证码图片失败", e);
            throw new RuntimeException("生成验证码图片失败");
        }
    }

    /**
     * 退出登录
     * 将token加入黑名单，使其失效
     */
    @Override
    public Result<Void> logout(String authorization) {
        try {
            // 提取纯token（去掉Bearer前缀）
            String token = tokenUtils.extractToken(authorization);

            // 解析token获取过期时间和用户信息
            Long remainingTime = jwtUtils.getRemainingTime(token);

            // 如果token已过期，直接返回成功
            if (remainingTime != null && remainingTime < 0) {
                return Result.success();
            }

            // 计算token剩余有效时间（秒）
            long expireSeconds = remainingTime != null ? remainingTime / 1000 : jwtUtils.getExpiration() / 1000;

            // 将token加入黑名单，设置过期时间为token的剩余有效时间
            String blacklistKey = UserConstant.TOKEN_BLACKLIST + token;
            stringRedisTemplate.opsForValue().set(blacklistKey, "1", expireSeconds, TimeUnit.SECONDS);

            // 清除用户token映射
            try {
                Claims claims = jwtUtils.parseJWT(token);
                Integer userId = claims.get("userId", Integer.class);
                if (userId != null) {
                    String userTokenKey = UserConstant.USER_TOKEN_MAP + userId;
                    String storedToken = stringRedisTemplate.opsForValue().get(userTokenKey);
                    // 只清除当前token对应的映射
                    if (token.equals(storedToken)) {
                        stringRedisTemplate.delete(userTokenKey);
                    }
                }
            } catch (Exception e) {
                log.warn("清除用户token映射失败: {}", e.getMessage());
            }
            return Result.success();
        } catch (Exception e) {
            log.error("退出登录失败: {}", e.getMessage());
            return Result.error("退出登录失败");
        }
    }

    // 获取用户信息
    @Override
    public Result<UserVO> getUserInfo(Integer userId) throws JsonProcessingException {
        if (userId != null) {
            // 先从Redis中获取用户信息
            String userInfoKey = UserConstant.USER_INFO + userId;
            String cachUserInfo = stringRedisTemplate.opsForValue().get(userInfoKey);
            if (cachUserInfo != null) {
                UserVO cachUserVO = objectMapper.readValue(cachUserInfo, UserVO.class);
                return Result.success(cachUserVO);
            }
            User user = authMapper.selectById(userId);
            if (user != null) {
                UserVO userVO = new UserVO();
                BeanUtils.copyProperties(user, userVO);
                userVO.setRole(user.getRole() != null ? user.getRole().getCode() : null);
                // 写入Redis，设置过期时间与token一致
                long tokenExpireSeconds = jwtUtils.getExpiration() / 1000;
                stringRedisTemplate.opsForValue().set(userInfoKey, objectMapper.writeValueAsString(userVO), tokenExpireSeconds, TimeUnit.SECONDS);
                return Result.success(userVO);
            }
            return Result.error(ResultCode.USER_NOT_FOUND);
        }
        return Result.error(ResultCode.USER_NOT_FOUND);
    }

    // 修改密码
    @Override
    public Result<String> changePassword(String authorization, @Valid ChangePasswordDTO changePasswordDTO) throws JsonProcessingException {
        // 获取用户id
        Integer userId = tokenUtils.getUserId(authorization);
        if (userId != null) {
            User user = authMapper.selectById(userId);
            if (!user.getPassword().equals(MD5Utils.md5(changePasswordDTO.getOldPassword()))){
                return Result.error(ResultCode.USER_PASSWORD_ERROR);
            }
            if (!changePasswordDTO.getNewPassword().equals(changePasswordDTO.getConfirmPassword())){
                return Result.error(ResultCode.USER_PASSWORD_NOT_MATCH);
            }
            user.setPassword(MD5Utils.md5(changePasswordDTO.getNewPassword()));
            authMapper.update(user);
            userEmailUtils.userEmailUtils(userId, "密码修改成功", "密码修改成功，请返回系统登录。");
            return Result.success("密码修改成功");
        }
        return Result.error("密码修改失败");
    }

    @Override
    public Result<LoginVO> refreshToken(String authorization) {
        String pureToken = tokenUtils.extractToken(authorization);

        if (tokenUtils.isTokenBlacklisted(pureToken)) {
            return Result.error(ResultCode.TOKEN_EXPIRED_OR_INVALID);
        }

        io.jsonwebtoken.Claims claims;
        try {
            claims = jwtUtils.parseJWTWithoutExpiration(pureToken);
        } catch (Exception e) {
            log.warn("refreshToken - 解析token失败: {}", e.getMessage());
            return Result.error(ResultCode.TOKEN_INVALID);
        }

        Object userIdObj = claims.get("userId");
        if (!(userIdObj instanceof Number)) {
            return Result.error(ResultCode.TOKEN_INVALID);
        }
        Integer userId = ((Number) userIdObj).intValue();

        String userTokenKey = UserConstant.USER_TOKEN_MAP + userId;
        String storedToken = stringRedisTemplate.opsForValue().get(userTokenKey);
        if (!pureToken.equals(storedToken)) {
            return Result.error(ResultCode.TOKEN_EXPIRED_OR_INVALID);
        }

        String username = (String) claims.get("username");
        String role = (String) claims.get("role");

        String newToken = jwtUtils.createJWT(java.util.Map.of(
                "userId", userId,
                "username", username != null ? username : "",
                "role", role != null ? role : ""
        ));
        long tokenExpireSeconds = jwtUtils.getExpiration() / 1000;

        stringRedisTemplate.opsForValue().set(userTokenKey, newToken, tokenExpireSeconds, TimeUnit.SECONDS);

        String userInfoKey = UserConstant.USER_INFO + userId;
        String userInfo = stringRedisTemplate.opsForValue().get(userInfoKey);
        if (userInfo != null) {
            stringRedisTemplate.opsForValue().set(userInfoKey, userInfo, tokenExpireSeconds, TimeUnit.SECONDS);
        }

        log.info("用户 {} 的token已通过接口刷新", userId);

        LoginVO loginVO = LoginVO.builder()
                .token(newToken)
                .expiresIn(jwtUtils.getExpiration())
                .build();

        return Result.success(loginVO);
    }

    // 重置密码（忘记密码）
    @Override
    public Result<String> resetPassword(ResetPasswordDTO resetPasswordDTO) {
        String newPassword = resetPasswordDTO.getNewPassword();
        String confirmPassword = resetPasswordDTO.getConfirmPassword();
        String key = UserConstant.RESETPASSWORD_CAPTCHA_EMAIL + resetPasswordDTO.getEmail();
        String cachCode = stringRedisTemplate.opsForValue().get(key);
        if (cachCode != null && cachCode.equalsIgnoreCase(resetPasswordDTO.getCode())) {
            if (!Objects.equals(newPassword, confirmPassword)){
                return Result.error(ResultCode.USER_PASSWORD_NOT_MATCH);
            }
            String password = authMapper.selectByEmail(resetPasswordDTO.getEmail()).getPassword();
            if (password.equals(MD5Utils.md5(newPassword))){
                return Result.error(ResultCode.USER_PASSWORD_NOT_CHANGE);
            }
            authMapper.updatePassword(resetPasswordDTO.getEmail(), MD5Utils.md5(newPassword));
            stringRedisTemplate.delete("user:list:");
            return Result.success("密码重置成功");
        }
        return Result.error(ResultCode.CAPTCHA_ERROR);
    }
}
