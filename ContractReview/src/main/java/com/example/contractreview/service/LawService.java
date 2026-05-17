package com.example.contractreview.service;

import com.example.contractreview.common.Result;
import com.example.contractreview.enums.LawCategory;
import com.example.contractreview.model.vo.LawRegulationDetailVO;
import com.example.contractreview.model.vo.LawRegulationVO;

import java.util.List;

/**
 * 法律法规服务接口
 */
public interface LawService {

    /**
     * 获取所有法规分类
     *
     * @return 分类列表
     */
    Result<List<String>> getAllCategories();

    /**
     * 搜索法规
     *
     * @param keyword  关键词
     * @param category 分类
     * @param page     页码
     * @param pageSize 每页大小
     * @return 法规列表
     */
    Result<List<LawRegulationVO>> searchLaws(String keyword, String category, Integer page, Integer pageSize);

    /**
     * 获取法规详情
     *
     * @param lawId 法规ID
     * @return 法规详情
     */
    Result<LawRegulationDetailVO> getLawDetail(Long lawId);
}
