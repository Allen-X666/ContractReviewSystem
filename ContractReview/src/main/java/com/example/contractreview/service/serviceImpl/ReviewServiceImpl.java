package com.example.contractreview.service.serviceImpl;

import com.example.contractreview.client.FastApiClient;
import com.example.contractreview.common.Result;
import com.example.contractreview.constant.ContractConstant;
import com.example.contractreview.constant.ReviewConstant;
import com.example.contractreview.enums.NotificationType;
import com.example.contractreview.enums.ReviewStatus;
import com.example.contractreview.enums.RiskLevel;
import com.example.contractreview.mapper.ContractMapper;
import com.example.contractreview.mapper.ReviewMapper;
import com.example.contractreview.model.dto.StartReviewDTO;
import com.example.contractreview.model.entity.Contract;
import com.example.contractreview.model.vo.*;
import com.example.contractreview.model.vo.fastapi.FastApiResult;
import com.example.contractreview.model.vo.fastapi.ReviewProgressVO;
import com.example.contractreview.model.vo.fastapi.ReviewResultVO;
import com.example.contractreview.service.AsyncMailService;
import com.example.contractreview.service.PdfReportService;
import com.example.contractreview.service.ReviewService;
import com.example.contractreview.sse.SseEmitterManager;
import com.example.contractreview.utils.GetContractNameUtils;
import com.example.contractreview.utils.GetUserSystemConfigUtils;
import com.example.contractreview.utils.TokenUtils;
import com.example.contractreview.utils.UserEmailUtils;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.pagehelper.PageHelper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.InputStreamResource;
import org.springframework.core.io.Resource;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.interceptor.TransactionAspectSupport;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

@Slf4j
@Service
@RequiredArgsConstructor
public class ReviewServiceImpl implements ReviewService {

    private final FastApiClient fastApiClient;
    private final ReviewMapper reviewMapper;
    private final PdfReportService pdfReportService;
    private final TokenUtils tokenUtils;
    private final ContractMapper contractMapper;
    private final StringRedisTemplate stringRedisTemplate;
    private final ObjectMapper objectMapper;
    private final GetContractNameUtils getContractNameUtils;
    private final AsyncMailService asyncMailService;
    private final UserEmailUtils userEmailUtils;
    private final SseEmitterManager sseEmitterManager;

    private final ScheduledExecutorService scheduler = Executors.newScheduledThreadPool(10);
    private final GetUserSystemConfigUtils getUserSystemConfigUtils;

