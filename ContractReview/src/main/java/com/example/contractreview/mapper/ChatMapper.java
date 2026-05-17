package com.example.contractreview.mapper;

import com.example.contractreview.model.entity.ChatbotConversation;
import com.example.contractreview.model.entity.ChatbotMessage;
import com.example.contractreview.model.vo.ChatDetailVO;
import com.example.contractreview.model.vo.ChatbotConversationVO;
import com.example.contractreview.model.vo.ChatbotMessageVO;
import com.example.contractreview.model.vo.ChatbotReplyVO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

@Mapper
public interface ChatMapper {

    // 获取聊天详情
    List<ChatDetailVO> getChatDetail(Integer id, Integer userId);

    /**
     * 插入对话
     * @param conversation 对话实体
     * @return 影响行数
     */
    int insertConversation(@Param("conversation") ChatbotConversation conversation);

    /**
     * 插入消息
     * @param message 消息实体
     * @return 影响行数
     */
    int insertMessage(@Param("message") ChatbotMessage message);

    /**
     * 更新对话名称
     * @param conversationId 对话ID
     * @param name 对话名称
     * @return 影响行数
     */
    int updateConversationName(@Param("userId") Integer userId, @Param("conversationId") Integer conversationId, @Param("name") String name);

    /**
     * 根据ID查询对话
     * @param conversationId 对话ID
     * @return 对话实体
     */
    ChatbotConversation selectConversationById(@Param("conversationId") Long conversationId);

    /**
     * 获取对话列表
     * @param userId 用户ID
     * @return 对话列表
     */
    List<ChatbotConversationVO> getConversations(Integer userId);

    /**
     * 获取对话详情
     * @param id 对话ID
     * @param userId 用户ID
     * @return 对话详情
     */
    List<ChatbotMessageVO> getConversationDetail(Integer id, Integer userId);

    /**
     * 获取对话名称
     * @param id 对话ID
     * @return 对话名称
     */
    String getConversationName(Integer id);

    /**
     * 更新对话更新时间
     * @param conversationId 对话ID
     */
    void updateConversationUpdatedAt(Long conversationId);

    /**
     * 删除对话
     * @param userId 用户ID
     * @param id 对话ID
     * @return 影响行数
     */
    int deleteConversation(Integer userId, Integer id);

    /**
     * 根据对话ID获取历史消息（用于构建AI上下文）
     * @param conversationId 对话ID
     * @return 消息列表（按时间正序）
     */
    List<ChatbotMessageVO> getMessagesByConversationId(@Param("conversationId") Long conversationId);
}
