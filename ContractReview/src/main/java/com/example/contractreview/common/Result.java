package com.example.contractreview.common;

import java.time.LocalDateTime;
import java.time.ZoneId;

/**
 * 统一响应结果封装类
 *
 * @param <T> 响应数据类型
 */
public class Result<T> {

    /**
     * 状态码
     */
    private Integer code;

    /**
     * 提示信息
     */
    private String message;

    /**
     * 响应数据
     */
    private T data;

    /**
     * 数据总数（分页使用）
     */
    private Long total;

    /**
     * 时间戳
     */
    private Long timestamp;

    public Result() {
        this.timestamp = System.currentTimeMillis();
    }

    public Result(Integer code, String message, T data) {
        this.code = code;
        this.message = message;
        this.data = data;
        this.timestamp = System.currentTimeMillis();
    }

    /**
     * 成功响应（无数据）
     */
    public static <T> Result<T> success() {
        return new Result<>(ResultCode.SUCCESS.getCode(), ResultCode.SUCCESS.getMessage(), null);
    }

    /**
     * 成功响应（带数据）
     */
    public static <T> Result<T> success(T data) {
        return new Result<>(ResultCode.SUCCESS.getCode(), ResultCode.SUCCESS.getMessage(), data);
    }

    /**
     * 成功响应（分页数据）
     */
    public static <T> Result<T> success(T data, Long total) {
        Result<T> result = new Result<>(ResultCode.SUCCESS.getCode(), ResultCode.SUCCESS.getMessage(), data);
        result.setTotal(total);
        return result;
    }

    /**
     * 成功响应（自定义消息）
     */
    public static <T> Result<T> success(String message, T data) {
        return new Result<>(ResultCode.SUCCESS.getCode(), message, data);
    }

    /**
     * 失败响应
     */
    public static <T> Result<T> error() {
        return new Result<>(ResultCode.ERROR.getCode(), ResultCode.ERROR.getMessage(), null);
    }

    /**
     * 失败响应（自定义消息）
     */
    public static <T> Result<T> error(String message) {
        return new Result<>(ResultCode.ERROR.getCode(), message, null);
    }

    /**
     * 失败响应（自定义状态码和消息）
     */
    public static <T> Result<T> error(Integer code, String message) {
        return new Result<>(code, message, null);
    }

    /**
     * 失败响应（使用ResultCode）
     */
    public static <T> Result<T> error(ResultCode resultCode) {
        return new Result<>(resultCode.getCode(), resultCode.getMessage(), null);
    }

    /**
     * 失败响应（使用ResultCode，带数据）
     */
    public static <T> Result<T> error(ResultCode resultCode, T data) {
        return new Result<>(resultCode.getCode(), resultCode.getMessage(), data);
    }

    /**
     * 失败响应（自定义状态码、消息和数据）
     */
    public static <T> Result<T> error(Integer code, String message, T data) {
        return new Result<>(code, message, data);
    }

    /**
     * 参数错误响应
     */
    public static <T> Result<T> badRequest(String message) {
        return new Result<>(ResultCode.BAD_REQUEST.getCode(), message, null);
    }

    /**
     * 未授权响应
     */
    public static <T> Result<T> unauthorized(String message) {
        return new Result<>(ResultCode.UNAUTHORIZED.getCode(), message, null);
    }

    /**
     * 禁止访问响应
     */
    public static <T> Result<T> forbidden(String message) {
        return new Result<>(ResultCode.FORBIDDEN.getCode(), message, null);
    }

    /**
     * 资源不存在响应
     */
    public static <T> Result<T> notFound(String message) {
        return new Result<>(ResultCode.NOT_FOUND.getCode(), message, null);
    }

    /**
     * 判断是否为成功响应
     */
    public boolean isSuccess() {
        return ResultCode.SUCCESS.getCode().equals(this.code);
    }

    public Integer getCode() {
        return code;
    }

    public void setCode(Integer code) {
        this.code = code;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public T getData() {
        return data;
    }

    public void setData(T data) {
        this.data = data;
    }

    public Long getTotal() {
        return total;
    }

    public void setTotal(Long total) {
        this.total = total;
    }

    public Long getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(Long timestamp) {
        this.timestamp = timestamp;
    }

    @Override
    public String toString() {
        return "Result{" +
                "code=" + code +
                ", message='" + message + '\'' +
                ", data=" + data +
                ", timestamp=" + timestamp +
                '}';
    }
}
