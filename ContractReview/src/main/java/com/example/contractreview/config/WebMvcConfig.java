package com.example.contractreview.config;

import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * Web MVC 配置类
 */
@Configuration
@RequiredArgsConstructor
public class WebMvcConfig implements WebMvcConfigurer {

    private final TokenRefreshInterceptor tokenRefreshInterceptor;
    private final AuthInterceptor authInterceptor;

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        // Token刷新拦截器先执行，确保在Token过期前能刷新
        registry.addInterceptor(tokenRefreshInterceptor)
                .addPathPatterns("/**")
                .excludePathPatterns(
                        "/api/auth/register",
                        "/api/auth/login",
                        "/api/auth/captcha",
                        "/api/auth/send-code",
                        "/api/auth/logout",
                        "/api/auth/refresh-token",
                        "/api/auth/reset-password",
                        "/api/notifications/stream",
                        "/auth/register",
                        "/auth/login",
                        "/auth/captcha",
                        "/auth/send-code",
                        "/auth/logout",
                        "/auth/refresh-token",
                        "/notifications/stream",
                        "/swagger-ui/**",
                        "/v3/api-docs/**",
                        "/swagger-resources/**",
                        "/webjars/**"
                )
                .order(1);

        // 认证拦截器后执行，验证Token有效性
        registry.addInterceptor(authInterceptor)
                .addPathPatterns("/**")
                .excludePathPatterns(
                        "/api/auth/register",
                        "/api/auth/login",
                        "/api/auth/captcha",
                        "/api/auth/send-code",
                        "/api/auth/logout",
                        "/api/auth/refresh-token",
                        "/api/auth/reset-password",
                        "/api/notifications/stream",
                        "/auth/register",
                        "/auth/login",
                        "/auth/captcha",
                        "/auth/send-code",
                        "/auth/logout",
                        "/auth/refresh-token",
                        "/notifications/stream",
                        "/swagger-ui/**",
                        "/v3/api-docs/**",
                        "/swagger-resources/**",
                        "/webjars/**"
                )
                .order(2);
    }
}
