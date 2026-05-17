package com.example.contractreview.service.serviceImpl;

import com.alibaba.excel.EasyExcel;
import com.alibaba.excel.write.metadata.style.WriteCellStyle;
import com.alibaba.excel.write.style.HorizontalCellStyleStrategy;
import com.example.contractreview.client.ChatBotClient;
import com.example.contractreview.common.Result;
import com.example.contractreview.constant.UserConstant;
import com.example.contractreview.mapper.ChatMapper;
import com.example.contractreview.model.dto.ChatbotCreateDTO;
import com.example.contractreview.model.dto.ChatbotRenameDTO;
import com.example.contractreview.model.entity.ChatExcel;
import com.example.contractreview.model.entity.ChatbotConversation;
import com.example.contractreview.model.entity.ChatbotMessage;
import com.example.contractreview.model.vo.ChatDetailVO;
import com.example.contractreview.model.vo.ChatbotConversationVO;
import com.example.contractreview.model.vo.ChatbotMessageVO;
import com.example.contractreview.model.vo.ChatbotReplyVO;
import com.example.contractreview.service.ChatBotService;
import com.example.contractreview.utils.TokenUtils;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.apache.poi.ss.usermodel.HorizontalAlignment;
import org.apache.poi.ss.usermodel.VerticalAlignment;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;
import org.springframework.web.servlet.mvc.method.annotation.StreamingResponseBody;

import java.io.IOException;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

@Service
@Slf4j
@RequiredArgsConstructor
public class ChatBotServiceImpl implements ChatBotService {

    private final ChatBotClient chatBotClient;
    private final StringRedisTemplate stringRedisTemplate;
    private final ChatMapper chatMapper;
    private final ObjectMapper objectMapper;
    private final TokenUtils tokenUtils;
    private final ExecutorService executorService = Executors.newFixedThreadPool(10);

    /**
     * 流式发送消息
     */
    @Override
    public StreamingResponseBody streamMessage(String authorization, ChatbotCreateDTO chatbotCreateDTO) {
        String content = chatbotCreateDTO.getContent();
        Integer conversationId = chatbotCreateDTO.getConversationId();
        Integer userId = tokenUtils.getUserId(authorization);
        deleteCach(userId, conversationId);
        if (userId == null) {
            throw new RuntimeException("用户认证信息无效");
        }

        log.info("流式发送消息，userId: {}, conversationId: {}, content: {}",
                userId, conversationId, content);

        // 处理对话ID
        Long finalConversationId = prepareConversation(conversationId, userId, content);

        // 保存用户消息
        saveUserMessage(finalConversationId, content);

        // 获取对话ID的副本用于lambda
        final Long convId = finalConversationId;

        try {
            return outputStream -> {
                try {
                    // 首先发送 conversationId
                    String conversationIdEvent = "data: {\"conversationId\": " + convId + "}\n\n";
                    outputStream.write(conversationIdEvent.getBytes(StandardCharsets.UTF_8));
                    outputStream.flush();
                    
                    chatBotClient.streamMessageWithCallback(content, convId, outputStream, aiResponse -> {
                        log.info("流式回调被调用，conversationId: {}, 内容长度: {}", convId, 
                                aiResponse != null ? aiResponse.length() : 0);
                        // 流式响应完成后，异步保存 AI 回复
                        executorService.submit(() -> {
                            try {
                                if (aiResponse != null && !aiResponse.trim().isEmpty()) {
                                    saveAiResponse(convId, aiResponse);
                                    log.info("流式响应保存完成，conversationId: {}", convId);
                                } else {
                                    log.warn("AI回复内容为空，跳过保存，conversationId: {}", convId);
                                }
                            } catch (Exception e) {
                                log.error("保存流式响应失败: {}", e.getMessage(), e);
                            }
                        });
                    }, authorization);
                } catch (Exception e) {
                    log.error("流式消息处理失败: {}", e.getMessage(), e);
                    throw new RuntimeException("流式消息处理失败: " + e.getMessage());
                }
            };
        } catch (Exception e) {
            log.error("流式消息处理失败: {}", e.getMessage(), e);
            throw new RuntimeException("流式消息处理失败: " + e.getMessage());
        }
    }

    /**
     * 导出为EXCEL
     */
    @Override
    public void exportExcel(Integer id, Integer userId, HttpServletResponse response) throws IOException {
        // 获取对话名称
        String conversationName = chatMapper.getConversationName(id);
        if (conversationName == null) {
            conversationName = "对话记录";
        }
        // 获取对话详情数据
        List<ChatExcel> chatExcels = fetchChatDetailForExport(id, userId);
        
        if (chatExcels.isEmpty()) {
            throw new RuntimeException("该对话没有可导出的消息记录");
        }

        // 设置响应头
        String fileName = URLEncoder.encode(conversationName, StandardCharsets.UTF_8).replaceAll("\\+", "%20");
        response.setContentType("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet");
        response.setCharacterEncoding("utf-8");
        response.setHeader("Content-Disposition", "attachment;filename*=utf-8''" + fileName + "_" + LocalDate.now() + ".xlsx");

        // 构建Excel数据
        List<List<String>> excelData = buildExcelData(chatExcels, conversationName);

        // 设置样式并写入Excel
        HorizontalCellStyleStrategy styleStrategy = createStyleStrategy();
        EasyExcel.write(response.getOutputStream())
                .sheet("对话详情")
                .registerWriteHandler(styleStrategy)
                .doWrite(excelData);
    }
    
