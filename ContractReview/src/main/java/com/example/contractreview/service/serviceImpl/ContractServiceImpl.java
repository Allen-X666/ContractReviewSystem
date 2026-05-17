package com.example.contractreview.service.serviceImpl;

import com.example.contractreview.common.Result;
import com.example.contractreview.common.ResultCode;
import com.example.contractreview.constant.ContractConstant;
import com.example.contractreview.mapper.ContractMapper;
import com.example.contractreview.mapper.ReviewMapper;
import com.example.contractreview.model.entity.Contract;
import com.example.contractreview.model.entity.ContractStats;
import com.example.contractreview.model.vo.ContractPreviewVO;
import com.example.contractreview.model.vo.ContractStatsVO;
import com.example.contractreview.model.vo.ContractVOPackage.UploadResultVO;
import com.example.contractreview.model.vo.ContractVO;
import com.example.contractreview.service.ContractService;
import com.example.contractreview.utils.TokenUtils;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.pagehelper.PageHelper;
import com.github.pagehelper.PageInfo;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.io.IOException;
import java.net.MalformedURLException;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.DayOfWeek;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.time.temporal.TemporalAdjusters;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;

@Service
@Slf4j
@RequiredArgsConstructor
public class ContractServiceImpl implements ContractService {

    private final ContractMapper contractMapper;
    private final ReviewMapper reviewMapper;
    private final SystemConfigServiceImpl systemConfigService;
    private final TokenUtils tokenUtils;
    private final StringRedisTemplate stringRedisTemplate;

    @Value("${server.servlet.context-path:}")
    private String contextPath;

    private static final long STATS_CACHE_EXPIRE_HOURS = 1;

    // 上传合同
    @Override
    public Result<UploadResultVO> uploadContract(String authorization, MultipartFile file) {
        if (file == null || file.isEmpty()) {
            log.warn("上传合同文件为空");
            return Result.error(ResultCode.FILE_UPLOAD_ERROR.getCode(), "上传文件不能为空");
        }

        Integer userId = tokenUtils.getUserId(authorization);
        if (userId == null) {
            return Result.error(ResultCode.UNAUTHORIZED.getCode(), "用户认证信息无效");
        }

        String originalFilename = file.getOriginalFilename();
        String fileExtension = getFileExtension(originalFilename);

        if (!isSupportedFileType(fileExtension)) {
            log.warn("不支持的文件类型: {}", fileExtension);
            return Result.error(ResultCode.FILE_TYPE_NOT_SUPPORTED);
        }

        try {
            String uploadPath = systemConfigService.getUploadPath(userId);
            File uploadDir = new File(uploadPath, "contract");

            if (!uploadDir.exists()) {
                boolean created = uploadDir.mkdirs();
                if (!created) {
                    log.error("创建上传目录失败: {}", uploadDir);
                    return Result.error(ResultCode.FILE_UPLOAD_ERROR.getCode(), "创建上传目录失败");
                }
            }

            String savedFileName = generateFileName(fileExtension);
            File destFile = new File(uploadDir, savedFileName);
            file.transferTo(destFile);

            Long fileSize = file.getSize();
            String fileType = fileExtension.toLowerCase();

            Contract contract = Contract.builder()
                    .fileName(originalFilename)
                    .filePath(destFile.getAbsolutePath())
                    .fileSize(fileSize)
                    .fileType(fileType)
                    .userId(userId.longValue())
                    .build();
            log.info("userId: {}, fileName: {}, fileSize: {}, path: {}, fileType:{}", userId, originalFilename, fileSize, destFile.getAbsolutePath(), fileType);
            contractMapper.insert(contract);

            UploadResultVO resultVO = UploadResultVO.builder()
                    .contractId(contract.getId())
                    .fileName(originalFilename)
                    .fileSize(fileSize)
                    .fileType(fileType)
                    .uploadTime(LocalDateTime.now())
                    .build();

            // 删除用户合同统计缓存
            clearContractStatsCache(userId);

            return Result.success(resultVO);

        } catch (IOException e) {
            log.error("合同文件保存失败, fileName: {}, error: {}", originalFilename, e.getMessage(), e);
            return Result.error(ResultCode.FILE_UPLOAD_ERROR.getCode(), "文件保存失败，请稍后重试");
        } catch (Exception e) {
            log.error("合同上传失败, fileName: {}, error: {}", originalFilename, e.getMessage(), e);
            return Result.error(ResultCode.FILE_UPLOAD_ERROR.getCode(), "合同上传失败，请稍后重试");
        }
    }

