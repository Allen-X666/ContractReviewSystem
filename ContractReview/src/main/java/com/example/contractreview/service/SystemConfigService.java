package com.example.contractreview.service;

import com.example.contractreview.common.Result;

import java.util.Map;

public interface SystemConfigService {

    // 获取存储路径配置
    Result<Map<String, String>> getStorageConfig(String authorization);

    // 保存存储路径配置
    Result<Void> saveStorageConfig(String authorization, Map<String, String> config);

    // 验证路径
    Result<Boolean> validatePath(String authorization,String path);
}
