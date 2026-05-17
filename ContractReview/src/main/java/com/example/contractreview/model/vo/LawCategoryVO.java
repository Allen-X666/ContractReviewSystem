package com.example.contractreview.model.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 法规分类VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class LawCategoryVO {

    /**
     * 分类ID
     */
    private String id;

    /**
     * 分类名称
     */
    private String name;
}