    // 批量上传合同
    @Override
    public Result<List<UploadResultVO>> batchUploadContracts(String authorization, List<MultipartFile> files) {
        if (files == null || files.isEmpty()) {
            return Result.error(ResultCode.FILE_UPLOAD_ERROR.getCode(), "上传文件列表不能为空");
        }

        Integer userId = tokenUtils.getUserId(authorization);
        if (userId == null) {
            return Result.error(ResultCode.UNAUTHORIZED.getCode(), "用户认证信息无效");
        }

        List<UploadResultVO> results = new ArrayList<>();
        int successCount = 0;
        int failCount = 0;

        for (MultipartFile file : files) {
            try {
                Result<UploadResultVO> result = uploadContract(authorization, file);
                if (result.isSuccess()) {
                    results.add(result.getData());
                    successCount++;
                } else {
                    failCount++;
                    log.warn("批量上传中文件上传失败, fileName: {}, message: {}", 
                            file.getOriginalFilename(), result.getMessage());
                }
            } catch (Exception e) {
                failCount++;
                log.error("批量上传中文件处理异常, fileName: {}, error: {}", 
                        file.getOriginalFilename(), e.getMessage(), e);
            }
        }

        log.info("批量上传完成, 成功: {}, 失败: {}, 总计: {}", successCount, failCount, files.size());
        return Result.success(results);
    }

    // 获取合同列表
    @Override
    public Result<List<ContractVO>> getContractList(String authorization, Integer page, Integer pageSize, String keyword) {
        Integer userId = tokenUtils.getUserId(authorization);
        if (userId == null) {
            return Result.error(ResultCode.UNAUTHORIZED.getCode(), "用户认证信息无效");
        }

        PageHelper.startPage(page != null ? page : 1, pageSize != null ? pageSize : 10);
        List<Contract> contracts = contractMapper.selectByUserId(userId.longValue(), keyword);
        PageInfo<Contract> pageInfo = new PageInfo<>(contracts);

        List<Integer> contractIds = contracts.stream()
                .map(Contract::getId)
                .collect(Collectors.toList());

        Map<Integer, Integer> reviewIdMap = new HashMap<>();
        Map<Integer, String> reviewNoMap = new HashMap<>();
        if (!contractIds.isEmpty()) {
            List<Map<String, Object>> reviewRows = reviewMapper.getLatestReviewIdsByContractIds(contractIds, userId);
            for (Map<String, Object> row : reviewRows) {
                Integer cid = ((Number) row.get("contractId")).intValue();
                Integer rid = ((Number) row.get("reviewNo")).intValue();
                // reviewNo 可能是 Long 或 String 类型
                Object reviewNoObj = row.get("reviewNo");
                String rno = reviewNoObj != null ? reviewNoObj.toString() : null;
                reviewIdMap.put(cid, rid);
                reviewNoMap.put(cid, rno);
            }
        }

        List<ContractVO> voList = contracts.stream()
                .map(contract -> {
                    ContractVO vo = convertToVO(contract);
                    vo.setLastReviewId(reviewIdMap.get(contract.getId()));
                    vo.setLastReviewNo(reviewNoMap.get(contract.getId()));
                    return vo;
                })
                .collect(Collectors.toList());

        return Result.success(voList, pageInfo.getTotal());
    }

    // 删除合同
    @Override
    public Result<String> deleteContract(String authorization, Long contractId) {
        Integer userId = tokenUtils.getUserId(authorization);
        Result<Contract> validateResult = validateContractAccess(authorization, contractId, "删除");
        if (!validateResult.isSuccess()) {
            return Result.error(validateResult.getCode(), validateResult.getMessage());
        }

        Contract contract = validateResult.getData();

        // 删除文件
        if (contract.getFilePath() != null && !contract.getFilePath().isEmpty()) {
            try {
                File file = new File(contract.getFilePath());
                if (file.exists()) {
                    boolean deleted = file.delete();
                    if (deleted) {
                        log.info("合同文件删除成功, contractId: {}, filePath: {}", contractId, contract.getFilePath());
                    } else {
                        log.warn("合同文件删除失败, contractId: {}, filePath: {}", contractId, contract.getFilePath());
                    }
                } else {
                    log.warn("合同文件不存在, contractId: {}, filePath: {}", contractId, contract.getFilePath());
                }
            } catch (Exception e) {
                log.error("删除合同文件时发生异常, contractId: {}, filePath: {}, error: {}",
                        contractId, contract.getFilePath(), e.getMessage(), e);
            }
        }
        clearContractStatsCache(userId);
        contractMapper.deleteById(contractId);
        return Result.success("删除成功");
    }

