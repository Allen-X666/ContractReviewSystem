package com.example.contractreview.model.vo;

import com.example.contractreview.enums.RiskLevel;
import com.example.contractreview.enums.ReviewStatus;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 合同详情VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ContractDetailVO {

    /**
     * 合同ID
     */
    private Long id;

    /**
     * 合同编号
     */
    private String contractNo;

    /**
     * 文件名
     */
    private String fileName;

    /**
     * 文件存储路径
     */
    private String filePath;

    /**
     * 文件大小
     */
    private Long fileSize;

    /**
     * 文件类型
     */
    private String fileType;

    /**
     * 合同文本内容
     */
    private String content;

    /**
     * 审查状态
     */
    private ReviewStatus reviewStatus;

    /**
     * 风险等级
     */
    private RiskLevel riskLevel;

    /**
     * 审查得分
     */
    private Integer reviewScore;

    /**
     * 创建时间
     */
    private LocalDateTime createdAt;

    /**
     * 更新时间
     */
    private LocalDateTime updatedAt;
}
