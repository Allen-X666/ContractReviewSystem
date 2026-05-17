package com.example.contractreview.model.vo.fastapi;

import lombok.Data;

@Data
public class FastApiResult<T> {

    private Integer code;
    private String message;
    private T data;

    public boolean isSuccess() {
        return code != null && code == 200;
    }
}
