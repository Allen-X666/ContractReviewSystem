package com.example.contractreview.model.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * 批量上传结果VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class BatchUploadResultVO {

    /**
     * 成功数量
     */
    private Integer success;

    /**
     * 失败数量
     */
    private Integer failed;

    /**
     * 合同列表
     */
    private List<ContractUploadStatusVO> contracts;

    /**
     * 合同上传状态VO
     */
    @Data
    @Builder
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ContractUploadStatusVO {

        /**
         * 合同ID
         */
        private Long contractId;

        /**
         * 文件名
         */
        private String fileName;

        /**
         * 状态
         */
        private String status;
    }
}
