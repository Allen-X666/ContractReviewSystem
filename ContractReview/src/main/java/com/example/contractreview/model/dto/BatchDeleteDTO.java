package com.example.contractreview.model.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * 批量删除DTO
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class BatchDeleteDTO {

    /**
     * ID列表
     */
    private List<Long> ids;
}
