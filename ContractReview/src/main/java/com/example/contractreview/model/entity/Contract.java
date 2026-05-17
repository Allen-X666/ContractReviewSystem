package com.example.contractreview.model.entity;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 合同实体类
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Contract {

    /**
     * 合同ID
     */
    private Integer id;

    /**
     * 文件名
     */
    private String fileName;

    /**
     * 文件存储路径
     */
    private String filePath;

    /**
     * 文件大小(字节)
     */
    private Long fileSize;

    /**
     * 文件类型
     */
    private String fileType;

    /**
     * 上传用户ID
     */
    private Long userId;

    /**
     * 审查状态
     */
    private String reviewStatus;

    /**
     * 风险等级
     */
    private String riskLevel;

    /**
     * 审查得分(0-100)
     */
    private Integer reviewScore;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;
}
