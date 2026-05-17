package com.example.contractreview.controller;

import com.example.contractreview.common.Result;
import com.example.contractreview.mapper.ReviewMapper;
import com.example.contractreview.model.dto.StartReviewDTO;
import com.example.contractreview.model.vo.LatestReviewVO;
import com.example.contractreview.model.vo.ReportPreviewVO;
import com.example.contractreview.model.vo.ReviewHistoryStatsVO;
import com.example.contractreview.model.vo.ReviewHistoryVO;
import com.example.contractreview.model.vo.fastapi.ReviewResultVO;
import com.example.contractreview.model.vo.RiskItemVO;
import com.example.contractreview.service.ReviewService;
import com.example.contractreview.utils.GetContractNameUtils;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.InputStreamResource;
import org.springframework.core.io.Resource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.ByteArrayInputStream;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/review")
@Slf4j
@Tag(name = "ReviewController", description = "合同审核")
@RequiredArgsConstructor
public class ReviewController {

    private final ReviewService reviewService;
    private final ObjectMapper objectMapper;
    private final GetContractNameUtils getContractNameUtils;

    /**
     * 发起合同审查
     */
    @PostMapping(value = "/start", consumes = "multipart/form-data")
    @Operation(summary = "发起合同审查")
    public Result<Map<String, Object>> startReview(
            @RequestHeader("Authorization") String authorization,
            @RequestParam("contractId") Integer contractId,
            @RequestParam(value = "file") MultipartFile file,
            @RequestParam(value = "reviewOptions") String reviewOptionsJson) {
        log.info("发起合同审查, contractId: {}", contractId);
        StartReviewDTO dto = new StartReviewDTO();
        dto.setContractId(contractId);
        dto.setFile(file);
        if (reviewOptionsJson != null && !reviewOptionsJson.isEmpty()) {
            try {
                StartReviewDTO.ReviewOptionsDTO options = objectMapper.readValue(reviewOptionsJson, StartReviewDTO.ReviewOptionsDTO.class);
                dto.setReviewOptions(options);
            } catch (Exception e) {
                dto.setReviewOptions(new StartReviewDTO.ReviewOptionsDTO(true, true, true, true));
            }
        } else {
            dto.setReviewOptions(new StartReviewDTO.ReviewOptionsDTO(true, true, true, true));
        }
        return reviewService.startReview(authorization, dto);
    }

    /**
     * 获取审查进度（SSE 实时推送）
     */
    @GetMapping("/{reviewId}/progress")
    @Operation(summary = "获取审查进度（SSE）")
    public SseEmitter getReviewProgress(
            @RequestHeader(value = "Authorization", required = false) String authorization,
            @RequestParam(value = "token", required = false) String tokenParam,
            @PathVariable Integer reviewId) {
        log.info("获取审查进度, reviewId: {}", reviewId);
        String auth = (authorization != null && !authorization.isEmpty()) ? authorization 
                      : (tokenParam != null && !tokenParam.isEmpty() ? "Bearer " + tokenParam : "");
        return reviewService.connectProgress(auth, reviewId);
    }

    /**
     * 获取审查结果
     */
    @GetMapping("/{reviewId}/result")
    @Operation(summary = "获取审查结果")
    public Result<ReviewResultVO> getReviewResult(@RequestHeader("Authorization") String authorization,
                                                  @PathVariable Integer reviewId) {
        log.info("获取审查结果, reviewId: {}", reviewId);
        return reviewService.getReviewResult(authorization, reviewId);
    }

    /**
     * 获取风险列表
     */
    @GetMapping("/{reviewId}/risks")
    @Operation(summary = "获取风险列表")
    public Result<List<RiskItemVO>> getRiskList(@RequestHeader("Authorization") String authorization,
                                          @PathVariable Integer reviewId,
                                          @RequestParam(required = false) String level,
                                          @RequestParam(required = false, defaultValue = "1") Integer page,
                                          @RequestParam(required = false, defaultValue = "10") Integer pageSize) {
        log.info("获取风险列表, reviewId: {}, level: {}", reviewId, level);
        return reviewService.getRiskList(authorization, reviewId, level, page, pageSize);
    }