    /**
     * 启动审查
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public Result<Map<String, Object>> startReview(String authorization, StartReviewDTO dto) {
        Integer userId = tokenUtils.getUserId(authorization);
        Contract contract = contractMapper.selectById(Long.valueOf(dto.getContractId()));
        if (!ReviewStatus.COMPLETED.getCode().equals(contract.getReviewStatus())) {
            try {
                // 调用 FastAPI 发起审查   FastAPI 返回数据:
                // FastApiResult(code=200, message=success, data={reviewId=1, contractId=10, status=processing, message=审查任务已启动，请使用 reviewId 查询进度})
                FastApiResult<Map<String, Object>> fastApiResult = fastApiClient.startReview(dto, authorization);
                log.info("FastAPI 返回数据: {}", fastApiResult);
                if (fastApiResult == null || !fastApiResult.isSuccess()) {
                    String errorMsg = fastApiResult != null ? fastApiResult.getMessage() : "AI 服务返回空结果";
                    log.error("发起审查失败: {}", errorMsg);
                    return Result.error(errorMsg);
                }

                // 异步保存审查记录到数据库，不阻塞返回
                final Integer finalUserId = userId;
                final Map<String, Object> fastApiData = fastApiResult.getData();
                scheduler.execute(() -> {
                    try {
                        saveReviewRecord(finalUserId, dto.getContractId(), fastApiData);
                        log.info("异步保存审查记录成功, contractId: {}, reviewId: {}",
                                dto.getContractId(), fastApiData.get("review_id"));
                    } catch (Exception e) {
                        log.error("异步保存审查记录失败: {}", e.getMessage(), e);
                    }
                });

                log.info("发起审查成功, contractId: {}, reviewId: {}",
                        dto.getContractId(), fastApiData.get("review_id"));

                return Result.success(fastApiData);
            } catch (Exception e) {
                log.error("发起审查异常: {}", e.getMessage(), e);
                // 手动回滚事务
                TransactionAspectSupport.currentTransactionStatus().setRollbackOnly();
                return Result.error("发起审查失败: " + e.getMessage());
            }
        } else {
            log.warn("合同已审查完成, contractId: {}", dto.getContractId());
            return Result.error("合同已审查完成");
        }
    }

    /**
     * 获取审查进度
     */
    @Override
    public SseEmitter connectProgress(String authorization, Integer reviewId) {
        // 获取用户ID，用于注册到SseEmitterManager
        Integer userId = tokenUtils.getUserId(authorization);
        if (userId == null) {
            throw new RuntimeException("无效的授权信息");
        }
        
        // 创建 SSE 发射器，超时时间 30 分钟
        // 同时注册到SseEmitterManager，以便接收通知
        SseEmitter emitter = sseEmitterManager.createEmitter(Long.valueOf(userId), 1800000L);
        
        log.info("审查进度SSE连接已创建并注册到通知管理器, userId: {}, reviewId: {}", userId, reviewId);

        // 定时任务：轮询 FastAPI 获取进度
        final ScheduledExecutorService progressScheduler = Executors.newSingleThreadScheduledExecutor();

        emitter.onCompletion(() -> {
            log.info("SSE 连接完成, reviewId: {}", reviewId);
            progressScheduler.shutdown();
        });

        emitter.onTimeout(() -> {
            log.warn("SSE 连接超时, reviewId: {}", reviewId);
            progressScheduler.shutdown();
        });

        emitter.onError((e) -> {
            log.error("SSE 连接错误, reviewId: {}", reviewId, e);
            progressScheduler.shutdown();
        });

        // 每 2 秒轮询一次进度
        progressScheduler.scheduleAtFixedRate(() -> {
            try {
                FastApiResult<ReviewProgressVO> result = fastApiClient.getReviewProgress(reviewId, authorization);

                if (result != null && result.isSuccess() && result.getData() != null) {
                    ReviewProgressVO progress = result.getData();

                    // 发送进度事件
                    SseEmitter.SseEventBuilder event = SseEmitter.event()
                            .name("progress")
                            .data(progress, MediaType.APPLICATION_JSON);
                    emitter.send(event);

                    // 如果审查完成或失败，关闭连接
                    if ("completed".equals(progress.getStatus()) || "failed".equals(progress.getStatus())) {
                        // 使用已获取的userId，不再重新获取
                        userEmailUtils.userEmailUtils(userId, "合同审查完毕", "您的合同审查完毕，请返回系统查看详情。");

                        Map<String, String> userSystemConfig = getUserSystemConfigUtils.getUserSystemConfig(userId);
                        String message = userSystemConfig.get("message");
                        if (message.equals("获取用户系统配置成功")) {
                            String reviewComplete = userSystemConfig.get("reviewComplete");
                            if (reviewComplete.equals("true")) {
                                log.info("开始发送审查完成SSE通知");
                                // 发送SSE通知（审查完成）
                                try {
                                    // 获取合同名称
                                    String contractName = getContractNameUtils.getContractName(reviewId);
                                    if (contractName != null) {
                                        int connectionCount = sseEmitterManager.getConnectionCount();
                                        log.info("准备发送审查完成SSE通知, userId: {}, reviewId: {}, 当前在线连接数: {}",
                                                userId, reviewId, connectionCount);

                                        sseEmitterManager.sendReviewCompleteNotification(
                                                Long.valueOf(userId),
                                                Long.valueOf(reviewId),
                                                null,
                                                contractName,
                                                progress.getProgress()
                                        );
                                        log.info("审查完成SSE通知已发送, userId: {}, reviewId: {}, 目标用户数: {}",
                                                userId, reviewId, connectionCount);
                                    }
                                } catch (Exception e) {
                                    log.error("发送审查完成SSE通知失败, reviewId: {}", reviewId, e);
                                }
                            } else {
                                log.info("用户未开启邮件通知");
                            }
                        }
                        emitter.complete();
                        progressScheduler.shutdown();
                    }
                }
            } catch (org.springframework.web.context.request.async.AsyncRequestNotUsableException e) {
                // 客户端断开连接（如用户取消审查），正常关闭
                log.info("SSE 连接已断开, reviewId: {}, 原因: 客户端取消", reviewId);
                progressScheduler.shutdown();
            } catch (org.apache.catalina.connector.ClientAbortException e) {
                // 客户端中止连接，正常关闭
                log.info("SSE 连接已断开, reviewId: {}, 原因: 客户端中止", reviewId);
                progressScheduler.shutdown();
            } catch (IOException e) {
                // IO 异常，通常是连接问题
                if (e.getMessage() != null && e.getMessage().contains("中止了一个已建立的连接")) {
                    log.info("SSE 连接已断开, reviewId: {}, 原因: 客户端关闭", reviewId);
                } else {
                    log.warn("SSE IO 异常, reviewId: {}", reviewId, e);
                }
                progressScheduler.shutdown();
            } catch (Exception e) {
                log.error("获取审查进度异常, reviewId: {}", reviewId, e);
                try {
                    emitter.send(SseEmitter.event()
                            .name("error")
                            .data("获取进度失败: " + e.getMessage()));
                } catch (Exception sendException) {
                    // 发送错误事件失败，可能是连接已断开
                    log.debug("发送 SSE 错误事件失败, reviewId: {}", reviewId);
                }
            }
        }, 0, 2, TimeUnit.SECONDS);

        return emitter;
    }

