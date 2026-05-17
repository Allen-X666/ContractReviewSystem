package com.example.contractreview.model.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.web.multipart.MultipartFile;

/**
 * 发起审查DTO
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class StartReviewDTO {

    /**
     * 合同ID
     */
    private Integer contractId;

    /**
     * 文件流
     */
    private MultipartFile file;

    /**
     * 审查选项
     */
    private ReviewOptionsDTO reviewOptions;

    /**
     * 审查选项DTO
     */
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ReviewOptionsDTO {

        /**
         * 检查无效条款
         */
        private Boolean checkInvalidClause;

        /**
         * 检查缺失条款
         */
        private Boolean checkMissingClause;

        /**
         * 检查不合理条款
         */
        private Boolean checkUnreasonableClause;

        /**
         * 检查法律风险
         */
        private Boolean checkLegalRisk;
    }
}
