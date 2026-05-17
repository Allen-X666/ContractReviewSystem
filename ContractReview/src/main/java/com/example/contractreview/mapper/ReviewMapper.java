package com.example.contractreview.mapper;

import com.example.contractreview.common.Result;
import com.example.contractreview.model.vo.ReportPreviewVO;
import com.example.contractreview.model.vo.ReviewHistoryStatsVO;
import com.example.contractreview.model.vo.ReviewHistoryVO;
import com.example.contractreview.model.vo.fastapi.ReviewResultVO;
import com.example.contractreview.model.vo.fastapi.RiskItemVO;
import org.apache.ibatis.annotations.MapKey;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;

@Mapper
public interface ReviewMapper {

    // 合同审核历史统计
    ReviewHistoryStatsVO getContractHistoryStats(Integer userId);

    // 获取审查历史列表
    List<ReviewHistoryVO> getContractHistoryList(Integer userId, String keyword, LocalDate startDate, LocalDate endDate);

    // 删除审查历史
    int deleteContractHistory(Integer userId, String reviewId);

    // 添加审查记录
    void addReviewRecord(@Param("reviewId") Integer reviewId, @Param("reviewNo") String reviewNo, @Param("contractId") Integer contractId, @Param("userId") Integer userId, @Param("status") String status);

    // 更新审查结果
    void updateReviewResult(Integer userId, Integer reviewId, @Param("reviewResultVo") ReviewResultVO resultVO);

    // 根据审查ID删除风险项
    void deleteRiskItemsByReviewId(Integer reviewId);

    // 插入风险项
    void insertRiskItem(@Param("reviewId") Integer reviewId,
                       @Param("contractId") Integer contractId,
                       @Param("risk") RiskItemVO risk);

    // 批量插入风险项
    void batchInsertRiskItems(@Param("reviewId") Integer reviewId,
                              @Param("contractId") Integer contractId,
                              @Param("risks") List<RiskItemVO> risks);

    // 获取合同标题
    String getContractTitle(Integer reviewId);

    // 更新审查状态
    void updateReviewStatus(Integer reviewId, String status);

    // 获取风险项列表
    List<com.example.contractreview.model.vo.RiskItemVO> selectRiskList(Integer reviewId, String level, Integer page, Integer pageSize);

    /**
     * 根据合同ID获取最新审查记录
     * @param contractId 合同ID
     * @param userId 用户ID
     * @return 最新审查记录
     */
    com.example.contractreview.model.vo.LatestReviewVO getLatestReviewByContractId(@Param("contractId") Integer contractId, @Param("userId") Integer userId);

    /**
     * 获取报告预览数据
     * @param reviewId 审查ID
     * @param userId 用户ID
     * @return 报告预览数据
     */
    ReportPreviewVO getReportPreview(@Param("reviewId") Integer reviewId, @Param("userId") Integer userId);

    /**
     * 获取审查任务基本信息
     * @param reviewId 审查ID
     * @param userId 用户ID
     * @return 审查任务信息
     */
    Map<String, Object> getReviewTaskInfo(@Param("reviewId") Integer reviewId, @Param("userId") Integer userId);

    /**
     * 根据 review_no 更新审查状态
     * @param reviewNo 审查编号
     * @param status 状态
     */
    void updateReviewStatusByReviewNo(@Param("reviewNo") Integer reviewNo, @Param("status") String status);

    /**
     * 批量获取合同最新审查记录ID
     * @param contractIds 合同ID列表
     * @param userId 用户ID
     * @return 每个合同的最新 review_task.id，字段: contractId, reviewId
     */
    List<Map<String, Object>> getLatestReviewIdsByContractIds(@Param("contractIds") List<Integer> contractIds, @Param("userId") Integer userId);

    /**
     * 重新审查时更新review_task表
     * @param reviewId 审查ID
     */
    void updateReviewTaskForReReview(@Param("reviewId") Integer reviewId);
}
