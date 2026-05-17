package com.example.contractreview.utils;

import org.springframework.stereotype.Component;

import java.util.Random;

@Component
public class RandomCaptcha {

    // 生成随机验证码
    public String generateRandomCode(int length) {
        String chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
        Random random = new Random();
        StringBuilder code = new StringBuilder();
        for (int i = 0; i < length; i++) {
            code.append(chars.charAt(random.nextInt(chars.length())));
        }
        return code.toString();
    }
}
