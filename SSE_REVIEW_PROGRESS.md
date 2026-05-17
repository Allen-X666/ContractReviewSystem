# SSE 审查进度推送实现文档

## 架构概览

```
┌─────────────┐      SSE Connection      ┌──────────────┐      HTTP Polling      ┌──────────────┐
│   前端页面   │ <──────────────────────> │  SpringBoot  │ <────────────────────> │   FastAPI    │
│  (Vue3)     │    GET /review/{id}/     │   (Java)     │    GET /review/{id}/   │   (Python)   │
│             │       progress           │              │       progress         │              │
└─────────────┘                          └──────────────┘                        └──────────────┘
       ▲                                          │
       │                                          │
       └──────────── 每 2 秒推送进度 ◄─────────────┘
```

***

## 一、后端实现（SpringBoot）

### 1. Controller 层

**文件**: `ReviewController.java`

```java
package com.example.contractreview.controller;

import com.example.contractreview.service.ReviewService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

@Slf4j
@RestController
@RequestMapping("/review")
@Tag(name = "ReviewController", description = "合同审核")
@RequiredArgsConstructor
public class ReviewController {

    private final ReviewService reviewService;

    /**
     * 获取审查进度（SSE 实时推送）
     * 
     * 前端通过 EventSource 建立长连接，SpringBoot 定时轮询 FastAPI 获取进度
     * 并将进度实时推送给前端
     */
    @GetMapping("/{reviewId}/progress")
    @Operation(summary = "获取审查进度（SSE）")
    public SseEmitter getReviewProgress(
            @RequestHeader("Authorization") String authorization,
            @PathVariable Long reviewId) {
        
        log.info("建立 SSE 连接获取审查进度, reviewId: {}", reviewId);
        return reviewService.connectProgress(authorization, reviewId);
    }
}
```

***

### 2. Service 接口

**文件**: `ReviewService.java`

```java
package com.example.contractreview.service;

import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

public interface ReviewService {

    /**
     * 连接审查进度（SSE）
     * 
     * @param authorization 用户认证令牌
     * @param reviewId 审查任务ID
     * @return SseEmitter SSE发射器，用于向前端推送实时进度
     */
    SseEmitter connectProgress(String authorization, Long reviewId);
}
```

***

### 3. Service 实现

**文件**: `ReviewServiceImpl.java`

