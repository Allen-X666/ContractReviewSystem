package com.example.contractreview.model.dto;

import com.example.contractreview.enums.NoticeType;
import com.example.contractreview.enums.PublishType;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * 公告发布请求DTO
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class NoticePublishDTO {

    /**
     * 公告标题
     */
    @NotBlank(message = "公告标题不能为空")
    @Size(max = 100, message = "公告标题长度不能超过100字符")
    private String title;

    /**
     * 公告类型: system-系统/feature-功能/maintenance-维护/other-其他
     */
    @NotNull(message = "公告类型不能为空")
    private NoticeType type;

    /**
     * 公告内容（支持Markdown）
     */
    @NotBlank(message = "公告内容不能为空")
    @Size(max = 2000, message = "公告内容长度不能超过2000字符")
    private String content;

    /**
     * 发布方式: immediate-立即发布/scheduled-定时发布
     */
    @NotNull(message = "发布方式不能为空")
    private PublishType publishType;

    /**
     * 发布时间（定时发布时必填）
     */
    private LocalDateTime publishTime;

    /**
     * 是否置顶: true-是/false-否
     */
    private Boolean isTop = false;
}
