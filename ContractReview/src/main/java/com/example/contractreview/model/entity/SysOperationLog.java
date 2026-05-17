package com.example.contractreview.model.entity;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 操作日志实体类
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SysOperationLog {

    /**
     * 日志ID
     */
    private Long id;

    /**
     * 用户ID
     */
    private Long userId;

    /**
     * 操作类型
     */
    private String operation;

    /**
     * 操作模块
     */
    private String module;

    /**
     * 操作描述
     */
    private String description;

    /**
     * 请求方法
     */
    private String requestMethod;

    /**
     * 请求URL
     */
    private String requestUrl;

    /**
     * 请求参数
     */
    private String requestParams;

    /**
     * 响应数据
     */
    private String responseData;

    /**
     * IP地址
     */
    private String ipAddress;

    /**
     * 浏览器UA
     */
    private String userAgent;

    /**
     * 执行时长(ms)
     */
    private Integer executionTime;

    /**
     * 状态
     */
    private Integer status;

    /**
     * 错误信息
     */
    private String errorMsg;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;
}
