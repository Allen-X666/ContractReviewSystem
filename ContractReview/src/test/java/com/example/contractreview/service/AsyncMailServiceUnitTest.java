package com.example.contractreview.service;

import com.example.contractreview.enums.NotificationType;
import jakarta.mail.internet.MimeMessage;
import lombok.extern.slf4j.Slf4j;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.test.util.ReflectionTestUtils;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

/**
 * AsyncMailService 单元测试类
 * 使用 Mockito 进行纯单元测试，不依赖 Spring 上下文
 */
@Slf4j
@ExtendWith(MockitoExtension.class)
public class AsyncMailServiceUnitTest {

    @Mock
    private JavaMailSender javaMailSender;

    @InjectMocks
    private AsyncMailService asyncMailService;

    @BeforeEach
    void setUp() {
        // 设置私有字段值
        ReflectionTestUtils.setField(asyncMailService, "from", "xjl20041115@126.com");
        ReflectionTestUtils.setField(asyncMailService, "senderName", "合同审查系统");
    }

    /**
     * 测试构建邮件内容 - 审查完成类型
     */
    @Test
    void testBuildEmailContent_ReviewComplete() {
        String title = "合同审查完成";
        String message = "您的合同审查已完成";

        String content = asyncMailService.buildEmailContent(
                NotificationType.REVIEW_COMPLETE,
                title,
                message
        );

        assertNotNull(content);
        assertTrue(content.contains(title));
        assertTrue(content.contains(message));
        assertTrue(content.contains("✓"));
        log.info("审查完成邮件内容：\n{}", content);
    }

    /**
     * 测试构建邮件内容 - 高风险预警类型
     */
    @Test
    void testBuildEmailContent_HighRiskWarning() {
        String title = "高风险预警";
        String message = "检测到高风险合同";

        String content = asyncMailService.buildEmailContent(
                NotificationType.HIGH_RISK_WARNING,
                title,
                message
        );

        assertNotNull(content);
        assertTrue(content.contains(title));
        assertTrue(content.contains(message));
        assertTrue(content.contains("⚠"));
        log.info("高风险预警邮件内容：\n{}", content);
    }

    /**
     * 测试构建邮件内容 - 系统公告类型
     */
    @Test
    void testBuildEmailContent_SystemAnnouncement() {
        String title = "系统更新";
        String message = "系统已更新到最新版本";

        String content = asyncMailService.buildEmailContent(
                NotificationType.SYSTEM_ANNOUNCEMENT,
                title,
                message
        );

        assertNotNull(content);
        assertTrue(content.contains(title));
        assertTrue(content.contains(message));
        assertTrue(content.contains("ℹ"));
        log.info("系统公告邮件内容：\n{}", content);
    }

    /**
     * 测试构建邮件内容 - 邮件通知类型
     */
    @Test
    void testBuildEmailContent_EmailNotification() {
        String title = "密码修改提醒";
        String message = "您的密码已修改";

        String content = asyncMailService.buildEmailContent(
                NotificationType.EMAIL_NOTIFICATION,
                title,
                message
        );

        assertNotNull(content);
        assertTrue(content.contains(title));
        assertTrue(content.contains(message));
        log.info("邮件通知内容：\n{}", content);
    }

    /**
     * 测试邮件内容包含 HTML 格式
     */
    @Test
    void testBuildEmailContent_ContainsHtml() {
        String content = asyncMailService.buildEmailContent(
                NotificationType.REVIEW_COMPLETE,
                "测试标题",
                "测试消息"
        );

        assertTrue(content.contains("<div"));
        assertTrue(content.contains("</div>"));
        assertTrue(content.contains("style="));
        log.info("HTML邮件内容验证通过");
    }

    /**
     * 测试邮件内容包含发送时间
     */
    @Test
    void testBuildEmailContent_ContainsTimestamp() {
        String content = asyncMailService.buildEmailContent(
                NotificationType.SYSTEM_ANNOUNCEMENT,
                "测试",
                "测试"
        );

        assertTrue(content.contains("发送时间:"));
        log.info("时间戳验证通过");
    }
}
