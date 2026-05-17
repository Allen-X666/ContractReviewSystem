package com.example.contractreview.config;

import com.example.contractreview.common.Result;
import com.example.contractreview.common.ResultCode;
import com.example.contractreview.utils.JwtUtils;
import com.example.contractreview.utils.TokenUtils;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.JwtException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.servlet.HandlerInterceptor;

@Slf4j
@Component
@RequiredArgsConstructor
public class AuthInterceptor implements HandlerInterceptor {

    private final TokenUtils tokenUtils;
    private final JwtUtils jwtUtils;
    private final ObjectMapper objectMapper;

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        String authorization = request.getHeader("Authorization");
        
        // 如果 Header 中没有 Authorization，尝试从 query parameter 获取（用于 SSE）
        if (!StringUtils.hasText(authorization)) {
            String tokenParam = request.getParameter("token");
            if (StringUtils.hasText(tokenParam)) {
                authorization = "Bearer " + tokenParam;
                log.debug("从 query parameter 获取 token");
            }
        }
        
        if (!StringUtils.hasText(authorization)) {
            sendErrorResponse(response, ResultCode.UNAUTHORIZED);
            return false;
        }

        try {
            String pureToken = tokenUtils.extractToken(authorization);
            
            if (tokenUtils.isTokenBlacklisted(pureToken)) {
                sendErrorResponse(response, ResultCode.TOKEN_EXPIRED_OR_INVALID);
                return false;
            }

            jwtUtils.parseJWT(pureToken);
            
            return true;
            
        } catch (ExpiredJwtException e) {
            log.warn("Token 已过期: {}", e.getMessage());
            sendErrorResponse(response, ResultCode.TOKEN_EXPIRED);
            return false;
        } catch (JwtException e) {
            log.warn("Token 验证失败: {}", e.getMessage());
            sendErrorResponse(response, ResultCode.TOKEN_INVALID);
            return false;
        } catch (Exception e) {
            log.error("Token 验证异常: {}", e.getMessage());
            sendErrorResponse(response, ResultCode.TOKEN_EXPIRED_OR_INVALID);
            return false;
        }
    }

    private void sendErrorResponse(HttpServletResponse response, ResultCode resultCode) throws Exception {
        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        response.setContentType(MediaType.APPLICATION_JSON_VALUE);
        response.setCharacterEncoding("UTF-8");
        
        Result<Void> result = Result.error(resultCode.getCode(), resultCode.getMessage());
        response.getWriter().write(objectMapper.writeValueAsString(result));
    }
}
