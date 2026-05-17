# Spring Boot 项目优化建议报告

## 项目概述

**项目名称**: ContractReview (合同审查系统)  
**Spring Boot版本**: 4.0.5  
**Java版本**: 25  
**技术栈**: Spring Boot + MyBatis + MySQL + Redis + JWT + Swagger

---

## 一、架构设计优化建议

### 1.1 分层架构优化

#### 现状问题
- Controller层直接返回Service层的Result结果，耦合度较高
- 部分Service层方法过于冗长，职责不够单一
- VO/BO/DO分层不够清晰

#### 优化建议

```java
// 推荐的分层结构
├─ controller          // 控制层：参数校验、调用Service、返回Result
├─ service            
│   ├─ dto            // 服务层数据传输对象
│   ├─ bo             // 业务对象
│   └─ impl           // 服务实现
├─ domain             // 领域层（新增）
│   ├─ entity         // 领域实体
│   ├─ repository     // 仓储接口
│   └─ service        // 领域服务
├─ infrastructure     // 基础设施层（新增）
│   ├─ mapper         // 数据访问实现
│   ├─ client         // 外部服务客户端
│   └─ config         // 配置类
└─ common             // 公共组件
```

### 1.2 接口设计优化

#### 现状问题
```java
// 当前代码：Controller直接传递Authorization Header
@PostMapping("/upload")
public Result<UploadResultVO> uploadContract(@RequestHeader("Authorization") String authorization,
                                             @RequestParam MultipartFile file)
```

#### 优化建议
使用Spring Security + 自定义注解实现用户上下文注入：

```java
// 1. 自定义当前用户注解
@Target(ElementType.PARAMETER)
@Retention(RetentionPolicy.RUNTIME)
public @interface CurrentUser {
}

// 2. 用户上下文Holder
public class UserContext {
    private static final ThreadLocal<UserInfo> userHolder = new ThreadLocal<>();
    
    public static void setUser(UserInfo user) { userHolder.set(user); }
    public static UserInfo getUser() { return userHolder.get(); }
    public static void clear() { userHolder.remove(); }
}

// 3. Controller使用示例
@PostMapping("/upload")
public Result<UploadResultVO> uploadContract(@CurrentUser UserInfo user,
                                             @RequestParam MultipartFile file) {
    return contractService.uploadContract(user.getId(), file);
}
```

---

## 二、配置管理优化

### 2.1 多环境配置分离

#### 现状问题
- 所有配置集中在单个application.yml
- 敏感信息（密码、密钥）硬编码在配置文件中

#### 优化建议

```yaml
# application.yml - 公共配置
spring:
  profiles:
    active: ${SPRING_PROFILES_ACTIVE:dev}
  
---
# application-dev.yml - 开发环境
spring:
  datasource:
    url: jdbc:mysql://localhost:3306/contract_review_dev
    username: ${DB_USERNAME:root}
    password: ${DB_PASSWORD}

---
# application-prod.yml - 生产环境
spring:
  datasource:
    url: jdbc:mysql://${DB_HOST}:3306/contract_review
    username: ${DB_USERNAME}
    password: ${DB_PASSWORD}
    hikari:
      maximum-pool-size: 50
      minimum-idle: 10
```

### 2.2 敏感配置加密

```java
// 使用Jasypt加密敏感配置
@Configuration
public class JasyptConfig {
    
    @Bean("jasyptStringEncryptor")
    public StringEncryptor stringEncryptor() {
        PooledPBEStringEncryptor encryptor = new PooledPBEStringEncryptor();
        SimpleStringPBEConfig config = new SimpleStringPBEConfig();
        config.setPassword(System.getenv("JASYPT_ENCRYPTOR_PASSWORD"));
        config.setAlgorithm("PBEWITHHMACSHA512ANDAES_256");
        config.setPoolSize(1);
        encryptor.setConfig(config);
        return encryptor;
    }
}

// 配置文件中加密后的密码
# ENC(加密后的密文)
spring.datasource.password: ENC(XvH8KpLmNqRsTuVw...)
```

### 2.3 配置属性类优化

#### 现状问题
```java
// FastApiConfig使用了@Data + @ConfigurationProperties，但存在一些问题
@Data
@Configuration
@ConfigurationProperties(prefix = "fastapi")
public class FastApiConfig {
    private String baseUrl = "http://localhost:8000";  // 默认值应该来自配置
    // ...
}
```

