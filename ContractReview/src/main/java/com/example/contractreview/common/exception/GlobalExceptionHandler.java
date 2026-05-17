package com.example.contractreview.common.exception;

import com.example.contractreview.common.Result;
import com.example.contractreview.common.ResultCode;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.ConstraintViolation;
import jakarta.validation.ConstraintViolationException;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.validation.BindException;
import org.springframework.validation.FieldError;
import org.springframework.web.HttpMediaTypeNotSupportedException;
import org.springframework.web.HttpRequestMethodNotSupportedException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.MissingServletRequestParameterException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.MethodArgumentTypeMismatchException;
import org.springframework.web.multipart.MaxUploadSizeExceededException;
import org.springframework.web.servlet.NoHandlerFoundException;

import java.util.HashMap;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;

/**
 * 全局异常处理器
 * 统一处理所有异常，返回标准化的 JSON 响应
 */
@Slf4j
@RestControllerAdvice
public class GlobalExceptionHandler {

    /**
     * 处理业务异常
     */
    @ExceptionHandler(BusinessException.class)
    public Result<Void> handleBusinessException(BusinessException e, HttpServletRequest request) {
        log.warn("业务异常 - URI: {}, 错误码: {}, 错误信息: {}",
                request.getRequestURI(), e.getCode(), e.getMessage());
        return Result.error(e.getCode(), e.getMessage());
    }

    /**
     * 处理参数校验异常（@Valid @RequestBody）
     */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public Result<Map<String, String>> handleMethodArgumentNotValidException(
            MethodArgumentNotValidException e, HttpServletRequest request) {
        log.warn("参数校验失败 - URI: {}", request.getRequestURI());
        Map<String, String> errors = new HashMap<>();
        e.getBindingResult().getFieldErrors().forEach(fieldError ->
            errors.put(fieldError.getField(), fieldError.getDefaultMessage())
        );
        return Result.error(ResultCode.VALIDATION_ERROR.getCode(), "请求参数校验失败", errors);
    }

    /**
     * 处理参数绑定异常（@ModelAttribute）
     */
    @ExceptionHandler(BindException.class)
    public Result<Map<String, String>> handleBindException(BindException e, HttpServletRequest request) {
        log.warn("参数绑定失败 - URI: {}", request.getRequestURI());
        Map<String, String> errors = new HashMap<>();
        for (FieldError fieldError : e.getFieldErrors()) {
            errors.put(fieldError.getField(), fieldError.getDefaultMessage());
        }
        return Result.error(ResultCode.VALIDATION_ERROR.getCode(), "请求参数绑定失败", errors);
    }

    /**
     * 处理单个参数校验失败（@RequestParam @PathVariable）
     */
    @ExceptionHandler(ConstraintViolationException.class)
    public Result<Void> handleConstraintViolationException(
            ConstraintViolationException e, HttpServletRequest request) {
        log.warn("参数校验失败 - URI: {}", request.getRequestURI());
        String message = e.getConstraintViolations().stream()
                .map(ConstraintViolation::getMessage)
                .collect(Collectors.joining(", "));
        return Result.error(ResultCode.VALIDATION_ERROR.getCode(), message);
    }

    /**
     * 处理缺少请求参数异常
     */
    @ExceptionHandler(MissingServletRequestParameterException.class)
    public Result<Void> handleMissingServletRequestParameterException(
            MissingServletRequestParameterException e, HttpServletRequest request) {
        log.warn("缺少请求参数 - URI: {}, 参数名: {}", request.getRequestURI(), e.getParameterName());
        return Result.error(ResultCode.BAD_REQUEST.getCode(), "缺少必要参数: " + e.getParameterName());
    }

    /**
     * 处理方法参数类型不匹配异常
     */
    @ExceptionHandler(MethodArgumentTypeMismatchException.class)
    public Result<Void> handleMethodArgumentTypeMismatchException(
            MethodArgumentTypeMismatchException e, HttpServletRequest request) {
        log.warn("参数类型不匹配 - URI: {}, 参数名: {}, 期望值: {}",
                request.getRequestURI(), e.getName(), e.getRequiredType());
        String expectedType = e.getRequiredType() != null ? e.getRequiredType().getSimpleName() : "未知";
        return Result.error(ResultCode.BAD_REQUEST.getCode(),
                String.format("参数 '%s' 类型错误，期望类型: %s", e.getName(), expectedType));
    }

