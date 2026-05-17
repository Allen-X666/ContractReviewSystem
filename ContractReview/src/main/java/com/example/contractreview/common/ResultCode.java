package com.example.contractreview.common;

/**
 * 统一响应状态码枚举
 * 状态码设计原则：
 * - 1xxx: 通用业务错误
 * - 2xxx: 用户/认证相关错误
 * - 3xxx: 业务逻辑错误（合同、审查等）
 * - 4xxx: Token/权限相关错误
 */
public enum ResultCode {

    SUCCESS(200, "success"),

    BAD_REQUEST(400, "请求参数错误"),

    UNAUTHORIZED(401, "未授权或Token无效"),

    FORBIDDEN(403, "禁止访问"),

    NOT_FOUND(404, "资源不存在"),

    ERROR(500, "服务器内部错误"),

    BUSINESS_ERROR(1001, "业务处理失败"),

    VALIDATION_ERROR(1002, "参数校验失败"),

    TOO_MANY_REQUESTS(1003, "请求过于频繁，请稍后再试"),

    FILE_UPLOAD_ERROR(1004, "文件上传失败"),

    FILE_TYPE_NOT_SUPPORTED(1005, "不支持的文件格式"),

    FILE_TOO_LARGE(1006, "文件大小超过限制"),

    USER_ALREADY_EXISTS(2001, "用户已存在"),

    USERNAME_OR_PASSWORD_ERROR(2002, "用户名或密码错误"),

    CAPTCHA_ERROR(2003, "验证码错误或已过期"),

    ACCOUNT_DISABLED(2004, "账号已被禁用"),

    USER_PASSWORD_ERROR(2005, "密码输入错误"),

    USER_PASSWORD_NOT_MATCH(2006, "两次输入的密码不一致"),

    USER_ALREADY_LOGIN(2007, "该账号已在其他设备登录，请确认是否为本人操作"),

    EMAIL_ALREADY_EXISTS(2008, "邮箱已被使用"),

    PHONE_ALREADY_EXISTS(2009, "手机号已被使用"),

    USER_PASSWORD_NOT_CHANGE(2010, "新密码不能和旧密码一致"),

    USER_NOT_FOUND(2020, "用户不存在，请注册后重试"),

    CAPTCHA_EXPIRED(2021, "验证码已过期"),

    REVIEW_FAILED(3001, "合同审查失败"),

    CONTRACT_PARSE_ERROR(3002, "合同解析失败"),

    AI_SERVICE_ERROR(3003, "AI服务异常"),

    CONTRACT_NOT_FOUND(3004, "合同不存在"),

    PARAM_ERROR(3005, "参数错误"),

    KNOWLEDGE_NOT_FOUND(3006, "知识库不存在"),

    KNOWLEDGE_BASE_ERROR(3007, "知识库异常"),

    LAW_NOT_FOUND(3008, "法律法规不存在"),

    TOKEN_EXPIRED(4001, "Token已过期，请重新登录"),

    TOKEN_INVALID(4002, "Token无效，请重新登录"),

    TOKEN_EXPIRED_OR_INVALID(4003, "Token已失效，请重新登录"),

    NO_TOKEN(4004, "没有Token，请重新登录"),

    REFRESH_TOKEN_FAILED(4005, "刷新Token失败，请重新登录");

    private final Integer code;
    private final String message;

    ResultCode(Integer code, String message) {
        this.code = code;
        this.message = message;
    }

    public Integer getCode() {
        return code;
    }

    public String getMessage() {
        return message;
    }

    public static ResultCode getByCode(Integer code) {
        if (code == null) return null;
        for (ResultCode resultCode : values()) {
            if (resultCode.getCode().equals(code)) {
                return resultCode;
            }
        }
        return null;
    }
}