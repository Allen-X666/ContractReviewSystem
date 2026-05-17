package com.example.contractreview.utils;

import lombok.extern.slf4j.Slf4j;

import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;

/**
 * MD5加密工具类
 */
@Slf4j
public class MD5Utils {

    /**
     * MD5加密
     *
     * @param input 输入字符串
     * @return MD5加密后的字符串（32位小写）
     */
    public static String md5(String input) {
        if (input == null || input.isEmpty()) {
            return null;
        }
        try {
            MessageDigest md = MessageDigest.getInstance("MD5");
            byte[] digest = md.digest(input.getBytes());
            StringBuilder sb = new StringBuilder();
            for (byte b : digest) {
                sb.append(String.format("%02x", b));
            }
            return sb.toString();
        } catch (NoSuchAlgorithmException e) {
            log.error("MD5加密失败", e);
            return null;
        }
    }

    /**
     * MD5加密（加盐）
     *
     * @param input 输入字符串
     * @param salt  盐值
     * @return MD5加密后的字符串
     */
    public static String md5WithSalt(String input, String salt) {
        if (input == null || input.isEmpty()) {
            return null;
        }
        return md5(input + salt);
    }
}
