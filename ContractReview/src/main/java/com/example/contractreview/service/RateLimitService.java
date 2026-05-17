package com.example.contractreview.service;

import com.example.contractreview.constant.UserConstant;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;

/**
 * 限流服务
 */
@Service
@Slf4j
@RequiredArgsConstructor
public class RateLimitService {

    private final StringRedisTemplate stringRedisTemplate;

    /**
     * 检查是否可以发送验证码（滑动窗口限流）
     *
     * @param target     目标（邮箱/手机号）
     * @param targetType 类型（email/phone）
     * @return true-可以发送，false-被限流
     */
    public boolean canSendCode(String target, String targetType) {
        String limitKey = UserConstant.RATE_LIMIT_PREFIX + targetType + ":" + target;
        String countKey = UserConstant.RATE_COUNT_PREFIX + targetType + ":" + target;

        // 1. 检查是否在冷却期内（60秒内只能发送一次）
        Boolean exists = stringRedisTemplate.hasKey(limitKey);
        if (Boolean.TRUE.equals(exists)) {
            Long ttl = stringRedisTemplate.getExpire(limitKey);
            log.warn("验证码发送过于频繁, target={}, 剩余冷却时间={}秒", target, ttl);
            return false;
        }

        // 2. 检查1小时内发送次数（最多5次）
        String countStr = stringRedisTemplate.opsForValue().get(countKey);
        if (countStr != null) {
            int count = Integer.parseInt(countStr);
            if (count >= 5) {
                log.warn("验证码发送次数超限, target={}, 1小时内已发送{}次", target, count);
                return false;
            }
        }

        return true;
    }

    /**
     * 记录验证码发送
     *
     * @param target     目标（邮箱/手机号）
     * @param targetType 类型（email/phone）
     */
    public void recordSendCode(String target, String targetType) {
        String limitKey = UserConstant.RATE_LIMIT_PREFIX + targetType + ":" + target;
        String countKey = UserConstant.RATE_COUNT_PREFIX + targetType + ":" + target;

        // 设置60秒冷却期
        stringRedisTemplate.opsForValue().set(limitKey, "1", Duration.ofSeconds(60));

        // 增加发送计数，1小时过期
        Long count = stringRedisTemplate.opsForValue().increment(countKey);
        if (count != null && count == 1) {
            stringRedisTemplate.expire(countKey, Duration.ofHours(1));
        }

        log.info("记录验证码发送, target={}, 当前小时内第{}次", target, count);
    }

    /**
     * 获取剩余冷却时间
     *
     * @param target     目标
     * @param targetType 类型
     * @return 剩余秒数，0表示无冷却
     */
    public long getRemainingCooldown(String target, String targetType) {
        String limitKey = UserConstant.RATE_LIMIT_PREFIX + targetType + ":" + target;
        Long ttl = stringRedisTemplate.getExpire(limitKey);
        return ttl != null && ttl > 0 ? ttl : 0;
    }
}
