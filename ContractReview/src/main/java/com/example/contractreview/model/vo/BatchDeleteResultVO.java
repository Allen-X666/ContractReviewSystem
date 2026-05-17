package com.example.contractreview.model.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 批量删除结果VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class BatchDeleteResultVO {

    /**
     * 删除数量
     */
    private Integer deleted;
}
