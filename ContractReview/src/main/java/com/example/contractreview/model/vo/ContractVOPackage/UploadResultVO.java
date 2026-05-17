package com.example.contractreview.model.vo.ContractVOPackage;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 上传结果VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class UploadResultVO {

    /**
     * 合同ID
     */
    private Integer contractId;

    /**
     * 文件名
     */
    private String fileName;

    /**
     * 文件大小
     */
    private Long fileSize;

    /**
     * 文件类型
     */
    private String fileType;

    /**
     * 上传时间
     */
    private LocalDateTime uploadTime;
}
