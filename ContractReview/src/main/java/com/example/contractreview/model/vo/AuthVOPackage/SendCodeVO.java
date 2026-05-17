package com.example.contractreview.model.vo.AuthVOPackage;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class SendCodeVO {
    private Integer expireSeconds;
}
