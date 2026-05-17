package com.example.contractreview.model.entity;

import com.example.contractreview.enums.ContractCategory;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 合同模板实体类
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ContractTemplate {

    /**
     * 模板ID
     */
    private Long id;

    /**
     * 模板名称
     */
    private String name;

    /**
     * 分类
     */
    private ContractCategory category;

    /**
     * 模板描述
     */
    private String description;

    /**
     * 文件路径
     */
    private String filePath;

    /**
     * 文件大小
     */
    private Long fileSize;

    /**
     * 模板内容
     */
    private String content;

    /**
     * 下载次数
     */
    private Integer downloadCount;

    /**
     * 是否启用
     */
    private Boolean isActive;

    /**
     * 创建人ID
     */
    private Long createdBy;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;

    /**
     * 更新时间
     */
    private LocalDateTime updatedAt;
}
