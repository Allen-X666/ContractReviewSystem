package com.example.contractreview.config;

import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.databind.DeserializationContext;
import com.fasterxml.jackson.databind.JsonDeserializer;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.databind.module.SimpleModule;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import com.fasterxml.jackson.datatype.jsr310.ser.LocalDateTimeSerializer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;

import java.io.IOException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.util.Arrays;
import java.util.List;

/**
 * Jackson全局配置
 * 接收格式: yyyy-MM-dd'T'HH:mm:ss (ISO格式) 或 yyyy-MM-dd HH:mm:ss
 * 返回格式: yyyy-MM-dd HH:mm:ss
 */
@Configuration
public class JacksonConfig {

    /**
     * 返回给前端的时间格式
     */
    private static final String OUTPUT_PATTERN = "yyyy-MM-dd HH:mm:ss";

    /**
     * 支持的输入格式列表（按优先级排序）
     */
    private static final List<DateTimeFormatter> INPUT_FORMATTERS = Arrays.asList(
            DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss"),  // ISO格式
            DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"),    // 带空格格式
            DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss.SSS"), // 带毫秒ISO格式
            DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss.SSS")   // 带毫秒空格格式
    );

    @Bean
    @Primary
    public ObjectMapper objectMapper() {
        ObjectMapper mapper = new ObjectMapper();

        // 注册JavaTimeModule用于处理JDK8日期时间
        JavaTimeModule javaTimeModule = new JavaTimeModule();

        // 配置LocalDateTime的序列化（返回给前端）
        javaTimeModule.addSerializer(LocalDateTime.class,
                new LocalDateTimeSerializer(DateTimeFormatter.ofPattern(OUTPUT_PATTERN)));

        mapper.registerModule(javaTimeModule);

        // 注册自定义反序列化器支持多种日期格式
        SimpleModule simpleModule = new SimpleModule();
        simpleModule.addDeserializer(LocalDateTime.class, new MultiFormatLocalDateTimeDeserializer());
        mapper.registerModule(simpleModule);

        // 禁用时间戳格式，使用字符串格式
        mapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);

        return mapper;
    }

    /**
     * 支持多种格式的LocalDateTime反序列化器
     */
    public static class MultiFormatLocalDateTimeDeserializer extends JsonDeserializer<LocalDateTime> {
        @Override
        public LocalDateTime deserialize(JsonParser p, DeserializationContext ctxt) throws IOException {
            String text = p.getValueAsString();
            if (text == null || text.trim().isEmpty()) {
                return null;
            }

            // 尝试每种格式
            for (DateTimeFormatter formatter : INPUT_FORMATTERS) {
                try {
                    return LocalDateTime.parse(text, formatter);
                } catch (DateTimeParseException e) {
                    // 继续尝试下一种格式
                }
            }

            // 所有格式都失败，抛出异常
            throw new IOException("无法解析日期时间: " + text + "，支持的格式: yyyy-MM-dd'T'HH:mm:ss 或 yyyy-MM-dd HH:mm:ss");
        }
    }
}
