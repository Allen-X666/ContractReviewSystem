package com.example.contractreview.service.serviceImpl;

import com.example.contractreview.common.Result;
import com.example.contractreview.constant.StorageConstant;
import com.example.contractreview.mapper.SystemConfigMapper;
import com.example.contractreview.service.SystemConfigService;
import com.example.contractreview.utils.TokenUtils;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.io.File;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
@Slf4j
@RequiredArgsConstructor
public class SystemConfigServiceImpl implements SystemConfigService {

    private final SystemConfigMapper systemConfigMapper;
    private final StringRedisTemplate stringRedisTemplate;
    private final ObjectMapper objectMapper;
    private final TokenUtils tokenUtils;

    // 默认存储路径
    private static final String DEFAULT_UPLOAD_PATH = "e:\\Professional\\合同审查agent\\ContractReview\\upload";
    private static final String DEFAULT_REVIEW_PATH = "e:\\Professional\\合同审查agent\\ContractReview\\review";

    // 获取存储路径配置
    @Override
    public Result<Map<String, String>> getStorageConfig(String authorization) {
        Integer userId = tokenUtils.getUserId(authorization);
        String uploadPath = StorageConstant.UPLOAD_PATH_KEY + userId;
        String reviewPath = StorageConstant.DOWNLOAD_PATH_KEY + userId;
        String cachUploadPath = stringRedisTemplate.opsForValue().get(uploadPath);
        String cachReviewPath = stringRedisTemplate.opsForValue().get(reviewPath);
        Map<String,String> map = new HashMap<>();
        if (cachReviewPath != null && cachUploadPath != null) {
            map.put("uploadPath", cachUploadPath);
            map.put("reviewPath", cachReviewPath);
        } else {
            String uploadPathFromDB = systemConfigMapper.selectUploadPathByUserId(userId);
            String reviewPathFromDB = systemConfigMapper.selectReviewPathByUserId(userId);
            if (uploadPathFromDB == null || uploadPathFromDB.trim().isEmpty()) {
                uploadPathFromDB = DEFAULT_UPLOAD_PATH;
            }
            if (reviewPathFromDB == null || reviewPathFromDB.trim().isEmpty()) {
                reviewPathFromDB = DEFAULT_REVIEW_PATH;
            }
            map.put("uploadPath", uploadPathFromDB);
            map.put("reviewPath", reviewPathFromDB);
            systemConfigMapper.updatePath(userId, uploadPathFromDB, reviewPathFromDB);
            stringRedisTemplate.opsForValue().set(uploadPath, uploadPathFromDB);
            stringRedisTemplate.opsForValue().set(reviewPath, reviewPathFromDB);
        }
        return Result.success(map);
    }

    // 保存存储路径配置
    @Override
    public Result<Void> saveStorageConfig(String authorization, Map<String, String> config) {
        Integer userId = tokenUtils.getUserId(authorization);
        String uploadPath = StorageConstant.UPLOAD_PATH_KEY + userId;
        String reviewPath = StorageConstant.DOWNLOAD_PATH_KEY + userId;
        String newUploadPath = config.get("uploadPath");
        String newReviewPath = config.get("reviewPath");
        if (newUploadPath == null || newUploadPath.trim().isEmpty()) {
            return Result.error("上传文件路径不能为空");
        }
        if (newReviewPath == null || newReviewPath.trim().isEmpty()) {
            return Result.error("审查文件路径不能为空");
        }
        uploadPath = uploadPath.trim();
        reviewPath = reviewPath.trim();
        if (!isValidPath(uploadPath)) {
            return Result.error("上传文件路径格式不正确");
        }
        if (!isValidPath(reviewPath)) {
            return Result.error("审查文件路径格式不正确");
        }
        systemConfigMapper.updatePath(userId, newUploadPath, newReviewPath);
        stringRedisTemplate.delete(List.of(uploadPath, reviewPath));
        log.info("存储路径配置已更新 - uploadPath: {}, reviewPath: {}", uploadPath, reviewPath);
        return Result.success();
    }

    // 验证路径
    @Override
    public Result<Boolean> validatePath(String authorization, String path) {
        if (path == null || path.trim().isEmpty()) {
            return Result.error("路径不能为空");
        }

        path = path.trim();

        if (!isValidPath(path)) {
            return Result.success(false);
        }

        File directory = new File(path);

        if (!directory.exists()) {
            boolean created = directory.mkdirs();
            if (!created) {
                log.warn("路径不存在且创建失败: {}", path);
                return Result.success(false);
            }
            log.info("路径不存在，已自动创建: {}", path);
        }

        if (!directory.isDirectory()) {
            return Result.error("路径不是有效的目录");
        }

        if (!directory.canWrite()) {
            return Result.error("路径没有写入权限");
        }

        log.info("路径验证成功: {}", path);
        return Result.success(true);
    }

    private boolean isValidPath(String path) {
        if (path == null || path.trim().isEmpty()) {
            return false;
        }

        String trimmedPath = path.trim();

        if (trimmedPath.contains("<") || trimmedPath.contains(">") || 
            trimmedPath.contains("|") || trimmedPath.contains("\"") || 
            trimmedPath.contains("?") || trimmedPath.contains("*")) {
            return false;
        }

        return true;
    }

    /**
     * 获取上传路径，优先从Redis获取，否则查询数据库，使用默认值
     * @param userId 用户ID
     */
    public String getUploadPath(Integer userId) {
        String cacheKey = StorageConstant.UPLOAD_PATH_KEY + userId;
        String uploadPath = stringRedisTemplate.opsForValue().get(cacheKey);
        
        if (uploadPath != null) {
            return uploadPath;
        }
        
        uploadPath = systemConfigMapper.selectUploadPathByUserId(userId);
        if (uploadPath == null || uploadPath.trim().isEmpty()) {
            uploadPath = DEFAULT_UPLOAD_PATH;
        }
        
        stringRedisTemplate.opsForValue().set(cacheKey, uploadPath);
        return uploadPath;
    }

    /**
     * 获取审查路径，优先从Redis获取，否则查询数据库，使用默认值
     * @param userId 用户ID
     */
    public String getReviewPath(Integer userId) {
        String cacheKey = StorageConstant.DOWNLOAD_PATH_KEY + userId;
        String reviewPath = stringRedisTemplate.opsForValue().get(cacheKey);
        
        if (reviewPath != null) {
            return reviewPath;
        }
        
        reviewPath = systemConfigMapper.selectReviewPathByUserId(userId);
        if (reviewPath == null || reviewPath.trim().isEmpty()) {
            reviewPath = DEFAULT_REVIEW_PATH;
        }
        
        stringRedisTemplate.opsForValue().set(cacheKey, reviewPath);
        return reviewPath;
    }
}