#### 优化建议
```java
@Configuration
@ConfigurationProperties(prefix = "fastapi")
@Validated  // 添加参数校验
public class FastApiConfig {
    
    @NotBlank(message = "FastAPI基础URL不能为空")
    @URL(message = "FastAPI基础URL格式不正确")
    private String baseUrl;
    
    @NotBlank
    private String apiPrefix = "/api/v1";
    
    @Min(1000)
    @Max(300000)
    private int timeout = 30000;
    
    @Min(1000)
    @Max(60000)
    private int connectTimeout = 5000;
    
    // 使用构造函数或Builder模式，移除@Data避免被修改
    public String getFullApiUrl() {
        return baseUrl + apiPrefix;
    }
}
```

---

## 三、数据访问层优化

### 3.1 MyBatis优化

#### 现状问题
- XML中使用了`SELECT *`，可能导致不必要的数据传输
- 部分查询没有索引提示
- 动态SQL中缺少必要的空值判断

#### 优化建议

```xml
<!-- 1. 避免SELECT *，明确指定字段 -->
<select id="selectById" resultMap="BaseResultMap">
    SELECT 
        id, file_name, file_path, file_size, 
        file_type, user_id, review_status, 
        risk_level, review_score, created_at
    FROM contract
    WHERE id = #{id}
</select>

<!-- 2. 复杂查询添加索引提示（根据实际情况） -->
<select id="selectStatsByUserId" resultType="ContractStats">
    SELECT /*+ INDEX(contract idx_user_id) */
        COUNT(*) as total,
        SUM(CASE WHEN review_status = 'pending' THEN 1 ELSE 0 END) as pending
    FROM contract
    WHERE user_id = #{userId}
</select>

<!-- 3. 批量操作优化 -->
<insert id="batchInsert">
    INSERT INTO contract (
        file_name, file_path, file_size, 
        file_type, user_id, created_at
    ) VALUES
    <foreach collection="list" item="item" separator=",">
        (#{item.fileName}, #{item.filePath}, #{item.fileSize},
         #{item.fileType}, #{item.userId}, NOW())
    </foreach>
</insert>
```

### 3.2 数据库连接池优化

```yaml
# HikariCP生产环境推荐配置
spring:
  datasource:
    hikari:
      pool-name: ContractReviewHikariPool
      # 基础配置
      minimum-idle: 10              # 最小空闲连接
      maximum-pool-size: 50         # 最大连接数（根据服务器配置调整）
      connection-timeout: 20000     # 连接超时时间（毫秒）
      idle-timeout: 300000          # 空闲连接超时时间（5分钟）
      max-lifetime: 1200000         # 连接最大生命周期（20分钟）
      
      # 性能优化
      auto-commit: false            # 手动控制事务
      connection-test-query: SELECT 1
      validation-timeout: 3000      # 连接验证超时
      leak-detection-threshold: 60000  # 连接泄漏检测阈值
      
      # 监控指标
      register-mbeans: true         # 注册JMX MBean用于监控
```

### 3.3 缓存策略优化

#### 现状问题
- 缓存使用较为简单，没有统一的缓存管理策略
- 部分热点数据没有缓存

#### 优化建议

```java
@Configuration
@EnableCaching
public class CacheConfig {
    
    @Bean
    public CacheManager cacheManager(RedisConnectionFactory factory) {
        RedisCacheConfiguration config = RedisCacheConfiguration.defaultCacheConfig()
            .entryTtl(Duration.ofMinutes(10))  // 默认过期时间
            .serializeKeysWith(RedisSerializationContext.SerializationPair
                .fromSerializer(new StringRedisSerializer()))
            .serializeValuesWith(RedisSerializationContext.SerializationPair
                .fromSerializer(new GenericJackson2JsonRedisSerializer()));
        
        return RedisCacheManager.builder(factory)
            .cacheDefaults(config)
            .withCacheConfiguration("contract", 
                RedisCacheConfiguration.defaultCacheConfig()
                    .entryTtl(Duration.ofMinutes(5)))
            .withCacheConfiguration("user",
                RedisCacheConfiguration.defaultCacheConfig()
                    .entryTtl(Duration.ofHours(1)))
            .transactionAware()
            .build();
    }
}

// Service层使用示例
@Service
public class ContractServiceImpl implements ContractService {
    
    @Cacheable(value = "contract", key = "'contract:' + #contractId")
    public ContractVO getContractById(Long contractId) {
        // 查询逻辑
    }
    
    @CacheEvict(value = "contract", key = "'contract:' + #contractId")
    public void updateContract(Long contractId, ContractDTO dto) {
        // 更新逻辑
    }
    
    @Caching(evict = {
        @CacheEvict(value = "contract", allEntries = true),
        @CacheEvict(value = "contractStats", allEntries = true)
    })
    public void deleteContract(Long contractId) {
        // 删除逻辑
    }
}
```