    /**
     * 处理请求体解析异常
     */
    @ExceptionHandler(HttpMessageNotReadableException.class)
    public Result<Void> handleHttpMessageNotReadableException(
            HttpMessageNotReadableException e, HttpServletRequest request) {
        log.warn("请求体解析失败 - URI: {}", request.getRequestURI());
        return Result.error(ResultCode.BAD_REQUEST.getCode(), "请求体格式错误，请检查JSON格式");
    }

    /**
     * 处理文件上传大小超出限制异常
     */
    @ExceptionHandler(MaxUploadSizeExceededException.class)
    public Result<Void> handleMaxUploadSizeExceededException(
            MaxUploadSizeExceededException e, HttpServletRequest request) {
        log.warn("文件上传过大 - URI: {}", request.getRequestURI());
        return Result.error(ResultCode.FILE_TOO_LARGE);
    }

    /**
     * 处理不支持的请求方法
     */
    @ExceptionHandler(HttpRequestMethodNotSupportedException.class)
    public Result<Void> handleHttpRequestMethodNotSupportedException(
            HttpRequestMethodNotSupportedException e, HttpServletRequest request) {
        log.warn("不支持的请求方法 - URI: {}, 方法: {}", request.getRequestURI(), e.getMethod());
        return Result.error(ResultCode.BAD_REQUEST.getCode(),
                String.format("不支持的请求方法: %s", e.getMethod()));
    }

    /**
     * 处理不支持的媒体类型
     */
    @ExceptionHandler(HttpMediaTypeNotSupportedException.class)
    public Result<Void> handleHttpMediaTypeNotSupportedException(
            HttpMediaTypeNotSupportedException e, HttpServletRequest request) {
        log.warn("不支持的媒体类型 - URI: {}", request.getRequestURI());
        return Result.error(ResultCode.FILE_TYPE_NOT_SUPPORTED);
    }

    /**
     * 处理404异常
     */
    @ExceptionHandler(NoHandlerFoundException.class)
    public Result<Void> handleNoHandlerFoundException(
            NoHandlerFoundException e, HttpServletRequest request) {
        log.warn("资源未找到 - URI: {}", request.getRequestURI());
        return Result.error(ResultCode.NOT_FOUND);
    }

    /**
     * 处理IllegalArgumentException
     */
    @ExceptionHandler(IllegalArgumentException.class)
    public Result<Void> handleIllegalArgumentException(
            IllegalArgumentException e, HttpServletRequest request) {
        log.warn("非法参数 - URI: {}, 错误信息: {}", request.getRequestURI(), e.getMessage());
        return Result.error(ResultCode.BAD_REQUEST.getCode(), e.getMessage());
    }

    /**
     * 处理所有未捕获的异常
     */
    @ExceptionHandler(Exception.class)
    public Result<Void> handleException(Exception e, HttpServletRequest request) {
        log.error("系统异常 - URI: {}, 异常类型: {}, 错误信息: {}",
                request.getRequestURI(), e.getClass().getSimpleName(), e.getMessage(), e);

        // 检查是否是 SSE 请求
        String acceptHeader = request.getHeader("Accept");
        if (acceptHeader != null && acceptHeader.contains("text/event-stream")) {
            return null;
        }

        // 根据异常类型返回更精确的错误信息
        if (e.getCause() != null) {
            String causeName = e.getCause().getClass().getSimpleName();
            if (causeName.contains("SQL") || causeName.contains("Data")) {
                return Result.error(ResultCode.ERROR.getCode(), "数据库操作失败，请稍后重试");
            }
        }

        return Result.error(ResultCode.ERROR.getCode(), "系统繁忙，请稍后重试");
    }
}