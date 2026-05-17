package com.example.contractreview.service;

import com.example.contractreview.enums.NotificationType;
import jakarta.mail.internet.MimeMessage;
import lombok.Getter;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.mail.SimpleMailMessage;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;

import jakarta.annotation.Resource;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

/**
 * 异步邮件服务
 */
@Service
@Slf4j
public class AsyncMailService {

    @Resource
    private JavaMailSender javaMailSender;

    @Value("${spring.mail.username}")
    private String from;

    @Getter
    @Value("${verify.code.expire}")
    private Integer expire;

    @Value("${app.name:合同审查系统}")
    private String senderName;
    /**
     * 异步发送验证码邮件
     *
     * @param to     收件人
     * @param code   验证码
     * @param type   验证码类型
     * @param expire 过期时间(秒)
     */
    @Async("verifyCodeExecutor")
    public void sendVerifyCodeMailAsync(String to, String code, String type, Integer expire) {
        String typeName = switch (type) {
            case "register" -> "注册";
            case "login" -> "登录";
            case "resetPassword" -> "忘记密码";
            default -> "验证";
        };

        long startTime = System.currentTimeMillis();
        try {
            MimeMessage mimeMessage = javaMailSender.createMimeMessage();
            MimeMessageHelper helper = new MimeMessageHelper(mimeMessage, true, "UTF-8");

            helper.setFrom(from, senderName);
            helper.setTo(to);
            helper.setSubject("【" + senderName + "】" + typeName + "验证码");
            helper.setText(buildEmailContent(typeName, code, expire), true);

            javaMailSender.send(mimeMessage);
            log.info("异步发送验证码邮件成功, 耗时{}ms, 收件人:{}", System.currentTimeMillis() - startTime, to);
        } catch (Exception e) {
            log.error("异步发送验证码邮件失败, 耗时{}ms, 收件人:{}, 错误:{}",
                    System.currentTimeMillis() - startTime, to, e.getMessage());
        }
    }

    /**
     * 构建验证码邮件内容（HTML格式）
     */
    private String buildEmailContent(String typeName, String code, Integer expire) {
        String time = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));

        return String.format(
                "<div style=\"font-family: 'Microsoft YaHei', Arial, sans-serif; max-width: 600px; margin: 0 auto; background: #ffffff;\">" +
                        "<div style=\"background: #1e3a5f; padding: 30px; text-align: center; border-bottom: 4px solid #c9a227;\">" +
                        "<h1 style=\"color: #ffffff; margin: 0; font-size: 24px; font-weight: 600; letter-spacing: 2px;\">智能合同审查助手</h1>" +
                        "<p style=\"color: #c9a227; margin: 10px 0 0 0; font-size: 14px; font-weight: 500;\">企业法务合规 AI 系统</p>" +
                        "</div>" +
                        "<div style=\"padding: 40px 30px;\">" +
                        "<h2 style=\"color: #1e3a5f; margin: 0 0 20px 0; font-size: 20px; font-weight: 600; border-left: 4px solid #c9a227; padding-left: 12px;\">%s验证码</h2>" +
                        "<p style=\"color: #666666; font-size: 14px; line-height: 1.6; margin: 0 0 30px 0;\">" +
                        "您正在进行<span style=\"color: #1e3a5f; font-weight: bold;\">%s</span>操作，请使用以下验证码完成验证：" +
                        "</p>" +
                        "<div style=\"background: #f8f9fa; border-left: 4px solid #1e3a5f; padding: 20px; margin: 20px 0; text-align: center;\">" +
                        "<p style=\"font-size: 32px; font-weight: bold; color: #1e3a5f; margin: 0; letter-spacing: 8px;\">%s</p>" +
                        "</div>" +
                        "<p style=\"color: #999999; font-size: 13px; margin: 20px 0;\">" +
                        "⏰ 验证码将于 <strong style=\"color: #c9a227;\">%d秒</strong> 后过期，请尽快使用" +
                        "</p>" +
                        "<div style=\"background: #f5f5f5; border: 1px solid #e0e0e0; border-radius: 6px; padding: 15px; margin: 20px 0;\">" +
                        "<p style=\"color: #666666; font-size: 13px; margin: 0;\">" +
                        "⚠️ 安全提示：请勿将验证码泄露给他人，如非本人操作请忽略此邮件。" +
                        "</p>" +
                        "</div>" +
                        "</div>" +
                        "<div style=\"background: #1e3a5f; padding: 20px; text-align: center;\">" +
                        "<p style=\"color: #ffffff; font-size: 12px; margin: 0;\">" +
                        "此邮件由 %s 自动发送，请勿回复<br>" +
                        "发送时间：%s" +
                        "</p>" +
                        "</div>" +
                        "</div>",
                typeName, typeName, code, expire, senderName, time
        );
    }

    /**
     * 发送通知邮件
     */
    @Async("emailTaskExecutor")
    public void sendNotificationEmail(String toEmail, NotificationType type, String title, String message) {
        try {
            MimeMessage mimeMessage = javaMailSender.createMimeMessage();
            MimeMessageHelper helper = new MimeMessageHelper(mimeMessage, true, "UTF-8");

            helper.setFrom(from, senderName);
            helper.setTo(toEmail);
            helper.setSubject("【" + senderName + "】" + title);
            helper.setText(buildEmailContent(type, title, message), true);

            javaMailSender.send(mimeMessage);
            log.info("邮件发送成功 - 收件人: {}, 主题: {}", toEmail, title);

        } catch (Exception e) {
            log.error("邮件发送失败 - 收件人: {}, 错误: {}", toEmail, e.getMessage(), e);
        }
    }

    /**
     * 构建邮件内容
     */
    public String buildEmailContent(NotificationType type, String title, String message) {
        String time = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));

        String headerColor;
        String icon = switch (type) {
            case REVIEW_COMPLETE -> {
                headerColor = "#67C23A";
                yield "✓";
            }
            case HIGH_RISK_WARNING -> {
                headerColor = "#E6A23C";
                yield "⚠";
            }
            default -> {
                headerColor = "#409EFF";
                yield "ℹ";
            }
        };

        return String.format(
                "<div style=\"font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;\">" +
                        "<h2 style=\"color: %s;\">%s %s</h2>" +
                        "<div style=\"background: #f5f7fa; padding: 20px; border-radius: 8px;\">" +
                        "<h3>%s</h3>" +
                        "<p>%s</p>" +
                        "</div>" +
                        "<p style=\"color: #909399; font-size: 12px; margin-top: 20px;\">" +
                        "此邮件由%s自动发送，请勿回复。<br>" +
                        "发送时间: %s" +
                        "</p>" +
                        "</div>",
                headerColor, icon, type.getDescription(),
                title, message,
                senderName, time
        );
    }
}