```java
package com.example.contractreview.service.serviceImpl;

import com.example.contractreview.client.FastApiClient;
import com.example.contractreview.model.vo.fastapi.FastApiResult;
import com.example.contractreview.model.vo.fastapi.ReviewProgressVO;
import com.example.contractreview.service.ReviewService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.IOException;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

@Slf4j
@Service
@RequiredArgsConstructor
public class ReviewServiceImpl implements ReviewService {

    private final FastApiClient fastApiClient;

    // SSE 连接超时时间：5分钟
    private static final long SSE_TIMEOUT = 300000L;
    
    // 轮询间隔：2秒
    private static final long POLLING_INTERVAL = 2;

    @Override
    public SseEmitter connectProgress(String authorization, Long reviewId) {
        // 1. 创建 SseEmitter 实例，设置超时时间
        SseEmitter emitter = new SseEmitter(SSE_TIMEOUT);
        
        // 2. 创建定时任务调度器，用于轮询 FastAPI
        final ScheduledExecutorService progressScheduler = 
            Executors.newSingleThreadScheduledExecutor(r -> {
                Thread thread = new Thread(r);
                thread.setName("review-progress-" + reviewId);
                thread.setDaemon(true);
                return thread;
            });

        // 3. 注册 SSE 连接完成回调
        emitter.onCompletion(() -> {
            log.info("SSE 连接正常完成, reviewId: {}", reviewId);
            shutdownScheduler(progressScheduler);
        });

        // 4. 注册 SSE 连接超时回调
        emitter.onTimeout(() -> {
            log.warn("SSE 连接超时, reviewId: {}", reviewId);
            shutdownScheduler(progressScheduler);
            try {
                emitter.send(SseEmitter.event()
                    .name("timeout")
                    .data("连接超时，请重新建立连接"));
            } catch (IOException e) {
                log.error("发送超时事件失败", e);
            }
        });

        // 5. 注册 SSE 连接错误回调
        emitter.onError((e) -> {
            log.error("SSE 连接发生错误, reviewId: {}", reviewId, e);
            shutdownScheduler(progressScheduler);
        });

        // 6. 启动定时任务，轮询 FastAPI 获取进度
        startPolling(emitter, progressScheduler, reviewId);

        return emitter;
    }

    /**
     * 启动轮询任务
     */
    private void startPolling(SseEmitter emitter, 
                             ScheduledExecutorService scheduler, 
                             Long reviewId) {
        
        scheduler.scheduleAtFixedRate(() -> {
            try {
                // 6.1 调用 FastAPI 获取最新进度
                FastApiResult<ReviewProgressVO> result = 
                    fastApiClient.getReviewProgress(reviewId);

                if (result == null || !result.isSuccess() || result.getData() == null) {
                    log.warn("获取进度失败或返回空数据, reviewId: {}", reviewId);
                    return;
                }

                ReviewProgressVO progress = result.getData();
                
                // 6.2 构建 SSE 事件并发送给前端
                sendProgressEvent(emitter, progress);

                // 6.3 检查是否完成或失败，如果是则关闭连接
                if (isCompletedOrFailed(progress.getStatus())) {
                    log.info("审查任务已完成或失败, reviewId: {}, status: {}", 
                        reviewId, progress.getStatus());
                    emitter.complete();
                    shutdownScheduler(scheduler);
                }

            } catch (Exception e) {
                log.error("轮询进度异常, reviewId: {}", reviewId, e);
                sendErrorEvent(emitter, e.getMessage());
            }
        }, 0, POLLING_INTERVAL, TimeUnit.SECONDS);
    }

    /**
     * 发送进度事件给前端
     */
    private void sendProgressEvent(SseEmitter emitter, ReviewProgressVO progress) {
        try {
            SseEmitter.SseEventBuilder event = SseEmitter.event()
                .name("progress")                          // 事件名称
                .id(String.valueOf(System.currentTimeMillis())) // 事件ID
                .data(progress, MediaType.APPLICATION_JSON);    // 事件数据
            
            emitter.send(event);
            
            log.debug("进度已推送: {}%, stage: {}", 
                progress.getProgress(), progress.getStage());
                
        } catch (IOException e) {
            log.error("发送进度事件失败", e);
            throw new RuntimeException("发送进度失败", e);
        }
    }

    /**
     * 发送错误事件给前端
     */
    private void sendErrorEvent(SseEmitter emitter, String errorMessage) {
        try {
            SseEmitter.SseEventBuilder event = SseEmitter.event()
                .name("error")
                .data("{\"message\": \"" + errorMessage + "\"}");
            
            emitter.send(event);
        } catch (IOException e) {
            log.error("发送错误事件失败", e);
        }
    }

    /**
     * 检查审查是否已完成或失败
     */
    private boolean isCompletedOrFailed(String status) {
        return "completed".equals(status) || "failed".equals(status);
    }

    /**
     * 安全关闭调度器
     */
    private void shutdownScheduler(ScheduledExecutorService scheduler) {
        try {
            scheduler.shutdown();
            if (!scheduler.awaitTermination(5, TimeUnit.SECONDS)) {
                scheduler.shutdownNow();
            }
        } catch (InterruptedException e) {
            scheduler.shutdownNow();
            Thread.currentThread().interrupt();
        }
    }
}
```

***

### 4. FastAPI 客户端

**文件**: `FastApiClient.java`

```java
package com.example.contractreview.client;

import com.example.contractreview.config.FastApiConfig;
import com.example.contractreview.model.vo.fastapi.FastApiResult;
import com.example.contractreview.model.vo.fastapi.ReviewProgressVO;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

@Slf4j
@Component
public class FastApiClient {

    private final RestClient restClient;

    public FastApiClient(FastApiConfig fastApiConfig) {
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
     * 获取审查进度
     */
    public FastApiResult<ReviewProgressVO> getReviewProgress(Long reviewId) {
        try {
            log.debug("调用 FastAPI 获取审查进度, reviewId: {}", reviewId);

            return restClient.get()
                    .uri("/review/{reviewId}/progress", reviewId)
                    .retrieve()
                    .body(new org.springframework.core.ParameterizedTypeReference<>() {});
                    
        } catch (RestClientException e) {
            log.error("调用 FastAPI 获取审查进度失败: {}", e.getMessage(), e);
            throw new RuntimeException("AI 服务调用失败: " + e.getMessage());
        }
    }
}
```