    // 批量删除合同
    @Override
    public Result<String> batchDeleteContracts(String authorization, List<Long> contractIds) {
        if (contractIds == null || contractIds.isEmpty()) {
            return Result.error(ResultCode.PARAM_ERROR.getCode(), "合同ID列表不能为空");
        }

        Integer userId = tokenUtils.getUserId(authorization);
        if (userId == null) {
            return Result.error(ResultCode.UNAUTHORIZED.getCode(), "用户认证信息无效");
        }

        int successCount = 0;
        int failCount = 0;

        for (Long contractId : contractIds) {
            try {
                Result<String> result = deleteContract(authorization, contractId);
                if (result.isSuccess()) {
                    successCount++;
                } else {
                    failCount++;
                    log.warn("批量删除中合同删除失败, contractId: {}, message: {}", contractId, result.getMessage());
                }
            } catch (Exception e) {
                failCount++;
                log.error("批量删除中合同处理异常, contractId: {}, error: {}", contractId, e.getMessage(), e);
            }
        }
        return Result.success(String.format("批量删除完成，成功: %d, 失败: %d", successCount, failCount));
    }

    /**
     * 验证用户对合同的访问权限
     */
    private Result<Contract> validateContractAccess(String authorization, Long contractId, String operation) {
        Integer userId = tokenUtils.getUserId(authorization);
        if (userId == null) {
            return Result.error(ResultCode.UNAUTHORIZED.getCode(), "用户认证信息无效");
        }

        Contract contract = contractMapper.selectById(contractId);
        if (contract == null) {
            return Result.error(ResultCode.CONTRACT_NOT_FOUND);
        }

        if (!contract.getUserId().equals(userId.longValue())) {
            log.warn("无权{}该合同, userId: {}, contractId: {}", operation, userId, contractId);
            return Result.error(ResultCode.UNAUTHORIZED.getCode(), "无权操作该合同");
        }

        return Result.success(contract);
    }

    private ContractVO convertToVO(Contract contract) {
        return ContractVO.builder()
                .id(contract.getId())
                .fileName(contract.getFileName())
                .fileSize(contract.getFileSize())
                .fileType(contract.getFileType())
                .reviewStatus(cleanQuotes(contract.getReviewStatus()))
                .riskLevel(cleanQuotes(contract.getRiskLevel()))
                .reviewScore(contract.getReviewScore())
                .createdAt(contract.getCreatedAt())
                .build();
    }

    private String cleanQuotes(String value) {
        if (value == null) {
            return null;
        }
        return value.replace("\"", "").replace("\"", "").replace("\"", "").trim();
    }

    private String generateFileName(String extension) {
        return UUID.randomUUID().toString().replace("-", "") + "." + extension;
    }

    private String getFileExtension(String filename) {
        if (filename == null || !filename.contains(".")) {
            return "";
        }
        return filename.substring(filename.lastIndexOf(".") + 1).toLowerCase();
    }

    private boolean isSupportedFileType(String extension) {
        return "pdf".equals(extension) || "docx".equals(extension);
    }

