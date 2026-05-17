package com.example.contractreview.service;

import com.example.contractreview.common.Result;
import com.example.contractreview.model.dto.StartReviewDTO;
import com.example.contractreview.model.vo.LatestReviewVO;
import com.example.contractreview.model.vo.ReportPreviewVO;
import com.example.contractreview.model.vo.ReviewHistoryStatsVO;
import com.example.contractreview.model.vo.ReviewHistoryVO;
import com.example.contractreview.model.vo.RiskItemVO;
import com.example.contractreview.model.vo.fastapi.ReviewResultVO;
import org.springframework.core.io.Resource;
import org.springframework.http.ResponseEntity;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;

public interface ReviewService {

    /**
     * 发起合同审查
     */
    Result<Map<String, Object>> startReview(String authorization, StartReviewDTO dto);

    /**
     * 连接审查进度（SSE）
     */
    SseEmitter connectProgress(String authorization, Integer reviewId);

    /**
     * 获取审查结果
     */
    Result<ReviewResultVO> getReviewResult(String authorization, Integer reviewId);

    /**
     * 获取风险列表
     */
    Result<List<RiskItemVO>> getRiskList(String authorization, Integer reviewId, String level, Integer page, Integer pageSize);

    /**
     * 重新审查
     */
    Result<Map<String, Object>> reReview(String authorization, Integer reviewId,StartReviewDTO dto);

    /**
     * 撤销合同审查
     */
    Result<Map<String, Object>> cancelReview(String authorization, Integer reviewId);

    /**
     * 合同审核历史统计
     */
    Result<ReviewHistoryStatsVO> getContractHistoryStats(String authorization);

    /**
     * 获取审查历史列表
     */
    Result<List<ReviewHistoryVO>> getContractHistoryList(String authorization, Integer page, Integer pageSize, String keyword, LocalDate startDate, LocalDate endDate);

    /**
     * 删除审查历史
     */
    Result<String> deleteContractHistory(String authorization, Integer reviewId);

    /**
     * 生成审查报告PDF
     * @param reviewId 审查ID
     * @return PDF字节数组
     */
    byte[] generateReviewReport(Integer reviewId, String contractName, String authorization);

    /**
     * 根据合同ID获取最新审查记录
     * @param authorization 认证令牌
     * @param contractId 合同ID
     * @return 最新审查记录
     */
    Result<LatestReviewVO> getLatestReviewByContractId(String authorization, Integer contractId);

    /**
     * 获取报告预览数据
     * @param authorization 认证令牌
     * @param reviewId 审查ID
     * @return 报告预览数据
     */
    Result<ReportPreviewVO> getReportPreview(String authorization, Integer reviewId);

    ResponseEntity<Resource> generatePdfResponse(Integer reviewId, String s, String authorization);
}