    /**
     * 获取对话详情数据（优先从缓存获取）
     */
    private List<ChatExcel> fetchChatDetailForExport(Integer id, Integer userId) throws IOException {
        String key = UserConstant.CONVERSATION_DETAIL + id;
        String cachedDetail = stringRedisTemplate.opsForValue().get(key);
        
        if (cachedDetail != null) {
            // 从缓存中获取数据 - 缓存中存储的是 ChatbotReplyVO 对象
            try {
                ChatbotReplyVO replyVO = objectMapper.readValue(cachedDetail, ChatbotReplyVO.class);
                if (replyVO.getMessages() != null) {
                    return replyVO.getMessages().stream()
                            .map(msg -> ChatExcel.builder()
                                    .id(Math.toIntExact(msg.getId()))
                                    .role(msg.getRole())
                                    .content(msg.getContent())
                                    .createTime(msg.getCreatedAt())
                                    .build())
                            .toList();
                }
            } catch (Exception e) {
                log.warn("缓存数据格式不匹配，尝试从数据库获取: {}", e.getMessage());
            }
        }
        
        // 从数据库中获取数据
        try {
            List<ChatDetailVO> chatDetailList = chatMapper.getChatDetail(id, userId);
            return convertToChatExcelList(chatDetailList);
        } catch (Exception e) {
            log.error("获取聊天详情失败: {}", e.getMessage(), e);
            throw new RuntimeException("获取聊天详情失败: " + e.getMessage());
        }
    }
    
    /**
     * 将 ChatDetailVO 列表转换为 ChatExcel 列表
     */
    private List<ChatExcel> convertToChatExcelList(List<ChatDetailVO> chatDetailList) {
        return chatDetailList.stream()
                .map(vo -> ChatExcel.builder()
                        .id(vo.getId())
                        .role(vo.getRole())
                        .content(vo.getContent())
                        .createTime(vo.getCreateTime())
                        .build())
                .toList();
    }
    