    // 获取合同统计信息
    @Override
    public Result<ContractStatsVO> getContractStats(String authorization) {
        Integer userId = tokenUtils.getUserId(authorization);
        String cacheKey = ContractConstant.CONTRACT_STATS_KEY_PREFIX + userId;
        try {
            String cachedStats = stringRedisTemplate.opsForValue().get(cacheKey);
            if (cachedStats != null) {
                ContractStatsVO statsVO = new ObjectMapper().readValue(cachedStats, ContractStatsVO.class);
                return Result.success(statsVO);
            }
        } catch (Exception e) {
            log.warn("从Redis读取统计数据失败, userId: {}, error: {}", userId, e.getMessage());
        }

        ContractStats stats = contractMapper.selectStatsByUserId(userId.longValue());

        // 计算本周和上周的时间范围
        LocalDate now = LocalDate.now();
        LocalDate thisWeekStart = now.with(TemporalAdjusters.previousOrSame(DayOfWeek.MONDAY));
        LocalDate thisWeekEnd = thisWeekStart.plusDays(7);
        LocalDate lastWeekStart = thisWeekStart.minusDays(7);

        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
        String thisWeekStartStr = thisWeekStart.atStartOfDay().format(formatter);
        String thisWeekEndStr = thisWeekEnd.atStartOfDay().format(formatter);
        String lastWeekStartStr = lastWeekStart.atStartOfDay().format(formatter);
        String lastWeekEndStr = thisWeekStart.atStartOfDay().format(formatter);

        // 查询本周和上周的各类统计数据
        ContractStats thisWeekStats = contractMapper.selectStatsByUserIdAndTimeRange(
                userId.longValue(), thisWeekStartStr, thisWeekEndStr);
        ContractStats lastWeekStats = contractMapper.selectStatsByUserIdAndTimeRange(
                userId.longValue(), lastWeekStartStr, lastWeekEndStr);

        // 查询本周和上周的合同数量
        Long thisWeekCount = contractMapper.selectCountByUserIdAndTimeRange(
                userId.longValue(), thisWeekStartStr, thisWeekEndStr);
        Long lastWeekCount = contractMapper.selectCountByUserIdAndTimeRange(
                userId.longValue(), lastWeekStartStr, lastWeekEndStr);

        // 计算周增长率
        Double weekGrowthRate = calculateGrowthRate(thisWeekCount, lastWeekCount);

        // 计算各项数据的趋势（本周vs上周）
        Integer totalTrend = calculateTrend(thisWeekCount, lastWeekCount);
        Integer pendingTrend = calculateTrend(
                thisWeekStats != null && thisWeekStats.getPending() != null ? thisWeekStats.getPending() : 0L,
                lastWeekStats != null && lastWeekStats.getPending() != null ? lastWeekStats.getPending() : 0L);
        Integer completedTrend = calculateTrend(
                thisWeekStats != null && thisWeekStats.getCompleted() != null ? thisWeekStats.getCompleted() : 0L,
                lastWeekStats != null && lastWeekStats.getCompleted() != null ? lastWeekStats.getCompleted() : 0L);
        Integer highRiskTrend = calculateTrend(
                thisWeekStats != null && thisWeekStats.getHighRisk() != null ? thisWeekStats.getHighRisk() : 0L,
                lastWeekStats != null && lastWeekStats.getHighRisk() != null ? lastWeekStats.getHighRisk() : 0L);
        Integer mediumRiskTrend = calculateTrend(
                thisWeekStats != null && thisWeekStats.getMediumRisk() != null ? thisWeekStats.getMediumRisk() : 0L,
                lastWeekStats != null && lastWeekStats.getMediumRisk() != null ? lastWeekStats.getMediumRisk() : 0L);
        Integer lowRiskTrend = calculateTrend(
                thisWeekStats != null && thisWeekStats.getLowRisk() != null ? thisWeekStats.getLowRisk() : 0L,
                lastWeekStats != null && lastWeekStats.getLowRisk() != null ? lastWeekStats.getLowRisk() : 0L);
        Integer noRiskTrend = calculateTrend(
                thisWeekStats != null && thisWeekStats.getNoRisk() != null ? thisWeekStats.getNoRisk() : 0L,
                lastWeekStats != null && lastWeekStats.getNoRisk() != null ? lastWeekStats.getNoRisk() : 0L);
        Integer avgScoreTrend = calculateTrend(
                thisWeekStats != null && thisWeekStats.getAvgScore() != null ? thisWeekStats.getAvgScore() : 0,
                lastWeekStats != null && lastWeekStats.getAvgScore() != null ? lastWeekStats.getAvgScore() : 0);
        Integer maxScoreTrend = calculateTrend(
                thisWeekStats != null && thisWeekStats.getMaxScore() != null ? thisWeekStats.getMaxScore() : 0,
                lastWeekStats != null && lastWeekStats.getMaxScore() != null ? lastWeekStats.getMaxScore() : 0);
        Integer minScoreTrend = calculateTrend(
                thisWeekStats != null && thisWeekStats.getMinScore() != null ? thisWeekStats.getMinScore() : 0,
                lastWeekStats != null && lastWeekStats.getMinScore() != null ? lastWeekStats.getMinScore() : 0);

        ContractStatsVO statsVO = ContractStatsVO.builder()
                .total(stats != null && stats.getTotal() != null ? stats.getTotal() : 0L)
                .pending(stats != null && stats.getPending() != null ? stats.getPending() : 0L)
                .completed(stats != null && stats.getCompleted() != null ? stats.getCompleted() : 0L)
                .highRisk(stats != null && stats.getHighRisk() != null ? stats.getHighRisk() : 0L)
                .mediumRisk(stats != null && stats.getMediumRisk() != null ? stats.getMediumRisk() : 0L)
                .lowRisk(stats != null && stats.getLowRisk() != null ? stats.getLowRisk() : 0L)
                .noRisk(stats != null && stats.getNoRisk() != null ? stats.getNoRisk() : 0L)
                .avgScore(stats != null && stats.getAvgScore() != null ? stats.getAvgScore() : 0)
                .maxScore(stats != null && stats.getMaxScore() != null ? stats.getMaxScore() : 0)
                .minScore(stats != null && stats.getMinScore() != null ? stats.getMinScore() : 0)
                .thisWeekCount(thisWeekCount != null ? thisWeekCount : 0L)
                .lastWeekCount(lastWeekCount != null ? lastWeekCount : 0L)
                .weekGrowthRate(weekGrowthRate)
                .totalTrend(totalTrend)
                .pendingTrend(pendingTrend)
                .completedTrend(completedTrend)
                .highRiskTrend(highRiskTrend)
                .mediumRiskTrend(mediumRiskTrend)
                .lowRiskTrend(lowRiskTrend)
                .noRiskTrend(noRiskTrend)
                .avgScoreTrend(avgScoreTrend)
                .maxScoreTrend(maxScoreTrend)
                .minScoreTrend(minScoreTrend)
                .build();
        try {
            String statsJson = new ObjectMapper().writeValueAsString(statsVO);
            stringRedisTemplate.opsForValue().set(cacheKey, statsJson, STATS_CACHE_EXPIRE_HOURS, TimeUnit.HOURS);
        } catch (Exception e) {
            log.warn("缓存统计数据到Redis失败, userId: {}, error: {}", userId, e.getMessage());
        }
        return Result.success(statsVO);
    }