    /**
     * 获取审查结果
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public Result<ReviewResultVO> getReviewResult(String authorization, Integer reviewId) {
        Integer userId = tokenUtils.getUserId(authorization);
        try {
            ReviewResultVO cachedResult = getCachedReviewResult(reviewId);
            if (cachedResult != null) {
                return Result.success(cachedResult);
            }
            FastApiResult<com.example.contractreview.model.vo.fastapi.ReviewResultVO> fastApiResult =
                    fastApiClient.getReviewResult(reviewId, authorization);

            log.info("FastAPI 获取结果数据1: {}", fastApiResult);
            if (fastApiResult == null || !fastApiResult.isSuccess()) {
                String errorMsg = fastApiResult != null ? fastApiResult.getMessage() : "AI 服务返回空结果";
                return Result.error(errorMsg);
            }

            ReviewResultVO fastApiData = fastApiResult.getData();
            fastApiData.setCompletedAt(LocalDateTime.parse(LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME)));

            enrichContractName(fastApiData);
            sortRisksByLevel(fastApiData.getRisks());

            Map<String, String> userSystemConfig = getUserSystemConfigUtils.getUserSystemConfig(userId);
            String message = userSystemConfig.get("message");
            if (message.equals("获取用户系统配置成功")) {
                String riskAlert = userSystemConfig.get("riskAlert");
                if (riskAlert.equals("true")) {
                    log.info("开始发送高风险预警");
                    // 检测高风险并发送SSE通知
                    checkAndNotifyHighRisk(userId, reviewId, fastApiData);
                }
                else {
                    log.info("用户未开启邮件通知");
                }
            }
            String key = ReviewConstant.REVIEW_RESULT_KEY + reviewId;
            stringRedisTemplate.opsForValue().set(key, objectMapper.writeValueAsString(fastApiData));
            updateReviewResult(userId, reviewId, fastApiData);

            return Result.success(fastApiData);
        } catch (Exception e) {
            log.error("获取审查结果异常: {}", e.getMessage(), e);
            return Result.error("获取审查结果失败: " + e.getMessage());
        }
    }

    /**
     * 获取风险列表
     */
    public Result<List<RiskItemVO>> getRiskList(String authorization,
                                                Integer reviewId,
                                                String level,
                                                Integer page,
                                                Integer pageSize) {
        try {
            PageHelper.startPage(page, pageSize);
            List<RiskItemVO> result = reviewMapper.selectRiskList(reviewId, level, page, pageSize);
            log.info("获取风险列表成功: {}", result);
            return Result.success(result);
        } catch (Exception e) {
            log.error("获取风险列表异常: {}", e.getMessage(), e);
            return Result.error("获取风险列表失败: " + e.getMessage());
        }
    }

