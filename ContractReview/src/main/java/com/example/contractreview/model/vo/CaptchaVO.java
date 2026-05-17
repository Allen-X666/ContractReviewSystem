package com.example.contractreview.model.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 图形验证码VO
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Schema(description = "图形验证码响应")
public class CaptchaVO {

    @Schema(description = "验证码唯一标识")
    private String captchaId;

    @Schema(description = "验证码图片Base64字符串")
    private String imageBase64;
}
