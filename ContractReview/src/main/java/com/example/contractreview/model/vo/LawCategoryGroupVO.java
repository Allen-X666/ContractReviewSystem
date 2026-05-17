package com.example.contractreview.model.vo;

import com.example.contractreview.enums.LawCategory;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * 法规按分类分组VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class LawCategoryGroupVO {

    /**
     * 分类ID
     */
    private String categoryId;

    /**
     * 分类名称
     */
    private String categoryName;

    /**
     * 该分类下的法规列表
     */
    private List<LawRegulationVO> laws;
}