    /**
     * 重新审查
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public Result<Map<String, Object>> reReview(String authorization, Integer reviewId, StartReviewDTO dto) {
        try {
            String key = ReviewConstant.REVIEW_RESULT_KEY + reviewId;
            stringRedisTemplate.delete(key);

            // 1. 重置contract审查状态
            contractMapper.resetReviewStatus(Long.valueOf(dto.getContractId()));
            log.info("重置contract表为重新审查状态, contractId: {}", dto.getContractId());

            // 2. 更新review_task的status为processing，progress为0，删除overall_score，conclusion，completed_at
            reviewMapper.updateReviewTaskForReReview(reviewId);
            log.info("更新review_task表为重新审查状态, reviewId: {}", reviewId);

            // 3. 删除risk_item的有关数据
            reviewMapper.deleteRiskItemsByReviewId(reviewId);
            log.info("删除risk_item数据, reviewId: {}", reviewId);

            FastApiResult<Map<String, Object>> fastApiResult = fastApiClient.startReview(dto, authorization);

            if (fastApiResult == null || !fastApiResult.isSuccess()) {
                String errorMsg = fastApiResult != null ? fastApiResult.getMessage() : "AI 服务返回空结果";
                return Result.error(errorMsg);
            }

            return Result.success(fastApiResult.getData());
        } catch (Exception e) {
            log.error("重新审查异常: {}", e.getMessage(), e);
            return Result.error("重新审查失败: " + e.getMessage());
        }
    }

    /**
     * 取消审查
     */
    @Override
    public Result<Map<String, Object>> cancelReview(String authorization, Integer reviewId) {
        try {
            FastApiResult<Map<String, Object>> fastApiResult = fastApiClient.cancelReview(reviewId, authorization);

            if (fastApiResult == null || !fastApiResult.isSuccess()) {
                String errorMsg = fastApiResult != null ? fastApiResult.getMessage() : "AI 服务返回空结果";
                return Result.error(errorMsg);
            }

            // 更新数据库中的审查状态
            reviewMapper.updateReviewStatus(reviewId, "cancelled");

            return Result.success(fastApiResult.getData());
        } catch (Exception e) {
            log.error("取消审查异常: {}", e.getMessage(), e);
            return Result.error("取消审查失败: " + e.getMessage());
        }
    }

    /**
     * 获取合同审查历史统计
     */
    @Override
    public Result<ReviewHistoryStatsVO> getContractHistoryStats(String authorization) {
        try {
            // 从 token 中获取用户ID
            Integer userId = tokenUtils.getUserId(authorization);

            ReviewHistoryStatsVO stats = reviewMapper.getContractHistoryStats(userId);
            if (stats == null) {
                stats = new ReviewHistoryStatsVO();
                stats.setTotal(0);
                stats.setThisMonth(0);
                stats.setAvgScore(0);
                stats.setTotalIssues(0);
            }

            return Result.success(stats);
        } catch (Exception e) {
            log.error("获取审查历史统计异常: {}", e.getMessage(), e);
            return Result.error("获取统计信息失败: " + e.getMessage());
        }
    }

    /**
     * 获取合同审查历史列表
     */
    @Override
    public Result<List<ReviewHistoryVO>> getContractHistoryList(String authorization, Integer page, Integer pageSize,
                                                                 String keyword, LocalDate startDate, LocalDate endDate) {
        try {
            Integer userId = tokenUtils.getUserId(authorization);

            List<ReviewHistoryVO> list = reviewMapper.getContractHistoryList(userId, keyword, startDate, endDate);

            return Result.success(list);
        } catch (Exception e) {
            log.error("获取审查历史列表异常: {}", e.getMessage(), e);
            return Result.error("获取历史列表失败: " + e.getMessage());
        }
    }

    /**
     * 删除合同审查历史
     */
    @Override
    public Result<String> deleteContractHistory(String authorization, Integer reviewId) {
        try {
            Integer userId = tokenUtils.getUserId(authorization);
            String key = ReviewConstant.REVIEW_RESULT_KEY + reviewId;
            stringRedisTemplate.delete(key);
            contractMapper.resetReviewStatus(Long.valueOf(reviewId));
            log.info("重置contract表, contractId: {}", reviewId);
            int affected = reviewMapper.deleteContractHistory(userId, String.valueOf(reviewId));
            if (affected > 0) {
                return Result.success("删除成功");
            } else {
                return Result.error("删除失败，记录不存在或无权限");
            }
        } catch (Exception e) {
            log.error("删除审查历史异常: {}", e.getMessage(), e);
            return Result.error("删除失败: " + e.getMessage());
        }
    }

