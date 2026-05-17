package com.example.contractreview.model.vo;

import com.example.contractreview.enums.LawType;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 法律文档详情VO
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class LawVO {

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
     * 文件大小（字节）
     */
    private Long fileSize;

    /**
     * 生效日期
     */
    private LocalDate effectiveDate;

    /**
     * 文档说明
     */
    private String description;

    /**
     * 文件URL
     */
    private String fileUrl;

    /**
     * 上传时间
     */
    private LocalDateTime uploadTime;

    /**
     * 上传人
     */
    private String uploader;
}
