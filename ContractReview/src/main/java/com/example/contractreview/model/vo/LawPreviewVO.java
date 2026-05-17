package com.example.contractreview.model.vo;

import com.example.contractreview.enums.LawType;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 法律文档预览VO
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class LawPreviewVO {

    /**
     * 文档ID
     */
    private Long id;

    /**
     * 文档名称
     */
    private String name;

    /**
     * 文档类型
     */
    private LawType type;

    /**
     * 文档内容（文本内容或HTML）
     */
    private String content;

    /**
     * 预览URL（PDF或图片预览链接）
     */
    private String previewUrl;
}