    // 获取合同统计数据
    @Override
    public Result<ContractPreviewVO> getContractPreview(String authorization, Long contractId) {
        Result<Contract> validateResult = validateContractAccess(authorization, contractId, "查看");
        if (!validateResult.isSuccess()) {
            return Result.error(validateResult.getCode(), validateResult.getMessage());
        }

        Contract contract = validateResult.getData();

        String fileUrl = contextPath + "/contract/file/" + contractId;

        ContractPreviewVO previewVO = ContractPreviewVO.builder()
                .contractId(contract.getId())
                .fileName(contract.getFileName())
                .fileType(contract.getFileType())
                .fileUrl(fileUrl)
                .fileSize(contract.getFileSize())
                .created_at(contract.getCreatedAt())
                .build();

        log.info("获取合同预览信息成功, contractId: {}, fileName: {}", contractId, contract.getFileName());
        return Result.success(previewVO, 1L);
    }

    /**
     * 获取合同文件
     */
    @Override
    public ResponseEntity<Resource> getContractFile(String authorization, Long contractId, HttpServletRequest request) {
        Integer userId = tokenUtils.getUserId(authorization);
        if (userId == null) {
            log.warn("无法获取用户ID");
            return ResponseEntity.status(401).build();
        }

        Contract contract = contractMapper.selectById(contractId);
        if (contract == null) {
            log.warn("合同不存在, contractId: {}", contractId);
            return ResponseEntity.notFound().build();
        }

        if (!contract.getUserId().equals(userId.longValue())) {
            log.warn("无权访问该合同, userId: {}, contractId: {}", userId, contractId);
            return ResponseEntity.status(403).build();
        }

        Path path = Paths.get(contract.getFilePath());
        Resource resource;
        try {
            resource = new UrlResource(path.toUri());
        } catch (MalformedURLException e) {
            log.error("文件路径无效, contractId: {}, path: {}", contractId, contract.getFilePath(), e);
            return ResponseEntity.notFound().build();
        }

        if (!resource.exists() || !resource.isReadable()) {
            log.error("文件不存在或无法读取, contractId: {}, path: {}", contractId, contract.getFilePath());
            return ResponseEntity.notFound().build();
        }

        String contentType = determineContentType(contract.getFileType());
        String encodedFileName = URLEncoder.encode(contract.getFileName(), StandardCharsets.UTF_8)
                .replace("+", "%20");

        return ResponseEntity.ok()
                .contentType(MediaType.parseMediaType(contentType))
                .header(HttpHeaders.CONTENT_DISPOSITION, "inline; filename*=UTF-8''" + encodedFileName)
                .body(resource);
    }