***

### 5. 数据模型

**文件**: `ReviewProgressVO.java`

```java
package com.example.contractreview.model.vo.fastapi;

import lombok.Data;
import java.util.Map;

/**
 * 审查进度 VO
 * 对应 FastAPI 返回的进度数据结构
 */
@Data
public class ReviewProgressVO {

    /**
     * 总体进度百分比 (0-100)
     */
    private Integer progress;

    /**
     * 当前阶段
     * 可选值: parsing, retrieving, analyzing, generating
     */
    private String stage;

    /**
     * 任务状态
     * 可选值: pending, processing, completed, failed
     */
    private String status;

    /**
     * 进度描述信息
     */
    private String message;

    /**
     * 各阶段详细进度
     */
    private Map<String, Integer> stageProgress;
}
```

**文件**: `FastApiResult.java`

```java
package com.example.contractreview.model.vo.fastapi;

import lombok.Data;

/**
 * FastAPI 统一响应包装
 */
@Data
public class FastApiResult<T> {

    private Integer code;
    private String message;
    private T data;

    public boolean isSuccess() {
        return code != null && code == 200;
    }
}
```

***

## 二、前端实现（Vue3）

### 1. API 层

**文件**: `src/api/review.js`

```javascript
import { get, post, del } from '@/utils/request'

/**
 * 获取审查进度（SSE 连接）
 * 
 * @param {number} reviewId - 审查任务ID
 * @param {Function} onMessage - 收到消息时的回调函数
 * @param {Function} onError - 发生错误时的回调函数
 * @returns {EventSource} SSE 连接实例，可用于手动关闭连接
 */
export function connectReviewProgress(reviewId, onMessage, onError) {
  // 创建 EventSource 连接
  const eventSource = new EventSource(
    `${import.meta.env.VITE_API_BASE_URL}/review/${reviewId}/progress`,
    { withCredentials: true }
  )

  // 监听默认消息事件
  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data)
      console.log('收到进度更新:', data)
      
      // 调用回调函数处理数据
      onMessage(data)
      
      // 如果审查完成或失败，自动关闭连接
      if (data.status === 'completed' || data.status === 'failed') {
        console.log('审查结束，关闭 SSE 连接')
        eventSource.close()
      }
    } catch (err) {
      console.error('解析 SSE 数据失败:', err)
    }
  }

  // 监听特定事件：progress
  eventSource.addEventListener('progress', (event) => {
    try {
      const data = JSON.parse(event.data)
      onMessage(data)
    } catch (err) {
      console.error('解析 progress 事件失败:', err)
    }
  })

  // 监听特定事件：error
  eventSource.addEventListener('error', (event) => {
    console.error('收到错误事件:', event.data)
    onError?.(new Error(event.data))
    eventSource.close()
  })

  // 监听特定事件：timeout
  eventSource.addEventListener('timeout', (event) => {
    console.warn('连接超时:', event.data)
    onError?.(new Error('连接超时'))
    eventSource.close()
  })

  // 连接打开时
  eventSource.onopen = () => {
    console.log('SSE 连接已建立')
  }

  // 连接错误时
  eventSource.onerror = (error) => {
    console.error('SSE 连接错误:', error)
    onError?.(error)
    
    // 检查连接状态
    if (eventSource.readyState === EventSource.CLOSED) {
      console.log('SSE 连接已关闭')
    } else if (eventSource.readyState === EventSource.CONNECTING) {
      console.log('SSE 正在重连...')
    }
  }

  return eventSource
}

/**
 * 关闭 SSE 连接
 * 
 * @param {EventSource} eventSource - SSE 连接实例
 */
export function closeReviewProgress(eventSource) {
  if (eventSource && eventSource.readyState !== EventSource.CLOSED) {
    console.log('手动关闭 SSE 连接')
    eventSource.close()
  }
}
```

***

### 2. Store 层（Pinia）

**文件**: `src/stores/review.js`