    // ==================== 私有方法 ====================

    @Transactional(rollbackFor = Exception.class)
    protected void saveReviewRecord(Integer useId, Integer contractId, Map<String, Object> fastApiData) {
        // FastAPI 返回的字段名可能是 review_id 或 reviewId
        Object reviewIdObj = fastApiData.get("review_id") != null ? fastApiData.get("review_id") : fastApiData.get("reviewId");
        Integer reviewId = Integer.parseInt(reviewIdObj.toString());
        // 获取 reviewNo，如果没有则使用 reviewId 作为字符串
        Object reviewNoObj = fastApiData.get("review_no") != null ? fastApiData.get("review_no") : fastApiData.get("reviewNo");
        String reviewNo = reviewNoObj != null ? reviewNoObj.toString() : String.valueOf(reviewId);
        String status = fastApiData.get("status").toString();
        
        // 检查是否已存在相同的 review_no
        Map<String, Object> existingTask = reviewMapper.getReviewTaskInfo(reviewId, useId);
        if (existingTask != null) {
            log.info("审查记录已存在，更新状态, reviewId: {}", reviewId);
            // 更新现有记录的状态
            reviewMapper.updateReviewStatusByReviewNo(reviewId, status);
        } else {
            // 插入新记录
            reviewMapper.addReviewRecord(reviewId, reviewNo, contractId, useId, status);
        }
    }

    /**
     * 更新合同审查结果
     */
    private void updateReviewResult(Integer userId, Integer reviewId, ReviewResultVO resultVO) {
        try {
            log.info("更新合同审查结果: reviewId:{},{}", reviewId, resultVO);
            // 更新review_task表
            reviewMapper.updateReviewResult(userId, reviewId, resultVO);

            // 批量插入风险项，减少数据库往返次数
            if (resultVO.getRisks() != null && !resultVO.getRisks().isEmpty()) {
                reviewMapper.batchInsertRiskItems(reviewId, resultVO.getContractId(), resultVO.getRisks());
            }
            // 更新contract表中数据
            stringRedisTemplate.delete(ContractConstant.CONTRACT_STATS_KEY_PREFIX + userId);
            reviewMapper.updateReviewStatus(reviewId, "completed");
            Integer score = resultVO.getOverallScore();
            String level = String.valueOf(RiskLevel.EMPTY);
            if (score != null && score > 90) {
                level = String.valueOf(RiskLevel.EMPTY);
            } else if (score != null && score >= 80) {
                level = String.valueOf(RiskLevel.LOW);
            } else if (score != null && score >= 60) {
                level = String.valueOf(RiskLevel.MEDIUM);
            } else if (score != null) {
                level = String.valueOf(RiskLevel.HIGH);
            }
            Contract completed = Contract.builder().id(resultVO.getContractId()).reviewStatus("completed").reviewScore(score).riskLevel(level).build();
            contractMapper.update(completed);
            log.info("更新contract表中数据成功");
            log.info("更新审查结果成功, reviewId: {}, 风险项数量: {}", 
                    reviewId, resultVO.getRisks() != null ? resultVO.getRisks().size() : 0);
        } catch (Exception e) {
            log.error("更新审查结果失败, reviewId: {}", reviewId, e);
            throw new RuntimeException("更新审查结果失败", e);
        }
    }

