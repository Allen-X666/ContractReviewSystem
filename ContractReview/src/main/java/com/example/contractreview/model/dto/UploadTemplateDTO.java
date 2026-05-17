package com.example.contractreview.model.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 上传模板DTO
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class UploadTemplateDTO {

    /**
     * 模板名称
     */
    private String name;

    /**
     * 模板分类
     */
    private String category;

    /**
     * 模板描述
     */
    private String description;
}