    /**
     * 构建Excel数据
     */
    private List<List<String>> buildExcelData(List<ChatExcel> chatExcels, String conversationName) {
        List<List<String>> data = new ArrayList<>();
        
        // 表头
        data.add(Arrays.asList("序号", "角色", "内容", "发送时间"));
        
        // 消息数据
        int seq = 1;
        for (ChatExcel chat : chatExcels) {
            data.add(Arrays.asList(
                    String.valueOf(seq++),
                    translateRole(chat.getRole()),
                    chat.getContent(),
                    chat.getCreateTime().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"))
            ));
        }
        
        // 统计信息
        data.add(Arrays.asList("", "", "", ""));
        data.add(Arrays.asList("消息总数:", String.valueOf(chatExcels.size()), "", ""));
        data.add(Arrays.asList("文件创建者:", "XJL科技有限公司", "", ""));
        data.add(Arrays.asList("导出时间:", 
                LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss")), "", ""));
        
        return data;
    }
    
    /**
     * 角色翻译
     */
    private String translateRole(String role) {
        return switch (role != null ? role.toLowerCase() : "") {
            case "user" -> "用户";
            case "assistant" -> "智能客服";
            case "system" -> "系统";
            default -> role;
        };
    }
    
    /**
     * 创建Excel样式策略
     */
    private HorizontalCellStyleStrategy createStyleStrategy() {
        WriteCellStyle headStyle = new WriteCellStyle();
        headStyle.setHorizontalAlignment(HorizontalAlignment.CENTER);
        headStyle.setVerticalAlignment(VerticalAlignment.CENTER);
        
        WriteCellStyle contentStyle = new WriteCellStyle();
        contentStyle.setHorizontalAlignment(HorizontalAlignment.LEFT);
        contentStyle.setVerticalAlignment(VerticalAlignment.CENTER);
        
        return new HorizontalCellStyleStrategy(headStyle, contentStyle);
    }

    /**
     * 获取对话列表
     */
    @Override
    public Result<List<ChatbotConversationVO>> getConversations(String authorization) throws JsonProcessingException {
        Integer userId = tokenUtils.getUserId(authorization);
        String key = UserConstant.CONVERSATION_LIST + userId;
        String cachConversationList = stringRedisTemplate.opsForValue().get(key);
        if (cachConversationList != null){
            // 从缓存中获取数据
            List<ChatbotConversationVO> chatbotConversationVOS = objectMapper.readValue(cachConversationList, new TypeReference<List<ChatbotConversationVO>>() {});
            return Result.success(chatbotConversationVOS, (long) chatbotConversationVOS.size());
        }
        // 从数据库中获取数据
        try {
            List<ChatbotConversationVO> conversations = chatMapper.getConversations(userId);
            stringRedisTemplate.opsForValue().set(key, objectMapper.writeValueAsString(conversations));
            return Result.success(conversations, (long) conversations.size());
        } catch (Exception e) {
            log.error("获取对话列表失败: {}", e.getMessage(), e);
            throw new RuntimeException("获取对话列表失败: " + e.getMessage());
        }
    }

    /**
     * 获取对话详情
     */
    @Override
    public Result<ChatbotReplyVO> getConversationDetail(String authorization, Integer conversationId) throws JsonProcessingException {
        Integer userId = tokenUtils.getUserId(authorization);
        String key = UserConstant.CONVERSATION_DETAIL + conversationId;
        String cachConversationDetail = stringRedisTemplate.opsForValue().get(key);
        if (cachConversationDetail != null){
            // 从缓存中获取数据
            ChatbotReplyVO chatbotReplyVO = objectMapper.readValue(cachConversationDetail, ChatbotReplyVO.class);
            return Result.success(chatbotReplyVO);
        }
        // 从数据库中获取数据
        try {
            List<ChatbotMessageVO> messages = chatMapper.getConversationDetail(conversationId, userId);
            ChatbotReplyVO replyVO = new ChatbotReplyVO();
            replyVO.setId(conversationId);
            replyVO.setMessages(messages);
            stringRedisTemplate.opsForValue().set(key, objectMapper.writeValueAsString(replyVO));
            return Result.success(replyVO);
        } catch (Exception e) {
            log.error("获取对话详情失败: {}", e.getMessage(), e);
            throw new RuntimeException("获取对话详情失败: " + e.getMessage());
        }
    }

    /**
     * 删除对话
     */
    @Override
    public Result<String> deleteConversation(String authorization, Integer conversationId) {
        Integer userId = tokenUtils.getUserId(authorization);
        try {
            chatMapper.deleteConversation(conversationId, userId);
            deleteCach(userId, conversationId);
            return Result.success("删除成功");
        } catch (Exception e) {
            log.error("删除对话失败: {}", e.getMessage(), e);
            throw new RuntimeException("删除对话失败: " + e.getMessage());
        }
    }

    /**
     * 删除缓存
     */
    private void deleteCach(Integer userId, Integer conversationId) {
        String key = UserConstant.CONVERSATION_LIST + userId;
        String key2 = UserConstant.CONVERSATION_DETAIL + conversationId;
        stringRedisTemplate.delete(key);
        stringRedisTemplate.delete(key2);
    }

    /**
     * 准备对话（创建或获取现有对话）
     */
    private Long prepareConversation(Integer conversationId, Integer userId, String content) {
        if (conversationId == null) {
            // 创建新对话，使用用户消息的前20个字符作为标题
            String title = content.length() > 20 ? content.substring(0, 20) + "..." : content;
            ChatbotConversation conversation = new ChatbotConversation();
            conversation.setUserId(Long.valueOf(userId));
            conversation.setName(title);
            conversation.setStatus(1); // 1-正常
            conversation.setCreatedAt(LocalDateTime.now());
            conversation.setUpdatedAt(LocalDateTime.now());
            chatMapper.insertConversation(conversation);
            return conversation.getId();
        }
        return Long.valueOf(conversationId);
    }

    /**
     * 保存用户消息
     */
    private void saveUserMessage(Long conversationId, String content) {
        ChatbotMessage message = new ChatbotMessage();
        message.setConversationId(conversationId);
        message.setRole("user");
        message.setContent(content);
        message.setCreatedAt(LocalDateTime.now());
        chatMapper.insertMessage(message);
    }

    /**
     * 保存AI回复
     */
    private void saveAiResponse(Long conversationId, String content) {
        try {
            ChatbotMessage message = new ChatbotMessage();
            message.setConversationId(conversationId);
            message.setRole("assistant");
            message.setContent(content);
            message.setCreatedAt(LocalDateTime.now());
            chatMapper.insertMessage(message);
            log.info("AI回复已保存，conversationId: {}, 内容长度: {}", conversationId, content.length());
        } catch (Exception e) {
            log.error("保存AI回复失败，conversationId: {}, error: {}", conversationId, e.getMessage(), e);
            throw new RuntimeException("保存AI回复失败: " + e.getMessage());
        }
    }

    /**
     * 重命名对话
     */
    @Override
    public Result<String> renameConversation(String authorization, Integer conversationId, String name) {
        Integer userId = tokenUtils.getUserId(authorization);
        try {
            chatMapper.updateConversationName(userId, conversationId, name);
            deleteCach(userId, conversationId);
            return Result.success("重命名成功");
        } catch (Exception e) {
            log.error("重命名对话失败: {}", e.getMessage(), e);
            throw new RuntimeException("重命名对话失败: " + e.getMessage());
        }
    }
}
