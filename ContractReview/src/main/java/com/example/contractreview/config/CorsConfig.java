package com.example.contractreview.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

import java.util.Arrays;
import java.util.List;

/**
 * CORS 跨域配置
 */
@Configuration
public class CorsConfig {

    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration configuration = new CorsConfiguration();
        // 允许所有来源（生产环境应该指定具体域名）
        configuration.setAllowedOriginPatterns(List.of("*"));
        // 允许的 HTTP 方法
        configuration.setAllowedMethods(Arrays.asList("GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"));
        // 允许的请求头
        configuration.setAllowedHeaders(Arrays.asList("*"));
        // 暴露的响应头（前端可以访问这些响应头）
        configuration.setExposedHeaders(Arrays.asList("X-Refresh-Token", "X-Token-Refreshed", "Authorization", "Content-Disposition"));
        // 允许携带凭证（Cookie、Authorization 等）
        configuration.setAllowCredentials(true);
        // 预检请求缓存时间（秒）
        configuration.setMaxAge(3600L);

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", configuration);
        return source;
    }
}