```javascript
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { 
  startReview, 
  connectReviewProgress, 
  closeReviewProgress 
} from '@/api/review'
import { ElMessage } from 'element-plus'

export const useReviewStore = defineStore('review', () => {
  // ==================== State ====================
  const currentReview = ref(null)
  const reviewProgress = ref(0)
  const reviewStage = ref('')
  const reviewStatus = ref('')
  const eventSource = ref(null)
  
  // 各阶段进度
  const stageProgress = ref({
    parsing: 0,
    retrieving: 0,
    analyzing: 0,
    generating: 0
  })

  // ==================== Getters ====================
  const isReviewing = computed(() => reviewStatus.value === 'processing')
  const isCompleted = computed(() => reviewStatus.value === 'completed')
  const hasFailed = computed(() => reviewStatus.value === 'failed')

  // ==================== Actions ====================

  /**
   * 开始审查
   */
  async function start(contractId, options = {}) {
    try {
      // 1. 调用 API 发起审查
      const result = await startReview(contractId, options)
      
      currentReview.value = result.data
      reviewStatus.value = 'processing'
      reviewProgress.value = 0
      
      // 2. 建立 SSE 连接获取实时进度
      connectProgress(result.data.review_id)
      
      return result
    } catch (error) {
      console.error('启动审查失败:', error)
      ElMessage.error('启动审查失败: ' + error.message)
      throw error
    }
  }

  /**
   * 连接进度推送（SSE）
   */
  function connectProgress(reviewId) {
    // 关闭已有连接
    if (eventSource.value) {
      closeReviewProgress(eventSource.value)
    }

    // 建立新连接
    eventSource.value = connectReviewProgress(
      reviewId,
      // onMessage: 收到进度更新
      (data) => {
        // 更新进度
        reviewProgress.value = data.progress || 0
        reviewStage.value = data.stage || ''
        reviewStatus.value = data.status || 'processing'
        
        // 更新各阶段进度
        if (data.stageProgress) {
          stageProgress.value = { ...stageProgress.value, ...data.stageProgress }
        }
        
        // 更新消息
        if (data.message) {
          currentReview.value = {
            ...currentReview.value,
            message: data.message
          }
        }
        
        // 审查完成时获取结果
        if (data.status === 'completed') {
          fetchResult(reviewId)
        }
        
        // 审查失败时提示
        if (data.status === 'failed') {
          ElMessage.error('审查失败: ' + (data.message || '未知错误'))
        }
      },
      // onError: 连接错误
      (error) => {
        console.error('进度连接错误:', error)
        ElMessage.error('审查进度连接异常，请刷新页面重试')
        reviewStatus.value = 'failed'
      }
    )
  }

  /**
   * 取消审查
   */
  async function cancel(reviewId) {
    try {
      // 关闭 SSE 连接
      if (eventSource.value) {
        closeReviewProgress(eventSource.value)
        eventSource.value = null
      }
      
      // 调用取消 API
      await cancelReview(reviewId)
      
      ElMessage.success('已取消审查')
      reviewStatus.value = 'cancelled'
    } catch (error) {
      console.error('取消审查失败:', error)
      ElMessage.error('取消审查失败')
      throw error
    }
  }

  /**
   * 清理资源
   */
  function cleanup() {
    if (eventSource.value) {
      closeReviewProgress(eventSource.value)
      eventSource.value = null
    }
  }

  return {
    // State
    currentReview,
    reviewProgress,
    reviewStage,
    reviewStatus,
    stageProgress,
    eventSource,
    // Getters
    isReviewing,
    isCompleted,
    hasFailed,
    // Actions
    start,
    connectProgress,
    cancel,
    cleanup
  }
})
```

***

### 3. 组件中使用

**文件**: `src/views/review/Index.vue`

