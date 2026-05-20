package com.example.contractreview.client;

import com.example.contractreview.config.FastApiConfig;
import com.example.contractreview.model.dto.StartReviewDTO;
import com.example.contractreview.model.vo.fastapi.FastApiResult;
import com.example.contractreview.model.vo.fastapi.ReviewProgressVO;
import com.example.contractreview.model.vo.fastapi.ReviewResultVO;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.Getter;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.core.io.FileSystemResource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.ResourceAccessException;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.net.SocketTimeoutException;
import java.util.Map;

@Slf4j
@Component
public class FastApiClient {

    private final RestClient restClient;
    @Getter
    private final FastApiConfig fastApiConfig;
    @Getter
    private final ObjectMapper objectMapper;

    public FastApiClient(FastApiConfig fastApiConfig, ObjectMapper objectMapper) {
        this.fastApiConfig = fastApiConfig;
        this.objectMapper = objectMapper;

        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(fastApiConfig.getConnectTimeout());
        factory.setReadTimeout(fastApiConfig.getTimeout());

        this.restClient = RestClient.builder()
                .requestFactory(factory)
                .baseUrl(fastApiConfig.getFullApiUrl())
                .defaultHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
                .defaultHeader(HttpHeaders.ACCEPT, MediaType.APPLICATION_JSON_VALUE)
                .build();
    }

    /**
     * 处理FastAPI调用异常，区分超时场景返回友好提示
     */
    private RuntimeException handleFastApiException(Exception e, String operation) {
        // 判断是否为超时异常
        if (e instanceof ResourceAccessException) {
            Throwable cause = e.getCause();
            if (cause instanceof SocketTimeoutException) {
                log.error("FastAPI {} 超时: {}", operation, e.getMessage());
                return new RuntimeException("AI 服务繁忙，请稍后重试");
            }
        }
        // 检查异常消息中是否包含超时关键词
        String message = e.getMessage();
        if (message != null && (message.contains("timeout") || message.contains("timed out") || message.contains("Read timed out"))) {
            log.error("FastAPI {} 超时: {}", operation, message);
            return new RuntimeException("AI 服务繁忙，请稍后重试");
        }
        log.error("调用 FastAPI {} 失败: {}", operation, message, e);
        return new RuntimeException("AI 服务调用失败: " + message);
    }

    /**
     * 发起合同审查
     */
    public FastApiResult<Map<String, Object>> startReview(StartReviewDTO dto, String authorization) {
        try {
            log.info("调用 FastAPI 发起审查, contractId: {}", dto.getContractId());

            MultiValueMap<String, Object> parts = new LinkedMultiValueMap<>();
            parts.add("contract_id", dto.getContractId());

            if (dto.getFile() != null && !dto.getFile().isEmpty()) {
                parts.add("file", dto.getFile().getResource());
            }

            if (dto.getReviewOptions() != null) {
                String reviewOptionsJson = objectMapper.writeValueAsString(dto.getReviewOptions());
                parts.add("review_options", reviewOptionsJson);
            }

            return restClient.post()
                    .uri("/review/start")
                    .header(HttpHeaders.AUTHORIZATION, authorization)
                    .contentType(MediaType.MULTIPART_FORM_DATA)
                    .body(parts)
                    .retrieve()
                    .body(new org.springframework.core.ParameterizedTypeReference<FastApiResult<Map<String, Object>>>() {});
        } catch (RestClientException e) {
            throw handleFastApiException(e, "发起审查");
        } catch (Exception e) {
            log.error("序列化审查选项失败: {}", e.getMessage(), e);
            throw new RuntimeException("请求参数处理失败: " + e.getMessage());
        }
    }

    /**
     * 获取审查进度
     */
    public FastApiResult<ReviewProgressVO> getReviewProgress(Integer reviewId, String authorization) {
        try {
            log.info("调用 FastAPI 获取审查进度, reviewId: {}", reviewId);

            return restClient.get()
                    .uri("/review/{reviewId}/progress", reviewId)
                    .header(HttpHeaders.AUTHORIZATION, authorization)
                    .retrieve()
                    .body(new org.springframework.core.ParameterizedTypeReference<FastApiResult<ReviewProgressVO>>() {});
        } catch (RestClientException e) {
            log.error("调用 FastAPI 获取审查进度失败: {}", e.getMessage(), e);
            throw new RuntimeException("AI 服务调用失败: " + e.getMessage());
        }
    }

    /**
     * 获取审查结果
     */
    public FastApiResult<ReviewResultVO> getReviewResult(Integer reviewId, String authorization) {
        try {
            return restClient.get()
                    .uri("/review/{reviewId}/result", reviewId)
                    .header(HttpHeaders.AUTHORIZATION, authorization)
                    .retrieve()
                    .body(new org.springframework.core.ParameterizedTypeReference<FastApiResult<ReviewResultVO>>() {});
        } catch (RestClientException e) {
            log.error("调用 FastAPI 获取审查结果失败: {}", e.getMessage(), e);
            throw new RuntimeException("AI 服务调用失败: " + e.getMessage());
        }
    }