    /**
     * 生成 PDF 响应
     */
    @Override
    public ResponseEntity<Resource> generatePdfResponse(Integer reviewId, String contentDisposition, String authorization) {
        try {
            String contractName = getContractNameUtils.getContractName(reviewId);
            byte[] pdfBytes = generateReviewReport(reviewId, contractName, authorization);

            ByteArrayInputStream bis = new ByteArrayInputStream(pdfBytes);
            Resource resource = new InputStreamResource(bis);

            return ResponseEntity.ok()
                    .contentType(MediaType.APPLICATION_PDF)
                    .header(HttpHeaders.CONTENT_DISPOSITION, contentDisposition)
                    .contentLength(pdfBytes.length)
                    .body(resource);

        } catch (org.springframework.web.client.HttpClientErrorException.NotFound e) {
            log.error("审查任务不存在, reviewId: {}", reviewId);
            return ResponseEntity.status(404)
                    .body(null);
        } catch (Exception e) {
            return ResponseEntity.internalServerError().build();
        }
    }
    /**
     * 同步生成审查报告PDF
     */
    @Override
    public byte[] generateReviewReport(Integer reviewId, String contractName, String authorization) {
        try {
            log.info("开始生成审查报告 PDF, reviewId: {}", reviewId);

            // 优先从 Redis 缓存获取审查结果
            com.example.contractreview.model.vo.fastapi.ReviewResultVO reviewResult = null;
            String key = ReviewConstant.REVIEW_RESULT_KEY + reviewId;
            String cachedResult = stringRedisTemplate.opsForValue().get(key);

            if (cachedResult != null && !cachedResult.isEmpty()) {
                try {
                    reviewResult = objectMapper.readValue(cachedResult,
                            com.example.contractreview.model.vo.fastapi.ReviewResultVO.class);
                    log.info("从 Redis 缓存获取审查结果成功, reviewId: {}", reviewId);
                } catch (Exception e) {
                    log.warn("从 Redis 解析审查结果失败, reviewId: {}, 尝试从 FastAPI 获取", reviewId, e);
                }
            }

            // 如果缓存中没有，尝试从 FastAPI 获取
            if (reviewResult == null) {
                FastApiResult<com.example.contractreview.model.vo.fastapi.ReviewResultVO> fastApiResult =
                        fastApiClient.getReviewResult(reviewId, authorization);

                if (fastApiResult == null || !fastApiResult.isSuccess() || fastApiResult.getData() == null) {
                    log.error("获取审查结果失败，无法生成 PDF, reviewId: {}", reviewId);
                    throw new RuntimeException("获取审查结果失败，审查任务可能不存在或未完成");
                }

                reviewResult = fastApiResult.getData();
                log.info("从 FastAPI 获取审查结果成功, reviewId: {}", reviewId);

                // 缓存结果
                try {
                    stringRedisTemplate.opsForValue().set(key, objectMapper.writeValueAsString(reviewResult));
                } catch (Exception e) {
                    log.warn("缓存审查结果失败, reviewId: {}", reviewId, e);
                }
            }

            // 生成 PDF
            byte[] pdfBytes = pdfReportService.generateReviewReport(
                    contractName,
                    reviewId.longValue(),
                    reviewResult
            );

            log.info("审查报告 PDF 生成成功, reviewId: {}, size: {} bytes", reviewId, pdfBytes.length);
            return pdfBytes;

        } catch (Exception e) {
            log.error("生成审查报告 PDF 失败, reviewId: {}", reviewId, e);
            throw new RuntimeException("生成PDF报告失败: " + e.getMessage(), e);
        }
    }

    /**
     * 从 Redis 缓存获取审查结果，并补充合同名称
     */
    private ReviewResultVO getCachedReviewResult(Integer reviewId) throws Exception {
        String key = ReviewConstant.REVIEW_RESULT_KEY + reviewId;
        String cachedJson = stringRedisTemplate.opsForValue().get(key);
        if (cachedJson == null) {
            return null;
        }
        ReviewResultVO resultVO = objectMapper.readValue(cachedJson, ReviewResultVO.class);
        enrichContractName(resultVO);
        return resultVO;
    }

    /**
     * 补充审查结果中的合同名称
     */
    private void enrichContractName(ReviewResultVO resultVO) {
        if (resultVO.getContractName() == null && resultVO.getContractId() != null) {
            Contract contract = contractMapper.selectById(Long.valueOf(resultVO.getContractId()));
            if (contract != null) {
                resultVO.setContractName(contract.getFileName());
            }
        }
    }

    /**
     * 按风险等级排序风险项列表：high -> medium -> low -> none
     */
    private void sortRisksByLevel(List<com.example.contractreview.model.vo.fastapi.RiskItemVO> risks) {
        if (risks != null && !risks.isEmpty()) {
            risks.sort((r1, r2) -> {
                int priority1 = getRiskLevelPriority(r1.getLevel());
                int priority2 = getRiskLevelPriority(r2.getLevel());
                return Integer.compare(priority1, priority2);
            });
        }
    }

