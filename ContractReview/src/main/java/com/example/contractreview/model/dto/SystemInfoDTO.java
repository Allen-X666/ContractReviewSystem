package com.example.contractreview.model.dto;

import lombok.Builder;
import lombok.Data;

@Data
@Builder
public class SystemInfoDTO {
    // 系统版本
    private String version;
    // 前端版本
    private String frontendVersion;
    // 后端版本
    private String backendVersion;
    // 最近更新时间
    private String lastUpdate;
    // 知识库版本
    private String knowledgeVersion;
    // AI模型
    private String aiModel;
}
