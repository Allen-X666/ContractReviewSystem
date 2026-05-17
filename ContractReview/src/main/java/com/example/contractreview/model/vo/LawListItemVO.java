package com.example.contractreview.model.vo;

import com.example.contractreview.enums.LawType;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 法律文档列表项VO
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class LawListItemVO {

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
     * 上传时间
     */
    private LocalDateTime uploadTime;
}
