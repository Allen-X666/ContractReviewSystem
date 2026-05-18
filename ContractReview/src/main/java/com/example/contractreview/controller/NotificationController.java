package com.example.contractreview.controller;

import com.example.contractreview.common.Result;
import com.example.contractreview.sse.SseEmitterManager;
import com.example.contractreview.utils.TokenUtils;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

/**
 * 通知控制器
 * 提供SSE订阅和通知管理接口
 */
@Slf4j
@RestController
@RequestMapping("/notifications")
@Tag(name = "通知接口")
@RequiredArgsConstructor
public class NotificationController {

    private final SseEmitterManager sseEmitterManager;
    private final TokenUtils tokenUtils;

    /**
     * SSE订阅通知流
     * 用于接收实时通知（审查完成、高风险预警等）
     *
     * @param token JWT token
     * @return SseEmitter 连接
     */
    @GetMapping(value = "/stream", produces = "text/event-stream")
    @Operation(summary = "SSE订阅通知流")
    public SseEmitter subscribe(@RequestParam("token") String token) {
        Integer userId = tokenUtils.getUserId("Bearer " + token);
        if (userId == null) {
            log.warn("SSE订阅失败：无效的token");
            throw new RuntimeException("无效的token");
        }
        log.info("用户 {} 开始订阅SSE通知流", userId);
        return sseEmitterManager.createEmitter(Long.valueOf(userId));
    }

    /**
     * 检查用户SSE连接状态
     *
     * @param authorization 授权头
     * @return 连接状态
     */
    @GetMapping("/connection-status")
    @Operation(summary = "检查SSE连接状态")
    public Result<Boolean> checkConnectionStatus(@RequestHeader("Authorization") String authorization) {
        Integer userId = tokenUtils.getUserId(authorization);
        boolean connected = sseEmitterManager.isConnected(Long.valueOf(userId));
        return Result.success(connected);
    }

    /**
     * 获取当前SSE连接数（管理员接口）
     *
     * @return 连接数
     */
    @GetMapping("/connection-count")
    @Operation(summary = "获取SSE连接数")
    public Result<Integer> getConnectionCount() {
        int count = sseEmitterManager.getConnectionCount();
        return Result.success(count);
    }
}