```vue
<template>
  <div class="review-page">
    <!-- 审查进度展示 -->
    <div v-if="reviewStore.isReviewing" class="progress-section">
      <div class="progress-header">
        <div class="progress-title">
          <el-icon class="rotating"><Loading /></el-icon>
          <span>正在审查中...</span>
        </div>
        <div class="progress-percent">{{ reviewStore.reviewProgress }}%</div>
      </div>
      
      <!-- 进度条 -->
      <el-progress
        :percentage="reviewStore.reviewProgress"
        :stroke-width="8"
        :show-text="false"
        status="primary"
      />
      
      <!-- 各阶段状态 -->
      <div class="progress-stages">
        <div
          v-for="(label, stage) in stageLabels"
          :key="stage"
          class="stage-item"
          :class="getStageClass(stage)"
        >
          <el-icon v-if="isStageCompleted(stage)"><CircleCheck /></el-icon>
          <el-icon v-else-if="isStageActive(stage)"><Loading /></el-icon>
          <span v-else class="stage-dot"></span>
          <span class="stage-label">{{ label }}</span>
          <span v-if="stageProgress[stage] > 0" class="stage-percent">
            {{ stageProgress[stage] }}%
          </span>
        </div>
      </div>
      
      <!-- 当前操作信息 -->
      <div v-if="reviewStore.currentReview?.message" class="progress-message">
        {{ reviewStore.currentReview.message }}
      </div>
      
      <!-- 取消按钮 -->
      <el-button @click="handleCancel">
        <el-icon><CircleClose /></el-icon>
        <span>取消审查</span>
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useReviewStore } from '@/stores/review'

const route = useRoute()
const reviewStore = useReviewStore()

const contractId = route.params.contractId

// 阶段标签
const stageLabels = {
  parsing: '文档解析',
  retrieving: '知识检索',
  analyzing: '风险分析',
  generating: '报告生成'
}

// 获取阶段样式类
function getStageClass(stage) {
  const stages = Object.keys(stageLabels)
  const currentIndex = stages.indexOf(reviewStore.reviewStage)
  const stageIndex = stages.indexOf(stage)
  
  if (stageIndex < currentIndex) return 'completed'
  if (stageIndex === currentIndex) return 'active'
  return 'pending'
}

// 判断阶段是否完成
function isStageCompleted(stage) {
  const stages = Object.keys(stageLabels)
  const currentIndex = stages.indexOf(reviewStore.reviewStage)
  const stageIndex = stages.indexOf(stage)
  return stageIndex < currentIndex
}

// 判断阶段是否进行中
function isStageActive(stage) {
  return stage === reviewStore.reviewStage
}

// 取消审查
async function handleCancel() {
  try {
    await reviewStore.cancel(reviewStore.currentReview.review_id)
  } catch (error) {
    console.error('取消失败:', error)
  }
}

// 页面加载时启动审查
onMounted(() => {
  reviewStore.start(contractId)
})

// 页面卸载时清理资源
onUnmounted(() => {
  reviewStore.cleanup()
})
</script>

<style scoped>
.progress-section {
  padding: 20px;
  background: #f5f7fa;
  border-radius: 8px;
  margin-bottom: 20px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.progress-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 500;
}

.progress-percent {
  font-size: 24px;
  font-weight: bold;
  color: #409eff;
}

.progress-stages {
  display: flex;
  justify-content: space-around;
  margin-top: 20px;
  padding: 16px;
  background: white;
  border-radius: 4px;
}

.stage-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: #909399;
}

.stage-item.completed {
  color: #67c23a;
}

.stage-item.active {
  color: #409eff;
}

.stage-label {
  font-size: 14px;
}

.stage-percent {
  font-size: 12px;
  color: #909399;
}

.progress-message {
  margin-top: 16px;
  padding: 12px;
  background: white;
  border-radius: 4px;
  color: #606266;
  font-size: 14px;
}

.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
</style>
```

***

## 三、FastAPI 后端（Python）

**文件**: `app/api/v1/endpoints/review.py`

```python
from fastapi import APIRouter
from app.schemas.enums import ReviewStage, ReviewStatus
from app.schemas.models import Result, ReviewProgress

router = APIRouter()

# 模拟进度存储（实际应使用 Redis 或数据库）
review_progress_store = {}


@router.get("/{review_id}/progress")
async def get_review_progress(review_id: int):
    """
    获取审查进度
    
    SpringBoot 会轮询此接口获取最新进度
    """
    # 从存储中获取进度（实际应从任务队列或数据库获取）
    progress = review_progress_store.get(review_id, {
        "progress": 0,
        "stage": ReviewStage.PARSING,
        "status": ReviewStatus.PROCESSING,
        "message": "正在初始化...",
        "stage_progress": {
            "parsing": 0,
            "retrieving": 0,
            "analyzing": 0,
            "generating": 0
        }
    })
    
    return Result(data=progress)


@router.post("/{review_id}/update-progress")
async def update_review_progress(review_id: int, progress: ReviewProgress):
    """
    更新审查进度（内部使用）
    
    AI 任务执行过程中调用此接口更新进度
    """
    review_progress_store[review_id] = {
        "progress": progress.progress,
        "stage": progress.stage,
        "status": progress.status,
        "message": progress.message,
        "stage_progress": progress.stage_progress
    }
    
    return Result(message="进度已更新")
```