---

## 四、安全性优化

### 4.1 JWT认证优化

#### 现状问题
- JWT密钥硬编码在配置文件中
- Token刷新机制可以进一步优化
- 缺少Token黑名单的过期清理

#### 优化建议

```java
@Component
public class JwtTokenProvider {
    
    private final SecretKey secretKey;
    private final long accessTokenValidity;
    private final long refreshTokenValidity;
    
    // 使用硬件安全模块或密钥管理服务
    public JwtTokenProvider(@Value("${jwt.secret}") String secret,
                           @Value("${jwt.access-token-validity:3600000}") long accessValidity,
                           @Value("${jwt.refresh-token-validity:604800000}") long refreshValidity) {
        // 密钥长度校验
        if (secret.length() < 32) {
            throw new IllegalArgumentException("JWT密钥长度必须至少32字符");
        }
        this.secretKey = Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
        this.accessTokenValidity = accessValidity;
        this.refreshTokenValidity = refreshValidity;
    }
    
    public String generateAccessToken(UserDetails userDetails) {
        return generateToken(userDetails, accessTokenValidity, TOKEN_TYPE_ACCESS);
    }
    
    public String generateRefreshToken(UserDetails userDetails) {
        return generateToken(userDetails, refreshTokenValidity, TOKEN_TYPE_REFRESH);
    }
    
    private String generateToken(UserDetails userDetails, long validity, String type) {
        Date now = new Date();
        Date expiry = new Date(now.getTime() + validity);
        
        return Jwts.builder()
            .subject(userDetails.getUsername())
            .issuedAt(now)
            .expiration(expiry)
            .claim("type", type)
            .claim("roles", userDetails.getAuthorities().stream()
                .map(GrantedAuthority::getAuthority)
                .collect(Collectors.toList()))
            .signWith(secretKey, Jwts.SIG.HS512)  // 使用更强的算法
            .compact();
    }
}

// Token黑名单服务（带自动清理）
@Service
public class TokenBlacklistService {
    
    private final StringRedisTemplate redisTemplate;
    private static final String BLACKLIST_PREFIX = "token:blacklist:";
    
    public void blacklistToken(String token, long expirationTime) {
        String jti = extractJti(token);
        long ttl = expirationTime - System.currentTimeMillis();
        if (ttl > 0) {
            redisTemplate.opsForValue().set(
                BLACKLIST_PREFIX + jti, 
                "1", 
                Duration.ofMillis(ttl)
            );
        }
    }
    
    public boolean isBlacklisted(String token) {
        String jti = extractJti(token);
        return Boolean.TRUE.equals(
            redisTemplate.hasKey(BLACKLIST_PREFIX + jti)
        );
    }
}
```

### 4.2 API安全防护

```java
// 1. 接口防重放攻击
@Component
public class ReplayAttackInterceptor implements HandlerInterceptor {
    
    private final StringRedisTemplate redisTemplate;
    private static final String NONCE_PREFIX = "nonce:";
    private static final long NONCE_EXPIRE = 300; // 5分钟
    
    @Override
    public boolean preHandle(HttpServletRequest request, 
                            HttpServletResponse response, 
                            Object handler) {
        String nonce = request.getHeader("X-Nonce");
        String timestamp = request.getHeader("X-Timestamp");
        
        // 校验时间戳（防止过期请求）
        long ts = Long.parseLong(timestamp);
        if (Math.abs(System.currentTimeMillis() - ts) > 300000) {
            throw new BusinessException("请求已过期");
        }
        
        // 校验nonce（防止重放）
        String nonceKey = NONCE_PREFIX + nonce;
        if (Boolean.TRUE.equals(redisTemplate.hasKey(nonceKey))) {
            throw new BusinessException("重复请求");
        }
        
        redisTemplate.opsForValue().set(nonceKey, "1", Duration.ofSeconds(NONCE_EXPIRE));
        return true;
    }
}

// 2. 接口限流（基于令牌桶算法）
@Component
public class RateLimitInterceptor implements HandlerInterceptor {
    
    private final Map<String, RateLimiter> limiters = new ConcurrentHashMap<>();
    
    @Override
    public boolean preHandle(HttpServletRequest request, 
                            HttpServletResponse response, 
                            Object handler) {
        String clientId = getClientId(request);
        RateLimiter limiter = limiters.computeIfAbsent(clientId, 
            k -> RateLimiter.create(100.0)); // 每秒100个请求
        
        if (!limiter.tryAcquire()) {
            response.setStatus(429);
            response.getWriter().write("{"code":429,"message":"请求过于频繁"}");
            return false;
        }
        return true;
    }
}
```

