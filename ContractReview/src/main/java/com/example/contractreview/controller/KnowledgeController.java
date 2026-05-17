package com.example.contractreview.controller;

import com.example.contractreview.common.Result;
import com.example.contractreview.model.vo.KnowledgeStatsVO;
import com.example.contractreview.model.vo.LawCategoryGroupVO;
import com.example.contractreview.model.vo.LawCategoryVO;
import com.example.contractreview.model.vo.LawRegulationDetailVO;
import com.example.contractreview.model.vo.LawRegulationVO;
import com.example.contractreview.service.KnowledgeService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/knowledge")
@Slf4j
@Tag(name = "知识管理")
@RequiredArgsConstructor
public class KnowledgeController {

    private final KnowledgeService knowledgeService;

    @GetMapping("/stats")
    @Operation(summary = "获取知识库统计数据")
    public Result<KnowledgeStatsVO> getKnowledgeStats() {
        return knowledgeService.getKnowledgeStats();
    }

    @GetMapping("/laws/categories")
    @Operation(summary = "获取法条分类列表")
    public Result<List<LawCategoryVO>> getLawCategories() {
        return knowledgeService.getLawCategories();
    }

    @GetMapping("/laws/search")
    @Operation(summary = "搜索法条（按分类分组）")
    public Result<List<LawCategoryGroupVO>> searchLawsGrouped(
            @Parameter(description = "关键词") @RequestParam(required = false) String keyword,
            @Parameter(description = "页码") @RequestParam(required = false, defaultValue = "1") Integer page,
            @Parameter(description = "每页大小") @RequestParam(required = false, defaultValue = "100") Integer pageSize) {
        return knowledgeService.searchLawsGroupedByCategory(keyword, page, pageSize);
    }

    @GetMapping("/laws/{lawId}")
    @Operation(summary = "获取法条详情")
    public Result<LawRegulationDetailVO> getLawDetail(
            @Parameter(description = "法条ID") @PathVariable("lawId") Long lawId) {
        return knowledgeService.getLawDetail(lawId);
    }
}