    /**
     * 取消审查任务
     */
    public FastApiResult<Map<String, Object>> cancelReview(Integer reviewId, String authorization) {
        try {
            log.info("调用 FastAPI 取消审查, reviewId: {}", reviewId);

            return restClient.post()
                    .uri("/review/{reviewId}/cancel", reviewId)
                    .header(HttpHeaders.AUTHORIZATION, authorization)
                    .retrieve()
                    .body(new org.springframework.core.ParameterizedTypeReference<FastApiResult<Map<String, Object>>>() {});
        } catch (RestClientException e) {
            log.error("调用 FastAPI 取消审查失败: {}", e.getMessage(), e);
            throw new RuntimeException("AI 服务调用失败: " + e.getMessage());
        }
    }

    /**
     * 重新审查
     */
    public FastApiResult<Map<String, Object>> reReview(Integer reviewId, String authorization) {
        try {
            log.info("调用 FastAPI 重新审查, reviewId: {}", reviewId);

            return restClient.post()
                    .uri("/review/{reviewId}/re-review", reviewId)
                    .header(HttpHeaders.AUTHORIZATION, authorization)
                    .retrieve()
                    .body(new org.springframework.core.ParameterizedTypeReference<FastApiResult<Map<String, Object>>>() {});
        } catch (RestClientException e) {
            log.error("调用 FastAPI 重新审查失败: {}", e.getMessage(), e);
            throw new RuntimeException("AI 服务调用失败: " + e.getMessage());
        }
    }

    /**
     * 上传法律文档到FastAPI
     * @param file 文件
     * @param documentType 文档类型
     * @param effectiveDate 生效日期
     * @param description 文档说明
     * @param authorization 认证令牌
     * @return FastAPI返回结果
     */
    public FastApiResult<Map<String, Object>> uploadLawDocument(MultipartFile file, String documentType, String effectiveDate, String description, String authorization) {
        try {
            log.info("调用 FastAPI 上传法律文档, documentType: {}", documentType);

            MultiValueMap<String, Object> parts = new LinkedMultiValueMap<>();
            parts.add("file", file.getResource());
            parts.add("document_type", documentType);
            if (effectiveDate != null) {
                parts.add("effective_date", effectiveDate);
            }
            if (description != null) {
                parts.add("description", description);
            }

            return restClient.post()
                    .uri("/laws/upload")
                    .header(HttpHeaders.AUTHORIZATION, authorization)
                    .contentType(MediaType.MULTIPART_FORM_DATA)
                    .body(parts)
                    .retrieve()
                    .body(new org.springframework.core.ParameterizedTypeReference<FastApiResult<Map<String, Object>>>() {});
        } catch (RestClientException e) {
            log.error("调用 FastAPI 上传法律文档失败: {}", e.getMessage(), e);
            throw new RuntimeException("AI 服务调用失败: " + e.getMessage());
        }
    }

    /**
     * 上传系统文档到FastAPI
     * @param category 文档分类
     * @param tags 文档标签
     * @param description 文档说明
     * @param authorization 认证令牌
     */
    public void uploadSystemDocument(MultipartFile file, String category, String tags, String description, String authorization) {
        try {
            // 处理可能为null的参数，使用空字符串作为默认值
            String safeCategory = category != null ? category : "";
            String safeTags = tags != null ? tags : "[]";
            String safeDescription = description != null ? description : "";

            MultiValueMap<String, Object> parts = new LinkedMultiValueMap<>();
            parts.add("file", file.getResource());
            parts.add("category", safeCategory);
            parts.add("tags", safeTags);
            parts.add("description", safeDescription);
            restClient.post()
                    .uri("/system-docs/upload")
                    .header(HttpHeaders.AUTHORIZATION, authorization)
                    .contentType(MediaType.MULTIPART_FORM_DATA)
                    .body(parts)
                    .retrieve()
                    .body(new org.springframework.core.ParameterizedTypeReference<Void>() {});
        } catch (RestClientException e) {
            log.error("调用 FastAPI 上传系统文档失败: {}", e.getMessage(), e);
            throw new RuntimeException("AI 服务调用失败: " + e.getMessage());
        }
    }

    /**
     * 上传系统文档到FastAPI（通过文件路径）
     * @param filePath 文件路径
     * @param category 文档分类
     * @param tags 文档标签
     * @param description 文档说明
     * @param authorization 认证令牌
     */
    public void uploadSystemDocumentByPath(String filePath, String category, String tags, String description, String authorization) {
        try {
            File file = new File(filePath);
            if (!file.exists()) {
                throw new RuntimeException("文件不存在: " + filePath);
            }

            // 处理可能为null的参数，使用空字符串作为默认值
            String safeCategory = category != null ? category : "";
            String safeTags = tags != null ? tags : "[]";
            String safeDescription = description != null ? description : "";

            MultiValueMap<String, Object> parts = new LinkedMultiValueMap<>();
            parts.add("file", new FileSystemResource(file));
            parts.add("category", safeCategory);
            parts.add("tags", safeTags);
            parts.add("description", safeDescription);
            restClient.post()
                    .uri("/system-docs/upload")
                    .header(HttpHeaders.AUTHORIZATION, authorization)
                    .contentType(MediaType.MULTIPART_FORM_DATA)
                    .body(parts)
                    .retrieve()
                    .body(new org.springframework.core.ParameterizedTypeReference<Void>() {});
            log.info("FastAPI上传系统文档成功, filePath: {}", filePath);
        } catch (RestClientException e) {
            log.error("调用 FastAPI 上传系统文档失败: {}, filePath: {}", e.getMessage(), filePath, e);
            throw new RuntimeException("AI 服务调用失败: " + e.getMessage());
        }
    }
}