---

## 五、性能优化

### 5.1 异步处理优化

#### 现状问题
- AsyncConfig只配置了验证码发送线程池
- 其他异步场景没有统一的线程池管理

#### 优化建议

```java
@Configuration
@EnableAsync
public class AsyncConfig implements AsyncConfigurer {
    
    // 验证码发送线程池
    @Bean("verifyCodeExecutor")
    public Executor verifyCodeExecutor() {
        ThreadPoolTaskExecutor executor = createExecutor(
            "verify-code-", 5, 20, 100, 60);
        log.info("验证码发送线程池初始化完成");
        return executor;
    }
    
    // 邮件发送线程池
    @Bean("mailExecutor")
    public Executor mailExecutor() {
        return createExecutor("mail-", 10, 30, 200, 120);
    }
    
    // 文件处理线程池
    @Bean("fileExecutor")
    public Executor fileExecutor() {
        return createExecutor("file-", 5, 15, 50, 300);
    }
    
    // 报告生成线程池（CPU密集型）
    @Bean("reportExecutor")
    public Executor reportExecutor() {
        int processors = Runtime.getRuntime().availableProcessors();
        return createExecutor("report-", processors, processors * 2, 100, 600);
    }
    
    private ThreadPoolTaskExecutor createExecutor(String prefix, 
                                                   int core, 
                                                   int max, 
                                                   int queue, 
                                                   int awaitSeconds) {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(core);
        executor.setMaxPoolSize(max);
        executor.setQueueCapacity(queue);
        executor.setThreadNamePrefix(prefix);
        executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
        executor.setWaitForTasksToCompleteOnShutdown(true);
        executor.setAwaitTerminationSeconds(awaitSeconds);
        executor.initialize();
        return executor;
    }
    
    @Override
    public Executor getAsyncExecutor() {
        return verifyCodeExecutor();
    }
    
    @Override
    public AsyncUncaughtExceptionHandler getAsyncUncaughtExceptionHandler() {
        return (ex, method, params) -> 
            log.error("异步方法执行异常: {}.{}，参数: {}", 
                method.getDeclaringClass().getName(),
                method.getName(), 
                Arrays.toString(params), ex);
    }
}
```

### 5.2 HTTP客户端优化

#### 现状问题
- FastApiClient使用SimpleClientHttpRequestFactory，性能一般
- 缺少连接池配置

#### 优化建议

```java
@Component
public class FastApiClient {
    
    private final RestClient restClient;
    
    public FastApiClient(FastApiConfig config, ObjectMapper objectMapper) {
        // 使用Apache HttpClient连接池
        PoolingHttpClientConnectionManager cm = new PoolingHttpClientConnectionManager();
        cm.setMaxTotal(200);              // 最大连接数
        cm.setDefaultMaxPerRoute(50);     // 每个路由最大连接
        cm.setValidateAfterInactivity(30000); // 连接验证间隔
        
        CloseableHttpClient httpClient = HttpClients.custom()
            .setConnectionManager(cm)
            .evictIdleConnections(60, TimeUnit.SECONDS)  // 空闲连接回收
            .disableAutomaticRetries()    // 手动控制重试
            .build();
        
        HttpComponentsClientHttpRequestFactory factory = 
            new HttpComponentsClientHttpRequestFactory(httpClient);
        factory.setConnectTimeout(config.getConnectTimeout());
        factory.setReadTimeout(config.getTimeout());
        
        this.restClient = RestClient.builder()
            .requestFactory(factory)
            .baseUrl(config.getFullApiUrl())
            .defaultHeader(HttpHeaders.CONTENT_TYPE, MediaType.APPLICATION_JSON_VALUE)
            .requestInterceptor((request, body, execution) -> {
                // 添加请求日志
                log.debug("FastAPI请求: {} {}", request.getMethod(), request.getURI());
                return execution.execute(request, body);
            })
            .build();
    }
}
```