    /**
     * 获取风险等级优先级
     * @param level 风险等级字符串
     * @return 优先级数值（越小优先级越高）
     */
    private int getRiskLevelPriority(String level) {
        if (level == null) {
            return Integer.MAX_VALUE;
        }
        return switch (level.toLowerCase()) {
            case "high" -> 0;
            case "medium" -> 1;
            case "low" -> 2;
            case "none" -> 3;
            default -> Integer.MAX_VALUE;
        };
    }

    /**
     * 根据合同ID获取最新审查记录
     * @param authorization 认证令牌
     * @param contractId 合同ID
     * @return 最新审查记录
     */
    @Override
    public Result<LatestReviewVO> getLatestReviewByContractId(String authorization, Integer contractId) {
        try {
            log.info("获取合同最新审查记录, contractId: {}", contractId);

            // 从token中获取用户ID
            Integer userId = tokenUtils.getUserId(authorization);
            if (userId == null) {
                return Result.error(401, "用户未登录或登录已过期");
            }
            String key = ReviewConstant.REVIEW_RESULT_KEY + contractId;
            String cach = stringRedisTemplate.opsForValue().get(key);
            if (cach != null) {
                return Result.success(objectMapper.readValue(cach, LatestReviewVO.class));
            }

            // 查询最新审查记录
            LatestReviewVO latestReview = reviewMapper.getLatestReviewByContractId(contractId, userId);

            if (latestReview == null) {
                log.info("合同暂无审查记录, contractId: {}", contractId);
                return Result.success(null);
            }

            log.info("获取最新审查记录成功, contractId: {}, reviewId: {}", contractId, latestReview.getReviewId());
            return Result.success(latestReview);

        } catch (Exception e) {
            log.error("获取合同最新审查记录失败, contractId: {}", contractId, e);
            return Result.error(500, "获取审查记录失败: " + e.getMessage());
        }
    }

    /**
     * 获取报告预览数据 - 从 Redis 获取
     * @param authorization 认证令牌
     * @param reviewId 审查ID
     * @return 报告预览数据
     */
    @Override
    public Result<ReportPreviewVO> getReportPreview(String authorization, Integer reviewId) {
        try {
            log.info("获取报告预览数据, reviewId: {}", reviewId);
            ReviewResultVO cachedResult = getCachedReviewResult(reviewId);
            if (cachedResult != null) {
                ReportPreviewVO previewVO = convertToReportPreviewVO(reviewId, cachedResult);
                return Result.success(previewVO);
            }
            Integer userId = tokenUtils.getUserId(authorization);
            if (userId == null) {
                return Result.error(401, "用户未登录或登录已过期");
            }

            String key = ReviewConstant.REVIEW_RESULT_KEY + reviewId;
            String reviewResultJson = stringRedisTemplate.opsForValue().get(key);

            if (reviewResultJson == null || reviewResultJson.isEmpty()) {
                log.warn("Redis 中未找到审查结果, reviewId: {}", reviewId);
                return Result.error(404, "审查结果不存在或已过期");
            }

            ReviewResultVO reviewResult = objectMapper.readValue(reviewResultJson, ReviewResultVO.class);
            enrichContractName(reviewResult);

            ReportPreviewVO previewVO = convertToReportPreviewVO(reviewId, reviewResult);
            return Result.success(previewVO);

        } catch (Exception e) {
            log.error("获取报告预览数据失败, reviewId: {}", reviewId, e);
            return Result.error(500, "获取报告预览数据失败: " + e.getMessage());
        }
    }

