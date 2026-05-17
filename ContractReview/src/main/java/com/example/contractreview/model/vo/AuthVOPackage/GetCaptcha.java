package com.example.contractreview.model.vo.AuthVOPackage;

import lombok.Data;

@Data
public class GetCaptcha {
    /**
     * {
     *   "code": 200,
     *   "message": "success",
     *   "data": {
     *     "captchaId": "...",
     *     "imageBase64": "..."
     *   }
     * }
     */
    private String captchaId;
    private String imageBase64;
}
