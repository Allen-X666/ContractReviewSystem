package com.example.contractreview.sse;

import com.example.contractreview.enums.NotificationType;
import lombok.Builder;
import lombok.Data;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.IOException;
import java.time.LocalDateTime;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * SSE 连接管理器
 * 管理所有用户的 SSE 连接
 */
@Slf4j
@Component
public class SseEmitterManager {

    /**
     * 存储用户ID与SseEmitter的映射关系
     */
    private final Map<Long, SseEmitter> emitters = new ConcurrentHashMap<>();

    /**
     * 连接超时时间（毫秒）
     */
    private static final Long DEFAULT_TIMEOUT = 0L;

    /**
     * 创建 SSE 连接
     *
     * @param userId 用户ID
     * @return SseEmitter 实例
     */
    public SseEmitter createEmitter(Long userId) {
        // 如果已存在连接，先移除旧的
        removeEmitter(userId);

        // 创建新的 SseEmitter，0表示永不超时
        SseEmitter emitter = new SseEmitter(DEFAULT_TIMEOUT);

        // 存储连接
        emitters.put(userId, emitter);
        log.info("SSE连接已创建，用户ID: {}，当前连接数: {}", userId, emitters.size());

        // 连接完成时的回调
        emitter.onCompletion(() -> {
            log.info("SSE连接已完成，用户ID: {}", userId);
            emitters.remove(userId);
        });

        // 连接超时时的回调
        emitter.onTimeout(() -> {
            log.warn("SSE连接已超时，用户ID: {}", userId);
            emitters.remove(userId);
        });

        // 连接出错时的回调
        emitter.onError((e) -> {
            log.error("SSE连接发生错误，用户ID: {}，错误: {}", userId, e.getMessage());
            emitters.remove(userId);
        });

        // 发送连接成功事件
        try {
            emitter.send(SseEmitter.event()
                    .name("connect")
                    .data("连接成功"));
        } catch (IOException e) {
            log.error("发送连接成功事件失败，用户ID: {}", userId, e);
        }

        return emitter;
    }

    /**
     * 移除 SSE 连接
     *
     * @param userId 用户ID
     */
    public void removeEmitter(Long userId) {
        SseEmitter emitter = emitters.remove(userId);
        if (emitter != null) {
            try {
                emitter.complete();
                log.info("SSE连接已移除，用户ID: {}", userId);
            } catch (Exception e) {
                log.error("关闭SSE连接失败，用户ID: {}", userId, e);
            }
        }
    }

    /**
     * 发送消息给指定用户
     *
     * @param userId  用户ID
     * @param eventName 事件名称
     * @param data    消息数据
     * @return 是否发送成功
     */
    public boolean sendToUser(Long userId, String eventName, Object data) {
        SseEmitter emitter = emitters.get(userId);
        if (emitter == null) {
            log.warn("用户 {} 未建立SSE连接，无法发送消息", userId);
            return false;
        }

        try {
            emitter.send(SseEmitter.event()
                    .name(eventName)
                    .data(data));
            return true;
        } catch (IOException e) {
            log.error("发送SSE消息失败，用户ID: {}，事件: {}", userId, eventName, e);
            // 发送失败，移除连接
            removeEmitter(userId);
            return false;
        }
    }

    /**
     * 发送消息给所有用户
     *
     * @param eventName 事件名称
     * @param data    消息数据
     */
    public void sendToAll(String eventName, Object data) {
        emitters.forEach((userId, emitter) -> {
            try {
                emitter.send(SseEmitter.event()
                        .name(eventName)
                        .data(data));
            } catch (IOException e) {
                log.error("广播SSE消息失败，用户ID: {}，事件: {}", userId, eventName, e);
                removeEmitter(userId);
            }
        });
    }

    /**
     * 发送心跳消息给所有连接
     */
    public void sendHeartbeat() {
        emitters.forEach((userId, emitter) -> {
            try {
                emitter.send(SseEmitter.event()
                        .name("heartbeat")
                        .data("ping"));
            } catch (IOException e) {
                log.error("发送心跳失败，用户ID: {}", userId, e);
                removeEmitter(userId);
            }
        });
    }

    /**
     * 获取当前连接数
     *
     * @return 连接数
     */
    public int getConnectionCount() {
        return emitters.size();
    }

    /**
     * 检查用户是否已连接
     *
     * @param userId 用户ID
     * @return 是否已连接
     */
    public boolean isConnected(Long userId) {
        return emitters.containsKey(userId);
    }

    /**
     * 发送审查完成通知
     *
     * @param userId     用户ID
     * @param reviewId   审查ID
     * @param contractId 合同ID
     * @param contractName 合同名称
     * @param score      评分
     * @return 是否发送成功
     */
    public boolean sendReviewCompleteNotification(Long userId, Long reviewId, Long contractId, 
                                                   String contractName, Integer score) {
        NotificationData data = NotificationData.builder()
                .type(NotificationType.REVIEW_COMPLETE)
                .title("审查完成")
                .message(String.format("合同《%s》审查已完成，综合评分：%d分", contractName, score))
                .reviewId(reviewId)
                .contractId(contractId)
                .contractName(contractName)
                .score(score)
                .timestamp(LocalDateTime.now())
                .build();
        return sendToUser(userId, "review_complete", data);
    }

    /**
     * 发送高风险预警通知
     *
     * @param userId       用户ID
     * @param reviewId     审查ID
     * @param contractId   合同ID
     * @param contractName 合同名称
     * @param riskCount    高风险数量
     * @return 是否发送成功
     */
    public boolean sendHighRiskWarningNotification(Long userId, Long reviewId, Long contractId,
                                                    String contractName, Integer riskCount) {
        NotificationData data = NotificationData.builder()
                .type(NotificationType.HIGH_RISK_WARNING)
                .title("高风险预警")
                .message(String.format("合同《%s》检测到 %d 个高风险项，请重点关注", contractName, riskCount))
                .reviewId(reviewId)
                .contractId(contractId)
                .contractName(contractName)
                .riskCount(riskCount)
                .timestamp(LocalDateTime.now())
                .build();
        return sendToUser(userId, "high_risk_warning", data);
    }

    /**
     * 发送系统公告通知（给单个用户）
     *
     * @param userId  用户ID
     * @param title   公告标题
     * @param content 公告内容
     * @return 是否发送成功
     */
    public boolean sendSystemAnnouncement(Long userId, String title, String content) {
        NotificationData data = NotificationData.builder()
                .type(NotificationType.SYSTEM_ANNOUNCEMENT)
                .title(title)
                .message(content)
                .timestamp(LocalDateTime.now())
                .build();
        return sendToUser(userId, "system_announcement", data);
    }

    /**
     * 广播系统公告通知（给所有在线用户）
     *
     * @param title   公告标题
     * @param content 公告内容
     * @return 发送的目标用户数
     */
    public int broadcastSystemAnnouncement(String title, String content) {
        NotificationData data = NotificationData.builder()
                .type(NotificationType.SYSTEM_ANNOUNCEMENT)
                .title(title)
                .message(content)
                .timestamp(LocalDateTime.now())
                .build();
        sendToAll("system_announcement", data);
        return emitters.size();
    }

    /**
     * 通知数据对象
     */
    @Data
    @Builder
    public static class NotificationData {
        private NotificationType type;
        private String title;
        private String message;
        private Long reviewId;
        private Long contractId;
        private String contractName;
        private Integer score;
        private Integer riskCount;
        private LocalDateTime timestamp;
    }
}
