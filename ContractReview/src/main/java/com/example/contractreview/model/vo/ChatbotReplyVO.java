package com.example.contractreview.model.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * 智能客服AI回复结果VO
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ChatbotReplyVO {

    /**
     * 对话ID
     */
    private Integer id;

    /**
     * 对话名称
     */
    private String name;

    /**
     * 回复消息
     */
    private List<ChatbotMessageVO> messages;
}
