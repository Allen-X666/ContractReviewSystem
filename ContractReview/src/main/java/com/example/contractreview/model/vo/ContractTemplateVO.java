package com.example.contractreview.model.vo;

import com.example.contractreview.enums.ContractCategory;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 合同模板VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ContractTemplateVO {

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
     * 文件大小
     */
    private Long fileSize;

    /**
     * 下载次数
     */
    private Integer downloadCount;

    /**
     * 更新时间
     */
    private LocalDateTime updatedAt;
}