**文件**: `app/schemas/models.py`

```python
from pydantic import BaseModel
from typing import Optional, Dict
from app.schemas.enums import ReviewStage, ReviewStatus


class Result(BaseModel):
    """统一响应模型"""
    code: int = 200
    message: str = "success"
    data: Optional[dict] = None


class ReviewProgress(BaseModel):
    """审查进度模型"""
    progress: int  # 0-100
    stage: ReviewStage
    status: ReviewStatus
    message: str
    stage_progress: Dict[str, int]
```

**文件**: `app/schemas/enums.py`

```python
from enum import Enum


class ReviewStage(str, Enum):
    """审查阶段"""
    PARSING = "parsing"         # 文档解析
    RETRIEVING = "retrieving"   # 知识检索
    ANALYZING = "analyzing"     # 风险分析
    GENERATING = "generating"   # 报告生成


class ReviewStatus(str, Enum):
    """审查状态"""
    PENDING = "pending"         # 等待中
    PROCESSING = "processing"   # 进行中
    COMPLETED = "completed"     # 已完成
    FAILED = "failed"           # 失败
    CANCELLED = "cancelled"     # 已取消
```

***

## 四、流程时序图

```
前端                    SpringBoot                  FastAPI
 |                          |                          |
 |── POST /review/start ───>|                          |
 |                          |── POST /review/start ───>|
 |                          |<─ {review_id: 123} ──────|
 |<─ {review_id: 123} ──────|                          |
 |                          |                          |
 |── GET /review/123/progress (SSE) ──────────────────>|
 |                          |                          |
 |<─────── 建立 SSE 连接 ───|                          |
 |                          |                          |
 |                          |── GET /review/123/progress ──>|
 |                          |<─ {progress: 25, stage: "parsing"} |
 |<─ event: progress ───────|                          |
 |   {progress: 25}         |                          |
 |                          |                          |
 |                          |── GET /review/123/progress ──>|
 |                          |<─ {progress: 50, stage: "analyzing"} |
 |<─ event: progress ───────|                          |
 |   {progress: 50}         |                          |
 |                          |                          |
 |                          |── GET /review/123/progress ──>|
 |                          |<─ {progress: 100, status: "completed"} |
 |<─ event: progress ───────|                          |
 |   {progress: 100}        |                          |
 |<─ 关闭 SSE 连接 ─────────|                          |
 |                          |                          |
```

***

## 五、关键点说明

### 1. 为什么选择 SSE 而不是 WebSocket？

| 特性   | SSE         | WebSocket |
| ---- | ----------- | --------- |
| 方向   | 单向（服务器→客户端） | 双向        |
| 协议   | HTTP        | WebSocket |
| 复杂度  | 简单          | 较复杂       |
| 适用场景 | 实时推送、进度更新   | 即时通讯、游戏   |
| 重连   | 浏览器自动重连     | 需手动实现     |

**SSE 更适合本场景**：只需要服务器向客户端推送进度，不需要客户端向服务器发送数据。

### 2. 为什么要通过 SpringBoot 转发？

1. **统一认证**：SpringBoot 统一处理 JWT 认证
2. **日志记录**：可以在 SpringBoot 层记录完整请求链路
3. **服务解耦**：FastAPI 可以独立部署和扩展
4. **数据持久化**：SpringBoot 负责审查记录的持久化

### 3. 异常处理机制

- **连接超时**：SpringBoot 设置 5 分钟超时，超时后前端可重新建立连接
- **服务不可用**：SpringBoot 捕获 FastAPI 调用异常，通过 SSE 发送错误事件
- **前端断网**：EventSource 会自动尝试重连

### 4. 性能优化建议

1. **使用 Redis**：FastAPI 将进度写入 Redis，SpringBoot 从 Redis 读取
2. **减少轮询频率**：根据实际场景调整轮询间隔（当前 2 秒）
3. **连接池**：RestClient 使用连接池复用连接
4. **批量推送**：累积多个进度更新后一次性推送

