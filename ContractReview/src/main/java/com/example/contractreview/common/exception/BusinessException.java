package com.example.contractreview.common.exception;

import com.example.contractreview.common.ResultCode;

/**
 * 业务异常类
 */
public class BusinessException extends RuntimeException {

    /**
     * 错误码
     */
    private Integer code;

    /**
     * 错误信息
     */
    private String message;

    public BusinessException(String message) {
        super(message);
        this.code = ResultCode.BUSINESS_ERROR.getCode();
        this.message = message;
    }

    public BusinessException(Integer code, String message) {
        super(message);
        this.code = code;
        this.message = message;
    }

    public BusinessException(ResultCode resultCode) {
        super(resultCode.getMessage());
        this.code = resultCode.getCode();
        this.message = resultCode.getMessage();
    }

    public BusinessException(ResultCode resultCode, String message) {
        super(message);
        this.code = resultCode.getCode();
        this.message = message;
    }

    public Integer getCode() {
        return code;
    }

    @Override
    public String getMessage() {
        return message;
    }
}