### 5.3 数据库查询优化

```java
@Service
public class ContractServiceImpl implements ContractService {
    
    // 1. 使用批量查询替代循环查询
    @Override
    public Result<List<ContractVO>> getContractList(String authorization, 
                                                     Integer page, 
                                                     Integer pageSize) {
        Integer userId = tokenUtils.getUserId(authorization);
        
        // 使用PageHelper分页
        PageHelper.startPage(page, pageSize);
        
        // 单次查询获取合同列表
        List<Contract> contracts = contractMapper.selectByUserId(userId.longValue());
        
        if (contracts.isEmpty()) {
            return Result.success(Collections.emptyList());
        }
        
        // 批量获取关联的reviewId（使用IN查询替代循环）
        List<Integer> contractIds = contracts.stream()
            .map(Contract::getId)
            .collect(Collectors.toList());
        
        Map<Integer, Integer> reviewIdMap = contractIds.size() > 0 
            ? reviewMapper.getLatestReviewIdsByContractIds(contractIds, userId)
                .stream()
                .collect(Collectors.toMap(
                    row -> (Integer) row.get("contractId"),
                    row -> (Integer) row.get("reviewId"),
                    (v1, v2) -> v1
                ))
            : Collections.emptyMap();
        
        // 组装VO
        List<ContractVO> voList = contracts.stream()
            .map(c -> convertToVO(c, reviewIdMap.get(c.getId())))
            .collect(Collectors.toList());
        
        return Result.success(voList);
    }
}
```

---

## 六、日志与监控优化

### 6.1 日志规范

```yaml
# 优化后的日志配置
logging:
  level:
    root: WARN
    com.example.contractreview: INFO
    com.example.contractreview.mapper: DEBUG  # 开发环境使用，生产环境关闭
  pattern:
    console: "%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] [%X{traceId}] %-5level %logger{36} - %msg%n"
    file: "%d{yyyy-MM-dd HH:mm:ss.SSS} [%thread] [%X{traceId}] %-5level %logger{36} - %msg%n"
  logback:
    rollingpolicy:
      max-file-size: 100MB
      max-history: 30
      total-size-cap: 10GB
      clean-history-on-start: false
  
# 分布式链路追踪（可选）
tracing:
  enabled: true
  sampling:
    probability: 0.1  # 10%采样率
```

### 6.2 统一日志工具类

```java
@Component
@Slf4j
public class OperationLogger {
    
    private final ObjectMapper objectMapper;
    
    public void logOperation(String operation, Object params, Object result) {
        try {
            MDC.put("operation", operation);
            log.info("操作日志 | 操作:{} | 参数:{} | 结果:{}",
                operation,
                objectMapper.writeValueAsString(params),
                objectMapper.writeValueAsString(result));
        } catch (Exception e) {
            log.warn("操作日志序列化失败", e);
        } finally {
            MDC.remove("operation");
        }
    }
    
    public void logError(String operation, Object params, Throwable error) {
        try {
            MDC.put("operation", operation);
            log.error("操作异常 | 操作:{} | 参数:{} | 异常:{}",
                operation,
                objectMapper.writeValueAsString(params),
                error.getMessage(),
                error);
        } finally {
            MDC.remove("operation");
        }
    }
}
```

### 6.3 健康检查与指标监控

```java
@Component
public class CustomHealthIndicator implements HealthIndicator {
    
    private final FastApiClient fastApiClient;
    private final StringRedisTemplate redisTemplate;
    
    @Override
    public Health health() {
        Health.Builder builder = Health.up();
        
        // 检查FastAPI服务
        try {
            fastApiClient.healthCheck();
            builder.withDetail("fastApi", "UP");
        } catch (Exception e) {
            builder.down().withDetail("fastApi", "DOWN: " + e.getMessage());
        }
        
        // 检查Redis
        try {
            redisTemplate.opsForValue().get("health:check");
            builder.withDetail("redis", "UP");
        } catch (Exception e) {
            builder.down().withDetail("redis", "DOWN: " + e.getMessage());
        }
        
        return builder.build();
    }
}

// 自定义指标收集
@Component
public class BusinessMetrics {
    
    private final MeterRegistry meterRegistry;
    
    public void recordContractUpload(String fileType, long fileSize) {
        meterRegistry.counter("contract.upload", 
            "fileType", fileType).increment();
        
        meterRegistry.summary("contract.upload.size",
            "fileType", fileType).record(fileSize);
    }
    
    public void recordReviewDuration(long durationMs, String status) {
        meterRegistry.timer("review.duration",
            "status", status).record(durationMs, TimeUnit.MILLISECONDS);
    }
}
```

