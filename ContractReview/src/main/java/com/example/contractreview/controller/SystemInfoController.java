package com.example.contractreview.controller;

import com.example.contractreview.common.Result;
import com.example.contractreview.model.dto.SystemInfoDTO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

/**
 * 系统信息控制器
 */
@Tag(name = "系统信息")
@RestController
@RequestMapping("/system/info")
public class SystemInfoController {

    @Value("${app.version}")
    private String version;

    @Value("${app.frontend-version}")
    private String frontendVersion;

    @Value("${app.backend-version}")
    private String backendVersion;

    @Value("${app.last-update}")
    private String lastUpdate;

    @Value("${app.knowledge-version}")
    private String knowledgeVersion;

    @Value("${app.ai-model}")
    private String aiModel;

    /**
     * 获取系统信息
     */
    @Operation(summary = "获取系统信息")
    @GetMapping
    public Result<SystemInfoDTO> getSystemInfo() {
        SystemInfoDTO systemInfo = SystemInfoDTO.builder()
                .version(version)
                .frontendVersion(frontendVersion)
                .backendVersion(backendVersion)
                .lastUpdate(lastUpdate)
                .knowledgeVersion(knowledgeVersion)
                .aiModel(aiModel)
                .build();
        return Result.success(systemInfo);
    }
}
