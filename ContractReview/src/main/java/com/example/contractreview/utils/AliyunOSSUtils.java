package com.example.contractreview.utils;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;

/**
 * 阿里云OSS工具类
 * 封装头像、文件上传功能
 */
@Slf4j
@Component
@RequiredArgsConstructor
public class AliyunOSSUtils {

    private final PutObjectAsync putObjectAsync;

    /**
     * 异步上传头像文件
     *
     * @param file 头像文件
     * @param userId 用户ID
     * @return 头像访问URL
     * @throws IOException 文件读取异常
     */
    public String asyncUploadAvatar(MultipartFile file, Integer userId) throws IOException {
        log.info("开始上传用户头像, userId: {}, fileName: {}, fileSize: {}",
                userId, file.getOriginalFilename(), file.getSize());

        String avatarUrl = putObjectAsync.uploadAvatar(file, userId);

        log.info("用户头像上传成功, userId: {}, avatarUrl: {}", userId, avatarUrl);
        return avatarUrl;
    }

    /**
     * 异步上传文件（通用方法）
     *
     * @param file 文件
     * @param objectKey OSS对象键
     * @return 文件访问URL
     * @throws IOException 文件读取异常
     */
    public String asyncUploadFile(MultipartFile file, String objectKey) throws IOException {
        log.info("开始上传文件, fileName: {}, objectKey: {}", file.getOriginalFilename(), objectKey);

        String fileUrl = putObjectAsync.uploadFile(file, objectKey);

        log.info("文件上传成功, fileUrl: {}", fileUrl);
        return fileUrl;
    }

    /**
     * 删除OSS文件
     *
     * @param objectKey OSS对象键
     */
    public void deleteFile(String objectKey) {
        log.info("开始删除OSS文件, objectKey: {}", objectKey);
        putObjectAsync.deleteFile(objectKey);
        log.info("OSS文件删除成功, objectKey: {}", objectKey);
    }
}
