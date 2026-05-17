package com.example.contractreview.service;

import com.example.contractreview.common.Result;
import com.example.contractreview.model.vo.KnowledgeStatsVO;
import com.example.contractreview.model.vo.LawCategoryGroupVO;
import com.example.contractreview.model.vo.LawCategoryVO;
import com.example.contractreview.model.vo.LawRegulationDetailVO;
import com.example.contractreview.model.vo.LawRegulationVO;

import java.util.List;

public interface KnowledgeService {

    /**
     * 获取知识库统计数据
     */
    Result<KnowledgeStatsVO> getKnowledgeStats();

    /**
     * 获取法条分类列表
     */
    Result<List<LawCategoryVO>> getLawCategories();

    /**
     * 搜索法条（按分类分组）
     */
    Result<List<LawCategoryGroupVO>> searchLawsGroupedByCategory(String keyword, Integer page, Integer pageSize);

    /**
     * 获取法条详情
     */
    Result<LawRegulationDetailVO> getLawDetail(Long lawId);
}
