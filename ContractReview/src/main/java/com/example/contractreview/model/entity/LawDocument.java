package com.example.contractreview.model.entity;

import com.example.contractreview.enums.LawType;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 法律文档实体类
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class LawDocument {

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
     * 文件路径
     */
    private String filePath;

    /**
     * 文件大小(字节)
     */
    private Long fileSize;

    /**
     * 文件类型(pdf/doc/docx)
     */
    private String fileType;

    /**
     * 生效日期
     */
    private LocalDate effectiveDate;

    /**
     * 文档说明
     */
    private String description;

    /**
     * 上传用户ID
     */
    private Integer uploadUserId;

    /**
     * 创建时间
     */
    private LocalDateTime createAt;
}
