package com.example.contractreview.service;

import com.example.contractreview.common.Result;
import com.example.contractreview.model.dto.ChatbotCreateDTO;
import com.example.contractreview.model.vo.ChatbotConversationVO;
import com.example.contractreview.model.vo.ChatbotReplyVO;
import com.fasterxml.jackson.core.JsonProcessingException;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.web.servlet.mvc.method.annotation.StreamingResponseBody;

import java.io.IOException;
import java.util.List;

public interface ChatBotService {
    // 流式发送消息
    StreamingResponseBody streamMessage(String authorization, ChatbotCreateDTO chatbotCreateDTO);

    // 导出为EXCEL
    void exportExcel(Integer id, Integer userId, HttpServletResponse response) throws IOException;

    // 获取对话列表
    Result<List<ChatbotConversationVO>> getConversations(String authorization) throws JsonProcessingException;

    // 获取对话详情
    Result<ChatbotReplyVO> getConversationDetail(String authorization, Integer id) throws JsonProcessingException;

    // 重命名对话
    Result<String> renameConversation(String authorization, Integer id, String name);

    // 删除对话
    Result<String> deleteConversation(String authorization, Integer id);
}
