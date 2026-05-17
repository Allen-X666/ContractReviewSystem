package com.example.contractreview.component;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Component;

/**
 * 流式响应收集器
 * 用于收集 SSE 流式响应的完整内容
 */
@Component
public class StreamingResponseCollector {

    private final StringBuilder contentBuilder = new StringBuilder();
    private final ObjectMapper objectMapper = new ObjectMapper();

    /**
     * 处理 SSE 数据行
     * @param line SSE 数据行
     */
    public void processLine(String line) {
        if (line.startsWith("data: ")) {
            String data = line.substring(6);
            // 跳过结束标记和开始标记
            if ("[DONE]".equals(data) || data.contains("\"type\": \"start\"")) {
                return;
            }
            try {
                // 解析 JSON 提取 content
                JsonNode node = objectMapper.readTree(data);
                if (node.has("content")) {
                    String content = node.get("content").asText();
                    if (content != null && !content.isEmpty()) {
                        contentBuilder.append(content);
                    }
                }
            } catch (Exception e) {
                // 如果不是 JSON 格式，直接追加（排除空内容）
                if (!data.trim().isEmpty() && !data.equals("null")) {
                    contentBuilder.append(data);
                }
            }
        }
    }

    /**
     * 获取完整内容
     */
    public String getFullContent() {
        return contentBuilder.toString();
    }

    /**
     * 重置收集器
     */
    public void reset() {
        contentBuilder.setLength(0);
    }
}
