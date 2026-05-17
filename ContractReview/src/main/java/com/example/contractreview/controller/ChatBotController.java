package com.example.contractreview.controller;

import com.example.contractreview.common.Result;
import com.example.contractreview.model.dto.ChatbotCreateDTO;
import com.example.contractreview.model.dto.ChatbotRenameDTO;
import com.example.contractreview.model.vo.ChatbotConversationVO;
import com.example.contractreview.model.vo.ChatbotReplyVO;
import com.example.contractreview.service.ChatBotService;
import com.example.contractreview.utils.TokenUtils;
import com.fasterxml.jackson.core.JsonProcessingException;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.StreamingResponseBody;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.List;

@RestController
@Slf4j
@Tag(name = "智能客服")
@RequestMapping("/chatbot")
@RequiredArgsConstructor
public class ChatBotController {

    private final ChatBotService chatBotService;
    private final TokenUtils tokenUtils;

    /**
     * 发送消息
     */
    @PostMapping("/messages")
    @Operation(summary = "发送消息")
    public ResponseEntity<StreamingResponseBody> sendMessage(
            @RequestHeader("Authorization") String authorization,
            @RequestBody ChatbotCreateDTO chatbotCreateDTO,
            HttpServletResponse response) {
        log.info("收到智能客服请求, conversationId: {}", chatbotCreateDTO.getConversationId());
        
        // 设置异步请求超时时间为 5 分钟
        response.setHeader("X-Accel-Buffering", "no");
        
        StreamingResponseBody stream = chatBotService.streamMessage(authorization, chatbotCreateDTO);
        return ResponseEntity.ok()
                .contentType(MediaType.TEXT_EVENT_STREAM)
                .header("Cache-Control", "no-cache")
                .header("Connection", "keep-alive")
                .header("X-Accel-Buffering", "no")
                .body(stream);
    }

    /**
     * 获取对话列表
     */
    @GetMapping("/conversations")
    @Operation(summary = "获取对话列表")
    public Result<List<ChatbotConversationVO>> getConversations(@RequestHeader("Authorization") String authorization) throws JsonProcessingException {
        log.info("获取对话列表");
        return chatBotService.getConversations(authorization);
    }

    /**
     * 获取对话详情
     */
    @GetMapping("/conversations/{id}")
    @Operation(summary = "获取对话详情")
    public Result<ChatbotReplyVO> getConversationDetail(@RequestHeader("Authorization") String authorization,
                                                        @PathVariable("id") Integer id) throws JsonProcessingException {
        log.info("获取对话详情, id: {}", id);
        return chatBotService.getConversationDetail(authorization, id);
    }

    /**
     * 重命名对话
     */
    @PutMapping("/conversations/{id}/name")
    @Operation(summary = "重命名对话")
    public Result<String> renameConversation(@RequestHeader("Authorization") String authorization,
                                             @RequestBody ChatbotRenameDTO dto,
                                             @PathVariable("id") Integer id){
        log.info("重命名对话, id: {}, name: {}", id, dto.getName());
        return chatBotService.renameConversation(authorization, id, dto.getName());
    }

    /**
     * 删除对话
     */
    @DeleteMapping("/conversations/{id}")
    @Operation(summary = "删除对话")
    public Result<String> deleteConversation(@RequestHeader("Authorization") String authorization,
                                                     @PathVariable("id") Integer id){
        log.info("删除对话, id: {}", id);
        return chatBotService.deleteConversation(authorization, id);
    }

    /**
     * 导出为EXCEL
     */
    @GetMapping("/conversations/{id}/export")
    @Operation(summary = "导出为EXCEL")
    public void exportConversation(@RequestHeader("Authorization") String authorization,
                                   @PathVariable("id") Integer id,
                                   HttpServletResponse response) {
        log.info("导出为EXCEL, id: {}", id);
        // 获取用户id
        Integer userId = tokenUtils.getUserId(authorization);
        try {
            // 调用service层方法，所有业务逻辑不变
            chatBotService.exportExcel(id, userId, response);
        } catch (Exception e) {
            log.error("导出Excel失败: {}", e.getMessage(), e);
            try {
                // 异常时，给前端返回友好的纯文本提示
                response.reset(); // 重置响应头，防止残留的Excel格式导致乱码
                response.setContentType("text/plain;charset=UTF-8");
                response.getOutputStream().write(("Excel导出失败: " + e.getMessage()).getBytes(StandardCharsets.UTF_8));
                response.getOutputStream().flush();
            } catch (IOException ex) {
                log.error("写入错误响应失败: {}", ex.getMessage());
            }
        }
    }
}