    // 下载合同文件
    @Override
    public ResponseEntity<Resource> downloadContractFile(String authorization, Long contractId, HttpServletRequest request) {
        Integer userId = tokenUtils.getUserId(authorization);
        if (userId == null) {
            return ResponseEntity.status(401).build();
        }

        Contract contract = contractMapper.selectById(contractId);
        if (contract == null) {
            return ResponseEntity.notFound().build();
        }

        if (!contract.getUserId().equals(userId.longValue())) {
            return ResponseEntity.status(403).build();
        }

        String filePath = contract.getFilePath();
        if (filePath == null || filePath.isEmpty()) {
            log.error("合同文件路径为空, contractId: {}", contractId);
            return ResponseEntity.notFound().build();
        }

        String fileName = contract.getFileName();
        if (fileName == null || fileName.isEmpty()) {
            fileName = Paths.get(filePath).getFileName().toString();
        }

        Path path = Paths.get(filePath);
        Resource resource;
        try {
            resource = new UrlResource(path.toUri());
        } catch (MalformedURLException e) {
            log.error("文件路径无效, contractId: {}, path: {}", contractId, filePath, e);
            return ResponseEntity.notFound().build();
        }

        if (!resource.exists() || !resource.isReadable()) {
            log.error("文件不存在或无法读取, contractId: {}, path: {}", contractId, filePath);
            return ResponseEntity.notFound().build();
        }

        String contentType = determineContentType(getFileExtension(fileName));
        String encodedFileName = URLEncoder.encode(fileName, StandardCharsets.UTF_8)
                .replace("+", "%20");

        return ResponseEntity.ok()
                .contentType(MediaType.parseMediaType(contentType))
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename*=UTF-8''" + encodedFileName)
                .body(resource);
    }

    private String determineContentType(String fileType) {
        if (fileType == null) {
            return MediaType.APPLICATION_OCTET_STREAM_VALUE;
        }
        return switch (fileType.toLowerCase()) {
            case "pdf" -> MediaType.APPLICATION_PDF_VALUE;
            case "docx" -> "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
            case "doc" -> "application/msword";
            default -> MediaType.APPLICATION_OCTET_STREAM_VALUE;
        };
    }

    /**
     * 计算增长率
     */
    private Double calculateGrowthRate(Long current, Long last) {
        if (last == null || last == 0) {
            return current != null && current > 0 ? 100.0 : 0.0;
        }
        if (current == null) {
            current = 0L;
        }
        return ((current - last) * 100.0) / last;
    }

    /**
     * 计算趋势（整数百分比）
     *
     * @param current 当前值
     * @param last    上周值
     * @return 趋势值（整数百分比，如 10 表示增长 10%，-5 表示下降 5%）
     */
    private Integer calculateTrend(Long current, Long last) {
        if (last == null || last == 0) {
            return current != null && current > 0 ? 100 : 0;
        }
        if (current == null) {
            current = 0L;
        }
        return (int) Math.round(((current - last) * 100.0) / last);
    }

    /**
     * 计算趋势（整数百分比）- 重载方法用于Integer类型
     *
     * @param current 当前值
     * @param last    上周值
     * @return 趋势值（整数百分比）
     */
    private Integer calculateTrend(Integer current, Integer last) {
        if (last == null || last == 0) {
            return current != null && current > 0 ? 100 : 0;
        }
        if (current == null) {
            current = 0;
        }
        return (int) Math.round(((current - last) * 100.0) / last);
    }

    /**
     * 清除用户合同统计缓存
     *
     * @param userId 用户ID
     */
    private void clearContractStatsCache(Integer userId) {
        try {
            String cacheKey = ContractConstant.CONTRACT_STATS_KEY_PREFIX + userId;
            stringRedisTemplate.delete(cacheKey);
            log.debug("清除用户合同统计缓存成功, userId: {}", userId);
        } catch (Exception e) {
            log.warn("清除用户合同统计缓存失败, userId: {}, error: {}", userId, e.getMessage());
        }
    }
}
