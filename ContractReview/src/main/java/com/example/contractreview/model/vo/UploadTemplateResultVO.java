package com.example.contractreview.model.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 上传模板结果VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UploadTemplateResultVO {

    /**
     * 模板ID
     */
    private Long templateId;

    /**
     * 模板名称
     */
    private String name;

    /**
     * 分类
     */
    private String category;
}