---

## 七、代码质量优化

### 7.1 统一异常处理增强

```java
@RestControllerAdvice
@Slf4j
public class GlobalExceptionHandler {
    
    // 业务异常
    @ExceptionHandler(BusinessException.class)
    public Result<Void> handleBusinessException(BusinessException e, 
                                                HttpServletRequest request) {
        log.warn("业务异常 | URI:{} | 错误码:{} | 错误信息:{}",
            request.getRequestURI(), e.getCode(), e.getMessage());
        return Result.error(e.getCode(), e.getMessage());
    }
    
    // 参数校验异常 - 优化返回格式
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public Result<Map<String, Object>> handleValidationException(
            MethodArgumentNotValidException e,
            HttpServletRequest request) {
        
        Map<String, Object> errors = e.getBindingResult().getFieldErrors().stream()
            .collect(Collectors.toMap(
                FieldError::getField,
                fieldError -> Optional.ofNullable(fieldError.getDefaultMessage())
                    .orElse("参数错误"),
                (v1, v2) -> v1
            ));
        
        log.warn("参数校验失败 | URI:{} | 错误:{}",
            request.getRequestURI(), errors);
        
        return Result.error(ResultCode.VALIDATION_ERROR.getCode(), 
            "请求参数校验失败", errors);
    }
    
    // 外部服务调用异常
    @ExceptionHandler(FastApiException.class)
    public Result<Void> handleFastApiException(FastApiException e,
                                               HttpServletRequest request) {
        log.error("FastAPI调用异常 | URI:{} | 操作:{} | 异常:{}",
            request.getRequestURI(), e.getOperation(), e.getMessage(), e);
        return Result.error(ResultCode.SERVICE_UNAVAILABLE.getCode(),
            "AI服务暂时不可用，请稍后重试");
    }
    
    // 兜底异常处理
    @ExceptionHandler(Exception.class)
    public Result<Void> handleException(Exception e, HttpServletRequest request) {
        String requestId = MDC.get("traceId");
        log.error("系统异常 | URI:{} | 请求ID:{} | 异常:{}",
            request.getRequestURI(), requestId, e.getMessage(), e);
        
        return Result.error(ResultCode.ERROR.getCode(),
            "系统繁忙，请稍后重试（错误码：" + requestId + "）");
    }
}
```

### 7.2 工具类优化

```java
// 使用不可变工具类
public final class JwtUtils {
    
    private JwtUtils() {
        throw new AssertionError("工具类禁止实例化");
    }
    
    // 线程安全的ObjectMapper
    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper()
        .registerModule(new JavaTimeModule())
        .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
    
    public static String toJson(Object obj) throws JsonProcessingException {
        return OBJECT_MAPPER.writeValueAsString(obj);
    }
}

// 常量类优化
public final class CacheKeys {
    
    private CacheKeys() {}
    
    // 使用模板方法生成key
    public static String contract(Long contractId) {
        return "contract:" + contractId;
    }
    
    public static String userStats(Long userId) {
        return "user:stats:" + userId;
    }
    
    public static String reviewResult(Integer reviewId) {
        return "review:result:" + reviewId;
    }
}
```

---

## 八、测试优化

### 8.1 单元测试规范

```java
@SpringBootTest
@AutoConfigureMockMvc
@Transactional
class ContractControllerTest {
    
    @Autowired
    private MockMvc mockMvc;
    
    @Autowired
    private ObjectMapper objectMapper;
    
    @MockBean
    private ContractService contractService;
    
    @Test
    @DisplayName("上传合同-成功场景")
    void uploadContract_Success() throws Exception {
        // Given
        MockMultipartFile file = new MockMultipartFile(
            "file", "test.pdf", "application/pdf", "test content".getBytes());
        
        UploadResultVO resultVO = UploadResultVO.builder()
            .contractId(1L)
            .fileName("test.pdf")
            .build();
        
        when(contractService.uploadContract(any(), any()))
            .thenReturn(Result.success(resultVO));
        
        // When & Then
        mockMvc.perform(multipart("/api/contract/upload")
                .file(file)
                .header("Authorization", "Bearer test-token"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.code").value(200))
            .andExpect(jsonPath("$.data.contractId").value(1));
    }
    
    @Test
    @DisplayName("上传合同-文件为空")
    void uploadContract_EmptyFile() throws Exception {
        mockMvc.perform(multipart("/api/contract/upload")
                .header("Authorization", "Bearer test-token"))
            .andExpect(status().isBadRequest());
    }
}
```

