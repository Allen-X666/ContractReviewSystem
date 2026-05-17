package com.example.contractreview.model.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 合同预览VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ContractPreviewVO {

    // 合同ID
    private Integer contractId;

    // 文件名
    private String fileName;

    // 文件类型
    private String fileType;

    // 文件URL
    private String fileUrl;

    // 文件大小
    private Long fileSize;

    // 创建时间
    private LocalDateTime created_at;
}
