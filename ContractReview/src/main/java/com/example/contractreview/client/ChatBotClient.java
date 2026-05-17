package com.example.contractreview.client;

import com.example.contractreview.component.StreamingResponseCollector;
import com.example.contractreview.config.FastApiConfig;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.util.function.Consumer;

@Slf4j
@Component
public class ChatBotClient {

    private final RestClient restClient;
    private final RestClient streamingRestClient;
    private final FastApiConfig fastApiConfig;
    private final ObjectMapper objectMapper;

    public ChatBotClient(FastApiConfig fastApiConfig, ObjectMapper objectMapper) {
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

        SimpleClientHttpRequestFactory streamingFactory = new SimpleClientHttpRequestFactory();
        streamingFactory.setConnectTimeout(fastApiConfig.getConnectTimeout());
        streamingFactory.setReadTimeout(0);

        this.streamingRestClient = RestClient.builder()
                .requestFactory(streamingFactory)
                .baseUrl(fastApiConfig.getFullApiUrl())
                .defaultHeader(HttpHeaders.CONTENT_TYPE, MediaType.TEXT_PLAIN_VALUE)
                .defaultHeader(HttpHeaders.ACCEPT, MediaType.TEXT_EVENT_STREAM_VALUE)
                .build();
    }

    public String sendMessage(String content, String authorization) {
        try {
            log.info("调用 FastAPI 发送消息, content: {}", content);
            return restClient.post()
                    .uri("/chatbot/messages")
                    .header(HttpHeaders.AUTHORIZATION, authorization)
                    .contentType(MediaType.TEXT_PLAIN)
                    .header(HttpHeaders.CONTENT_ENCODING, "UTF-8")
                    .body(content.getBytes(StandardCharsets.UTF_8))
                    .retrieve()
                    .body(String.class);
        } catch (RestClientException e) {
            log.error("调用 FastAPI 发送消息失败: {}", e.getMessage(), e);
            throw new RuntimeException("AI 服务调用失败: " + e.getMessage());
        }
    }

    /**
     * 流式发送消息（带回调版本）
     * @param content 用户消息
     * @param conversationId 对话ID（用于关联 Redis Checkpointer 中的对话状态）
     * @param outputStream 输出流（给前端）
     * @param onComplete 完成回调，接收完整 AI 回复
     * @param authorization 认证令牌
     */
    public void streamMessageWithCallback(String content, Long conversationId, OutputStream outputStream, Consumer<String> onComplete, String authorization) {
        if (content == null || content.trim().isEmpty()) {
            log.warn("消息内容为空，跳过调用");
            return;
        }
        
        StreamingResponseCollector collector = new StreamingResponseCollector();
        StringBuilder rawResponse = new StringBuilder();

        String uri = "/chatbot/messages";
        if (conversationId != null) {
            uri += "?conversationId=" + conversationId;
        }
        
        try (InputStream responseStream = streamingRestClient.post()
                .uri(uri)
                .header(HttpHeaders.AUTHORIZATION, authorization)
                .contentType(MediaType.TEXT_PLAIN)
                .header(HttpHeaders.CONTENT_ENCODING, "UTF-8")
                .body(content.getBytes(StandardCharsets.UTF_8))
                .retrieve()
                .body(InputStream.class)) {
            
            if (responseStream == null) {
                log.error("FastAPI 返回空响应流");
                writeSseError(outputStream, "AI 服务返回空响应");
                return;
            }
            
            BufferedReader reader = new BufferedReader(
                    new InputStreamReader(responseStream, StandardCharsets.UTF_8));
            String line;
            boolean hasReceivedData = false;
            
            while ((line = reader.readLine()) != null) {
                log.debug("收到 SSE 行: {}", line);
                rawResponse.append(line).append("\n");
                
                // 检查是否是有效数据行
                if (line.startsWith("data: ")) {
                    hasReceivedData = true;
                }
                
                try {
                    // 写入前端
                    outputStream.write((line + "\n").getBytes(StandardCharsets.UTF_8));
                    outputStream.flush();
                } catch (Exception writeEx) {
                    // 前端连接可能已断开，但继续收集完整响应
                    log.warn("写入前端响应失败（可能连接已断开）: {}", writeEx.getMessage());
                }

                // 使用收集器收集完整回复
                collector.processLine(line);
            }
            
            try {
                outputStream.flush();
            } catch (Exception flushEx) {
                log.warn("刷新输出流失败: {}", flushEx.getMessage());
            }

            String fullContent = collector.getFullContent();
            log.info("流式响应收集完成，是否收到数据: {}, 原始响应长度: {}, 解析内容长度: {}", 
                    hasReceivedData, rawResponse.length(), fullContent.length());
            
            if (!hasReceivedData) {
                log.warn("未收到任何有效 SSE 数据，原始响应: {}", rawResponse.toString());
            }
            
            // 调用完成回调 - 即使前端连接断开也要保存
            if (onComplete != null) {
                onComplete.accept(fullContent);
            }
            
        } catch (Exception e) {
            log.error("流式调用 FastAPI 失败: {}", e.getMessage(), e);
            log.error("已收集的原始响应: {}", rawResponse.toString());
            
            // 尝试保存已收集的内容
            String partialContent = collector.getFullContent();
            if (!partialContent.isEmpty() && onComplete != null) {
                log.info("尝试保存部分收集的内容，长度: {}", partialContent.length());
                onComplete.accept(partialContent);
            }
            
            try {
                writeSseError(outputStream, "AI 服务流式调用失败: " + e.getMessage());
            } catch (Exception writeEx) {
                log.error("写入错误 SSE 失败: {}", writeEx.getMessage());
            }
            throw new RuntimeException("AI 服务流式调用失败: " + e.getMessage());
        }
    }

    private void writeSseError(OutputStream outputStream, String errorMessage) throws Exception {
        String errorSse = "data: {\"error\": \"" + errorMessage + "\"}\n\n";
        outputStream.write(errorSse.getBytes(StandardCharsets.UTF_8));
        outputStream.flush();
    }
}
