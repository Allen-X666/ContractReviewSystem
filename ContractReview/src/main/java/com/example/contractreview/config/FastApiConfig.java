package com.example.contractreview.config;

import lombok.Data;
import lombok.Value;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Data
@Configuration
@ConfigurationProperties(prefix = "fastapi")
public class FastApiConfig {
    private String baseUrl = "http://localhost:8000";
    private String apiPrefix = "/api/v1";
    private int timeout = 30000;
    private int connectTimeout = 5000;
    public String getFullApiUrl() {
        return baseUrl + apiPrefix;
    }
}
