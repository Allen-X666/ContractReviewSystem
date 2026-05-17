package com.example.contractreview.service;

import com.example.contractreview.enums.NotificationType;
import lombok.extern.slf4j.Slf4j;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;

import java.util.concurrent.TimeUnit;

/**
 * AsyncMailService 测试类
 */
@Slf4j
@SpringBootTest
public class AsyncMailServiceTest {

    @Autowired
    private AsyncMailService asyncMailService;

    /**
     * 测试发送审查完成通知邮件
     */
    @Test
    public void testSendReviewCompleteEmail() throws InterruptedException {
        String toEmail = "xjl20041115@126.com";
        String title = "合同审查完成";
        String message = "您的合同《采购合同-2024001》审查已完成，综合评分：85分。共发现 3 个风险项，其中高风险 1 个，中风险 2 个。点击查看详情。";

        log.info("开始发送审查完成邮件...");
        asyncMailService.sendNotificationEmail(toEmail, NotificationType.REVIEW_COMPLETE, title, message);

        // 等待异步执行完成
        TimeUnit.SECONDS.sleep(3);
        log.info("审查完成邮件发送测试结束");
    }

    /**
     * 测试发送高风险预警邮件
     */
    @Test
    public void testSendHighRiskWarningEmail() throws InterruptedException {
        String toEmail = "user@example.com";
        String title = "高风险合同预警";
        String message = "检测到高风险合同《租赁合同-2024002》，存在 5 个高风险项，包括：违约责任条款不明确、租金支付方式存在漏洞等。建议立即查看并修改。";

        log.info("开始发送高风险预警邮件...");
        asyncMailService.sendNotificationEmail(toEmail, NotificationType.HIGH_RISK_WARNING, title, message);

        // 等待异步执行完成
        TimeUnit.SECONDS.sleep(3);
        log.info("高风险预警邮件发送测试结束");
    }

    /**
     * 测试发送系统公告邮件
     */
    @Test
    public void testSendSystemAnnouncementEmail() throws InterruptedException {
        String toEmail = "user@example.com";
        String title = "系统功能更新通知";
        String message = "尊敬的用户，系统已完成版本更新（v2.1.0）。新增功能：1. 支持批量合同审查；2. 优化风险识别算法；3. 新增合同模板库。欢迎体验！";

        log.info("开始发送系统公告邮件...");
        asyncMailService.sendNotificationEmail(toEmail, NotificationType.SYSTEM_ANNOUNCEMENT, title, message);

        // 等待异步执行完成
        TimeUnit.SECONDS.sleep(3);
        log.info("系统公告邮件发送测试结束");
    }

    /**
     * 测试发送邮件通知
     */
    @Test
    public void testSendEmailNotification() throws InterruptedException {
        String toEmail = "user@example.com";
        String title = "密码修改提醒";
        String message = "您的账户密码已于 2026-05-16 14:30:00 修改。如非本人操作，请立即联系管理员。";

        log.info("开始发送邮件通知...");
        asyncMailService.sendNotificationEmail(toEmail, NotificationType.EMAIL_NOTIFICATION, title, message);

        // 等待异步执行完成
        TimeUnit.SECONDS.sleep(3);
        log.info("邮件通知发送测试结束");
    }

    /**
     * 测试批量发送不同类型邮件
     */
    @Test
    public void testSendMultipleEmails() throws InterruptedException {
        String toEmail = "user@example.com";

        log.info("开始批量发送邮件测试...");

        // 发送审查完成邮件
        asyncMailService.sendNotificationEmail(
                toEmail,
                NotificationType.REVIEW_COMPLETE,
                "合同审查完成通知",
                "合同《服务协议-2024003》审查完成，评分：92分，无高风险项。"
        );

        // 发送高风险预警邮件
        asyncMailService.sendNotificationEmail(
                toEmail,
                NotificationType.HIGH_RISK_WARNING,
                "⚠️ 紧急：高风险合同预警",
                "合同《保密协议-2024004》检测到 8 个高风险项，请立即处理！"
        );

        // 发送系统公告邮件
        asyncMailService.sendNotificationEmail(
                toEmail,
                NotificationType.SYSTEM_ANNOUNCEMENT,
                "系统维护通知",
                "系统将于今晚 22:00-24:00 进行例行维护，期间服务可能不可用。"
        );

        // 等待所有异步任务完成
        TimeUnit.SECONDS.sleep(5);
        log.info("批量邮件发送测试结束");
    }

    /**
     * 测试邮件内容构建
     */
    @Test
    public void testBuildEmailContent() {
        String title = "测试邮件标题";
        String message = "这是一封测试邮件的内容。";

        // 测试审查完成类型的邮件内容
        String reviewContent = asyncMailService.buildEmailContent(
                NotificationType.REVIEW_COMPLETE,
                title,
                message
        );
        log.info("审查完成邮件内容：\n{}", reviewContent);

        // 测试高风险预警类型的邮件内容
        String warningContent = asyncMailService.buildEmailContent(
                NotificationType.HIGH_RISK_WARNING,
                title,
                message
        );
        log.info("高风险预警邮件内容：\n{}", warningContent);

        // 测试系统公告类型的邮件内容
        String announcementContent = asyncMailService.buildEmailContent(
                NotificationType.SYSTEM_ANNOUNCEMENT,
                title,
                message
        );
        log.info("系统公告邮件内容：\n{}", announcementContent);
    }
}
