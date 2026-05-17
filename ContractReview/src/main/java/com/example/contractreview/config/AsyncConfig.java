package com.example.contractreview.config;

import lombok.extern.slf4j.Slf4j;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.AsyncConfigurer;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;
import org.springframework.web.servlet.config.annotation.AsyncSupportConfigurer;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

import java.util.concurrent.Executor;
import java.util.concurrent.ThreadPoolExecutor;

/**
 * 异步配置类
 * 配置异步请求超时时间和线程池
 */
@Slf4j
@Configuration
@EnableAsync
public class AsyncConfig implements AsyncConfigurer, WebMvcConfigurer {

    /**
     * 配置异步支持 - 增加超时时间
     */
    @Override
    public void configureAsyncSupport(AsyncSupportConfigurer configurer) {
        // 设置异步请求超时时间为 5 分钟
        configurer.setDefaultTimeout(300000);

        // 设置异步执行器
        configurer.setTaskExecutor(mvcTaskExecutor());

        log.info("异步支持配置完成，默认超时时间: 300000ms");
    }

    /**
     * 创建用于 MVC 异步处理的线程池执行器
     */
    @Bean(name = "mvcTaskExecutor")
    public ThreadPoolTaskExecutor mvcTaskExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(10);
        executor.setMaxPoolSize(50);
        executor.setQueueCapacity(100);
        executor.setThreadNamePrefix("MvcAsync-");
        executor.setKeepAliveSeconds(300);
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        executor.initialize();
        return executor;
    }

    /**
     * 配置 @Async 注解使用的默认执行器
     */
    @Override
    @Bean(name = "asyncExecutor")
    public Executor getAsyncExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(10);
        executor.setMaxPoolSize(50);
        executor.setQueueCapacity(100);
        executor.setThreadNamePrefix("Async-");
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        executor.initialize();
        return executor;
    }

    /**
     * 邮件发送专用线程池
     */
    @Bean(name = "emailTaskExecutor")
    public ThreadPoolTaskExecutor mailTaskExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(5);
        executor.setMaxPoolSize(20);
        executor.setQueueCapacity(50);
        executor.setThreadNamePrefix("Mail-");
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        executor.initialize();
        log.info("邮件线程池初始化完成");
        return executor;
    }

    /**
     * 通知发送专用线程池
     */
    @Bean(name = "notificationTaskExecutor")
    public ThreadPoolTaskExecutor notificationTaskExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(10);
        executor.setMaxPoolSize(30);
        executor.setQueueCapacity(100);
        executor.setThreadNamePrefix("Notification-");
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        executor.initialize();
        log.info("通知线程池初始化完成");
        return executor;
    }

    /**
     * 验证码邮件发送专用线程池
     */
    @Bean(name = "verifyCodeExecutor")
    public ThreadPoolTaskExecutor verifyCodeExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(5);
        executor.setMaxPoolSize(20);
        executor.setQueueCapacity(100);
        executor.setThreadNamePrefix("VerifyCode-");
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        executor.initialize();
        log.info("验证码邮件线程池初始化完成");
        return executor;
    }

    /**
     * SSE 心跳任务线程池
     */
    @Bean(name = "sseHeartbeatExecutor")
    public ThreadPoolTaskExecutor sseHeartbeatExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(2);
        executor.setMaxPoolSize(5);
        executor.setQueueCapacity(10);
        executor.setThreadNamePrefix("SSE-Heartbeat-");
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.DiscardPolicy());
        executor.initialize();
        log.info("SSE心跳线程池初始化完成");
        return executor;
    }
}