    /**
     * 将 ReviewResultVO 转换为 ReportPreviewVO
     */
    private ReportPreviewVO convertToReportPreviewVO(Integer reviewId, ReviewResultVO reviewResult) {
        // 构建风险摘要
        ReportPreviewVO.RiskSummary riskSummary = ReportPreviewVO.RiskSummary.builder()
                .high(reviewResult.getRiskSummary() != null ? reviewResult.getRiskSummary().getOrDefault("high", 0) : 0)
                .medium(reviewResult.getRiskSummary() != null ? reviewResult.getRiskSummary().getOrDefault("medium", 0) : 0)
                .low(reviewResult.getRiskSummary() != null ? reviewResult.getRiskSummary().getOrDefault("low", 0) : 0)
                .none(reviewResult.getRiskSummary() != null ? reviewResult.getRiskSummary().getOrDefault("none", 0) : 0)
                .build();

        // 使用Stream API优化风险列表转换和法条收集（单次遍历）
        Map<String, ReportPreviewVO.LawReferenceVO> lawMap = new HashMap<>();
        List<ReportPreviewVO.RiskPreviewVO> risks = new ArrayList<>();

        if (reviewResult.getRisks() != null) {
            for (com.example.contractreview.model.vo.fastapi.RiskItemVO risk : reviewResult.getRisks()) {
                // 转换法条引用
                List<ReportPreviewVO.LawReferenceVO> lawRefs = new ArrayList<>();
                if (risk.getLawReferences() != null) {
                    for (com.example.contractreview.model.vo.fastapi.LawReferenceVO law : risk.getLawReferences()) {
                        String key = law.getName() + "-" + law.getArticle();
                        ReportPreviewVO.LawReferenceVO lawRef = lawMap.get(key);
                        if (lawRef == null) {
                            lawRef = ReportPreviewVO.LawReferenceVO.builder()
                                    .name(law.getName())
                                    .article(law.getArticle())
                                    .content(law.getContent())
                                    .citationCount(1)
                                    .build();
                            lawMap.put(key, lawRef);
                        } else {
                            lawRef.setCitationCount(lawRef.getCitationCount() + 1);
                        }
                        lawRefs.add(lawRef);
                    }
                }

                risks.add(ReportPreviewVO.RiskPreviewVO.builder()
                        .level(risk.getLevel())
                        .clause(risk.getClause())
                        .description(risk.getDescription())
                        .location(risk.getLocation() != null ? risk.getLocation().getText() : "")
                        .suggestion(risk.getSuggestion())
                        .lawReferences(lawRefs)
                        .build());
            }
        }

        return ReportPreviewVO.builder()
                .title("合同审查报告")
                .reviewId(reviewId)
                .reviewNo(reviewResult.getReviewNo())
                .reviewTime(reviewResult.getCompletedAt() != null ? reviewResult.getCompletedAt() : LocalDateTime.now())
                .reviewAgency("智能合同审查系统")
                .overallScore(reviewResult.getOverallScore() != null ? reviewResult.getOverallScore() : 0)
                .conclusion(reviewResult.getConclusion() != null ? reviewResult.getConclusion() : "经系统审查，本合同存在若干需要关注的风险点，建议根据修改建议进行调整后再签署。")
                .riskSummary(riskSummary)
                .risks(risks)
                .lawReferences(new ArrayList<>(lawMap.values()))
                .build();
    }

    /**
     * 检测高风险并发送SSE通知
     *
     * @param userId     用户ID
     * @param reviewId   审查ID
     * @param reviewResult 审查结果
     */
    private void checkAndNotifyHighRisk(Integer userId, Integer reviewId, ReviewResultVO reviewResult) {
        try {
            // 统计高风险数量
            long highRiskCount = 0;
            if (reviewResult.getRisks() != null) {
                highRiskCount = reviewResult.getRisks().stream()
                        .filter(risk -> "high".equalsIgnoreCase(risk.getLevel()))
                        .count();
            }

            // 如果有高风险，发送SSE通知
            if (highRiskCount > 0) {
                Integer contractId = reviewResult.getContractId();
                String contractName = reviewResult.getContractName();
                if (contractName == null && contractId != null) {
                    Contract contract = contractMapper.selectById(Long.valueOf(contractId));
                    if (contract != null) {
                        contractName = contract.getFileName();
                    }
                }

                if (contractId != null && contractName != null) {
                    int connectionCount = sseEmitterManager.getConnectionCount();
                    log.info("准备发送高风险预警SSE通知, userId: {}, reviewId: {}, 当前在线连接数: {}",
                            userId, reviewId, connectionCount);
                    
                    sseEmitterManager.sendHighRiskWarningNotification(
                            Long.valueOf(userId),
                            Long.valueOf(reviewId),
                            Long.valueOf(contractId),
                            contractName,
                            (int) highRiskCount
                    );
                    log.info("高风险预警SSE通知已发送, userId: {}, reviewId: {}, highRiskCount: {}, 目标用户数: {}",
                            userId, reviewId, highRiskCount, connectionCount);
                }
            }
        } catch (Exception e) {
            log.error("检测高风险并发送通知失败, reviewId: {}", reviewId, e);
        }
    }
}