### 8.2 集成测试

```java
@SpringBootTest
@Testcontainers
class ContractServiceIntegrationTest {
    
    @Container
    static MySQLContainer<?> mysql = new MySQLContainer<>("mysql:8.0")
        .withDatabaseName("test_contract");
    
    @Container
    static GenericContainer<?> redis = new GenericContainer<>("redis:7-alpine")
        .withExposedPorts(6379);
    
    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", mysql::getJdbcUrl);
        registry.add("spring.datasource.username", mysql::getUsername);
        registry.add("spring.datasource.password", mysql::getPassword);
        registry.add("spring.data.redis.host", redis::getHost);
        registry.add("spring.data.redis.port", redis::getFirstMappedPort);
    }
    
    @Autowired
    private ContractService contractService;
    
    @Test
    @DisplayName("合同CRUD完整流程")
    void contractCrudFlow() {
        // 测试完整业务流程
    }
}
```

---

## 九、部署与运维优化

### 9.1 Docker化配置

```dockerfile
# Dockerfile
FROM eclipse-temurin:25-jdk-alpine as builder
WORKDIR /app
COPY .mvn/ .mvn
COPY mvnw pom.xml ./
RUN ./mvnw dependency:go-offline

COPY src ./src
RUN ./mvnw clean package -DskipTests

FROM eclipse-temurin:25-jre-alpine
WORKDIR /app

# 创建非root用户
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# JVM参数优化
ENV JAVA_OPTS="-XX:+UseG1GC \
               -XX:MaxRAMPercentage=75.0 \
               -XX:InitialRAMPercentage=50.0 \
               -XX:+UseContainerSupport \
               -Djava.security.egd=file:/dev/./urandom \
               -Dspring.backgroundpreinitializer.ignore=true"

COPY --from=builder /app/target/*.jar app.jar
RUN chown -R appuser:appgroup /app
USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=60s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8080/api/actuator/health || exit 1

ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]
```

### 9.2 Kubernetes部署配置

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: contract-review
  labels:
    app: contract-review
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: contract-review
  template:
    metadata:
      labels:
        app: contract-review
    spec:
      containers:
      - name: app
        image: contract-review:latest
        ports:
        - containerPort: 8080
        env:
        - name: SPRING_PROFILES_ACTIVE
          value: "prod"
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: password
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /api/actuator/health/liveness
            port: 8080
          initialDelaySeconds: 60
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/actuator/health/readiness
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 5
```

---

## 十、优化优先级建议

| 优先级 | 优化项 | 影响范围 | 预期收益 |
|--------|--------|----------|----------|
| **P0** | 敏感配置加密 | 安全性 | 防止密钥泄露 |
| **P0** | 数据库连接池优化 | 性能/稳定性 | 提升并发处理能力 |
| **P1** | 统一用户上下文 | 代码质量 | 减少重复代码，提升可维护性 |
| **P1** | 缓存策略优化 | 性能 | 降低数据库压力 |
| **P1** | 线程池统一管理 | 性能/稳定性 | 避免资源耗尽 |
| **P2** | HTTP客户端连接池 | 性能 | 提升外部服务调用效率 |
| **P2** | 接口限流防刷 | 安全性 | 防止恶意攻击 |
| **P2** | 日志规范统一 | 可观测性 | 便于问题排查 |
| **P3** | 健康检查完善 | 可观测性 | 提升运维效率 |
| **P3** | 容器化部署 | 部署效率 | 标准化部署流程 |

---

## 总结

本报告从架构设计、配置管理、数据访问、安全性、性能、日志监控、代码质量、测试、部署运维等多个维度，对合同审查系统的Spring Boot后端进行了全面的分析和优化建议。

建议按照优先级逐步实施，优先处理P0和P1级别的优化项，以快速提升系统的安全性、稳定性和性能。同时，建议建立代码评审机制和性能基准测试，持续监控优化效果。
