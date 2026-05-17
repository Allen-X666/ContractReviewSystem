package com.example.contractreview.model.entity;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SystemDocument {
    private Integer id;                    // 文档ID
    private String name;                // 文档名称
    private String category; // 文档分类 (MANUAL/GUIDE/FAQ/SYSTEM/OTHER)
    private List<String> tags;                // 标签(JSON数组字符串)
    private String description;         // 文档说明
    private String filePath;            // 文件存储路径
    private Long fileSize;              // 文件大小
    private Integer status;     // 状态 (ACTIVE/DELETED)
    private LocalDateTime createAt;     // 创建时间
}