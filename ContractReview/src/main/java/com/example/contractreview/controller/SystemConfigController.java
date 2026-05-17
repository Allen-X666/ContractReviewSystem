package com.example.contractreview.controller;

import com.example.contractreview.common.Result;
import com.example.contractreview.service.SystemConfigService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@Tag(name = "系统配置管理")
@RestController
@RequestMapping("/system/config")
@RequiredArgsConstructor
public class SystemConfigController {

    private final SystemConfigService systemConfigService;

    @Operation(summary = "获取存储路径配置")
    @GetMapping("/storage")
    public Result<Map<String, String>> getStorageConfig(@RequestHeader("Authorization") String authorization) {
        return systemConfigService.getStorageConfig(authorization);
    }

    @Operation(summary = "保存存储路径配置")
    @PostMapping("/storage")
    public Result<Void> saveStorageConfig(@RequestHeader("Authorization") String authorization,
                                          @RequestBody Map<String, String> config) {
        return systemConfigService.saveStorageConfig(authorization, config);
    }

    @Operation(summary = "验证路径是否有效")
    @PostMapping("/validate-path")
    public Result<Boolean> validatePath(@RequestHeader("Authorization") String authorization,
                                        @RequestBody Map<String, String> params) {
        String path = params.get("path");
        return systemConfigService.validatePath(authorization, path);
    }
}