    /**
     * 重新审查
     */
    @PostMapping(value = "/{reviewId}/re-review", consumes = "multipart/form-data")
    @Operation(summary = "重新审查")
    public Result<Map<String, Object>> reReview(@RequestHeader("Authorization") String authorization,
                                                @PathVariable Integer reviewId,
                                                @RequestParam("contractId") Integer contractId,
                                                @RequestParam(value = "file", required = false) MultipartFile file,
                                                @RequestParam(value = "reviewOptions", required = false) String reviewOptionsJson) {
        log.info("重新审查, reviewId: {}, contractId: {}", reviewId, contractId);

        // 构建 DTO
        StartReviewDTO dto = new StartReviewDTO();
        dto.setContractId(contractId);
        dto.setFile(file);

        // 解析审查选项 JSON
        if (reviewOptionsJson != null && !reviewOptionsJson.isEmpty()) {
            try {
                StartReviewDTO.ReviewOptionsDTO options = objectMapper.readValue(reviewOptionsJson, StartReviewDTO.ReviewOptionsDTO.class);
                dto.setReviewOptions(options);
            } catch (Exception e) {
                // 使用默认选项
                dto.setReviewOptions(new StartReviewDTO.ReviewOptionsDTO(true, true, true, true));
            }
        } else {
            // 使用默认选项
            dto.setReviewOptions(new StartReviewDTO.ReviewOptionsDTO(true, true, true, true));
        }

        return reviewService.reReview(authorization, reviewId, dto);
    }

    /**
     * 取消审查
     */
    @PostMapping("/{reviewId}/cancel")
    @Operation(summary = "取消审查")
    public Result<Map<String, Object>> cancelReview(@RequestHeader("Authorization") String authorization,
                                                    @PathVariable Integer reviewId) {
        log.info("取消审查, reviewId: {}", reviewId);
        return reviewService.cancelReview(authorization, reviewId);
    }

    // ==================== 历史记录相关接口 ====================

    /**
     * 合同审核历史统计
     */
    @GetMapping("/history/stats")
    @Operation(summary = "合同审核历史统计")
    public Result<ReviewHistoryStatsVO> getContractHistoryStats(@RequestHeader("Authorization") String authorization) {
        return reviewService.getContractHistoryStats(authorization);
    }

    /**
     * 获取审查历史列表
     */
    @GetMapping("/history")
    @Operation(summary = "获取审查历史列表")
    public Result<List<ReviewHistoryVO>> getContractHistoryList(@RequestHeader("Authorization") String authorization,
                                                                @RequestParam(required = false, defaultValue = "1") Integer page,
                                                                @RequestParam(required = false, defaultValue = "10") Integer pageSize,
                                                                @RequestParam(required = false) String keyword,
                                                                @RequestParam(required = false) LocalDate startDate,
                                                                @RequestParam(required = false) LocalDate endDate) {
        return reviewService.getContractHistoryList(authorization, page, pageSize, keyword, startDate, endDate);
    }

    /**
     * 删除审查历史
     */
    @DeleteMapping("/{reviewId}")
    @Operation(summary = "删除审查历史")
    public Result<String> deleteContractHistory(@RequestHeader("Authorization") String authorization,
                                                @PathVariable Integer reviewId) {
        return reviewService.deleteContractHistory(authorization, reviewId);
    }

    // ==================== 合同审查记录查询接口 ====================

    /**
     * 根据合同ID获取最新审查记录
     * 用于检查合同是否已有审查记录，避免重复审查
     */
    @GetMapping("/contract/{contractId}/latest")
    @Operation(summary = "获取合同最新审查记录")
    public Result<LatestReviewVO> getLatestReviewByContractId(
            @RequestHeader("Authorization") String authorization,
            @PathVariable Integer contractId) {
        return reviewService.getLatestReviewByContractId(authorization, contractId);
    }

    // ==================== PDF 报告相关接口 ====================

    /**
     * 下载审查报告 PDF
     */
    @GetMapping("/{reviewId}/report/pdf")
    @Operation(summary = "下载审查报告 PDF")
    public ResponseEntity<Resource> downloadReport(
            @RequestHeader("Authorization") String authorization,
            @PathVariable Integer reviewId) {
        log.info("下载审查报告 PDF, reviewId: {}", reviewId);
        return reviewService.generatePdfResponse(reviewId, "attachment; filename=\"" + getContractNameUtils.getContractName(reviewId) + "-审查报告\"", authorization);
    }

    /**
     * 在线预览审查报告 - 返回 JSON 数据供前端渲染
     */
    @GetMapping("/{reviewId}/report/view")
    @Operation(summary = "在线预览审查报告")
    public Result<ReportPreviewVO> viewReport(
            @RequestHeader("Authorization") String authorization,
            @PathVariable Integer reviewId) {
        log.info("预览审查报告, reviewId: {}", reviewId);
        return reviewService.getReportPreview(authorization, reviewId);
    }
}
