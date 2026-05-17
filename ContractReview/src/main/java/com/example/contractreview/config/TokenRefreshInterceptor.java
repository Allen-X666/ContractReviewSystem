package com.example.contractreview.config;

import com.example.contractreview.constant.UserConstant;
import com.example.contractreview.utils.JwtUtils;
import com.example.contractreview.utils.TokenUtils;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.servlet.HandlerInterceptor;

import java.util.concurrent.TimeUnit;

/**
 * Token自动刷新拦截器
 * 当用户token在过期前5分钟内有操作时，自动刷新token
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class TokenRefreshInterceptor implements HandlerInterceptor {

    private final JwtUtils jwtUtils;
    private final TokenUtils tokenUtils;
    private final StringRedisTemplate stringRedisTemplate;

    // 刷新阈值：5分钟
    private static final long REFRESH_THRESHOLD = 5 * 60 * 1000L;

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        // 从请求头中获取Authorization
        String authorization = request.getHeader("Authorization");
        log.debug("TokenRefreshInterceptor - 请求路径: {}, Authorization: {}", 
                request.getRequestURI(), 
                StringUtils.hasText(authorization) ? "存在" : "不存在");
        
        if (!StringUtils.hasText(authorization)) {
            return true;
        }

        // TokenUtils自动处理Bearer前缀
        // 验证token是否有效
        if (!tokenUtils.validateToken(authorization)) {
            log.debug("TokenRefreshInterceptor - Token验证失败");
            return true;
        }

        // 检查是否需要刷新（剩余时间小于5分钟）
        Long remainingTime = tokenUtils.getRemainingTime(authorization);
        log.debug("TokenRefreshInterceptor - Token剩余时间: {} ms", remainingTime);
        
        if (remainingTime == null || remainingTime < 0) {
            log.debug("TokenRefreshInterceptor - Token已过期或无效");
            return true;
        }

        // 如果剩余时间大于5分钟，不需要刷新
        if (remainingTime > REFRESH_THRESHOLD) {
            log.debug("TokenRefreshInterceptor - Token剩余时间充足，无需刷新");
            return true;
        }
        
        log.info("TokenRefreshInterceptor - Token需要刷新，剩余时间: {} ms", remainingTime);

        // 需要刷新token
        try {
            String newToken = tokenUtils.refreshToken(authorization);
            if (newToken == null) {
                log.warn("Token刷新失败");
                return true;
            }

            // 获取用户ID
            Integer userId = tokenUtils.getUserId(authorization);
            if (userId == null) {
                return true;
            }

            // 计算新的过期时间（秒）
            long tokenExpireSeconds = jwtUtils.getExpiration() / 1000;

            // 1. 【关键修复】不在当前请求中将旧token加入黑名单
            // 原因：当前请求仍在使用旧token，加入黑名单会导致当前请求在后续验证时失败
            // 旧token会在其自然过期时间后失效，无需立即加入黑名单
            // String pureToken = tokenUtils.extractToken(authorization);
            // String blacklistKey = UserConstant.TOKEN_BLACKLIST + pureToken;
            // stringRedisTemplate.opsForValue().set(blacklistKey, "1", remainingTime / 1000, TimeUnit.SECONDS);

            // 2. 更新用户token映射（使用新的过期时间）
            String userTokenKey = UserConstant.USER_TOKEN_MAP + userId;
            stringRedisTemplate.opsForValue().set(userTokenKey, newToken, tokenExpireSeconds, TimeUnit.SECONDS);

            // 3. 刷新用户登录状态缓存（user:info）的过期时间
            String userInfoKey = UserConstant.USER_INFO + userId;
            String userInfo = stringRedisTemplate.opsForValue().get(userInfoKey);
            if (userInfo != null) {
                // 如果存在用户信息缓存，刷新过期时间与token一致
                stringRedisTemplate.opsForValue().set(userInfoKey, userInfo, tokenExpireSeconds, TimeUnit.SECONDS);
                log.debug("用户 {} 的登录状态缓存已刷新，过期时间 {} 秒", userId, tokenExpireSeconds);
            }

            // 4. 在响应头中返回新token（必须在preHandle中设置，afterCompletion时响应已提交）
            response.setHeader("X-Refresh-Token", newToken);
            response.setHeader("X-Token-Refreshed", "true");

            log.info("用户 {} 的token已自动刷新，新的过期时间为 {} 秒", userId, tokenExpireSeconds);
        } catch (Exception e) {
            log.error("Token自动刷新失败: {}", e.getMessage());
        }

        return true;
    }
}
