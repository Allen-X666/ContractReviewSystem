package com.example.contractreview.service;

import com.example.contractreview.model.vo.fastapi.LawReferenceVO;
import com.example.contractreview.model.vo.fastapi.ReviewResultVO;
import com.example.contractreview.model.vo.fastapi.RiskItemVO;
import freemarker.template.Configuration;
import freemarker.template.Template;
import freemarker.template.TemplateExceptionHandler;
import jakarta.annotation.PostConstruct;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.Resource;
import org.springframework.stereotype.Service;

import java.io.ByteArrayOutputStream;
import java.io.StringReader;
import java.io.StringWriter;
import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;

/**
 * PDF 报告生成服务
 * 使用 FreeMarker + iText 将模板转换为 PDF
 */
@Slf4j
@Service
public class PdfReportService {

    @Value("classpath:templates/report/contract-review-report.ftl")
    private Resource reportTemplateResource;

    private Configuration freemarkerConfig;

    @PostConstruct
    public void init() {
        // 初始化 FreeMarker 配置
        freemarkerConfig = new Configuration(Configuration.VERSION_2_3_31);
        freemarkerConfig.setDefaultEncoding("UTF-8");
        freemarkerConfig.setTemplateExceptionHandler(TemplateExceptionHandler.RETHROW_HANDLER);
        freemarkerConfig.setLogTemplateExceptions(false);
        freemarkerConfig.setWrapUncheckedExceptions(true);
    }

    /**
     * 生成合同审查报告 PDF
     *
     * @param contractName   合同名称
     * @param reviewId       审查ID
     * @param reviewResult   审查结果
     * @return PDF 文件字节数组
     */
    public byte[] generateReviewReport(
            String contractName,
            Long reviewId,
            ReviewResultVO reviewResult) {
        try {
            // 1. 读取 FTL 模板
            String ftlTemplate = readTemplate();

            // 2. 准备数据模型
            Map<String, Object> dataModel = prepareDataModel(contractName, reviewId, reviewResult);

            // 3. 使用 FreeMarker 渲染模板
            String htmlContent = renderTemplate(ftlTemplate, dataModel);

            // 4. 使用 iText 将 HTML 转换为 PDF
            return convertHtmlToPdf(htmlContent);

        } catch (Exception e) {
            log.error("生成 PDF 报告失败: {}", e.getMessage(), e);
            throw new RuntimeException("生成 PDF 报告失败: " + e.getMessage(), e);
        }
    }

    /**
     * 读取模板文件
     */
    private String readTemplate() throws Exception {
        return new String(reportTemplateResource.getInputStream().readAllBytes(), StandardCharsets.UTF_8);
    }

    /**
     * 准备 FreeMarker 数据模型
     */
    private Map<String, Object> prepareDataModel(
            String contractName,
            Long reviewId,
            ReviewResultVO reviewResult) {

        Map<String, Object> dataModel = new HashMap<>();
        log.info("准备数据模型:,合同名称：{}", contractName);
        // 封面信息
        dataModel.put("title", "合同审查报告");
        dataModel.put("contractName", contractName != null ? contractName : "未命名合同");
        dataModel.put("reviewId", "REV-" + String.format("%06d", reviewId));
        dataModel.put("completedAt", LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy年MM月dd日")));
        dataModel.put("reviewAgency", "智能合同审查系统");
        dataModel.put("generatedAt", LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy年MM月dd日 HH:mm:ss")));
        log.info("准备数据模型:{}", dataModel);
        // 评分信息
        int overallScore = reviewResult != null && reviewResult.getOverallScore() != null
                ? reviewResult.getOverallScore() : 0;
        dataModel.put("overallScore", overallScore);
        dataModel.put("assessmentText", getScoreAssessment(overallScore));
        dataModel.put("assessmentClass", getScoreClass(overallScore));

        // 风险统计
        Map<String, Integer> riskSummary = reviewResult != null && reviewResult.getRiskSummary() != null
                ? reviewResult.getRiskSummary() : new HashMap<>();
        int highRisk = riskSummary.getOrDefault("high", 0);
        int mediumRisk = riskSummary.getOrDefault("medium", 0);
        int lowRisk = riskSummary.getOrDefault("low", 0);
        int noRisk = riskSummary.getOrDefault("none", 0);

        // 计算总条款数和占比
        int totalClauses = highRisk + mediumRisk + lowRisk + noRisk;
        if (totalClauses == 0) {
            totalClauses = highRisk + mediumRisk + lowRisk;
            if (totalClauses == 0) totalClauses = 1;
        }

        int totalRisks = highRisk + mediumRisk + lowRisk;
        dataModel.put("totalRisks", totalRisks);
        dataModel.put("highRiskCount", highRisk);
        dataModel.put("mediumRiskCount", mediumRisk);
        dataModel.put("lowRiskCount", lowRisk);
        dataModel.put("noRiskCount", noRisk);

        // 计算百分比
        dataModel.put("highRiskPercent", String.valueOf(Math.round(highRisk * 100.0 / totalClauses)));
        dataModel.put("mediumRiskPercent", String.valueOf(Math.round(mediumRisk * 100.0 / totalClauses)));
        dataModel.put("lowRiskPercent", String.valueOf(Math.round(lowRisk * 100.0 / totalClauses)));
        dataModel.put("noRiskPercent", String.valueOf(Math.round(noRisk * 100.0 / totalClauses)));

        // 计算饼图坐标点（用于SVG渲染）
        if (totalRisks > 0) {
            double centerX = 100;
            double centerY = 100;
            double radius = 80;

            // 高风险角度和坐标
            double highAngle = highRisk * 360.0 / totalRisks;
            double highRad = Math.toRadians(highAngle);
            dataModel.put("highEndX", String.valueOf(centerX + radius * Math.sin(highRad)));
            dataModel.put("highEndY", String.valueOf(centerY - radius * Math.cos(highRad)));
            dataModel.put("highLargeArc", highAngle > 180 ? "1" : "0");

            // 中风险起始和结束坐标
            double mediumStartAngle = highAngle;
            double mediumAngle = mediumRisk * 360.0 / totalRisks;
            double mediumEndAngle = mediumStartAngle + mediumAngle;
            double mediumStartRad = Math.toRadians(mediumStartAngle);
            double mediumEndRad = Math.toRadians(mediumEndAngle);
            dataModel.put("mediumStartX", String.valueOf(centerX + radius * Math.sin(mediumStartRad)));
            dataModel.put("mediumStartY", String.valueOf(centerY - radius * Math.cos(mediumStartRad)));
            dataModel.put("mediumEndX", String.valueOf(centerX + radius * Math.sin(mediumEndRad)));
            dataModel.put("mediumEndY", String.valueOf(centerY - radius * Math.cos(mediumEndRad)));
            dataModel.put("mediumLargeArc", mediumAngle > 180 ? "1" : "0");

            // 低风险起始和结束坐标
            double lowStartAngle = mediumEndAngle;
            double lowAngle = lowRisk * 360.0 / totalRisks;
            double lowEndAngle = lowStartAngle + lowAngle;
            double lowStartRad = Math.toRadians(lowStartAngle);
            double lowEndRad = Math.toRadians(lowEndAngle);
            dataModel.put("lowStartX", String.valueOf(centerX + radius * Math.sin(lowStartRad)));
            dataModel.put("lowStartY", String.valueOf(centerY - radius * Math.cos(lowStartRad)));
            dataModel.put("lowEndX", String.valueOf(centerX + radius * Math.sin(lowEndRad)));
            dataModel.put("lowEndY", String.valueOf(centerY - radius * Math.cos(lowEndRad)));
            dataModel.put("lowLargeArc", lowAngle > 180 ? "1" : "0");

            // 无风险起始坐标
            double noStartAngle = lowEndAngle;
            double noAngle = noRisk * 360.0 / totalRisks;
            double noStartRad = Math.toRadians(noStartAngle);
            dataModel.put("noStartX", String.valueOf(centerX + radius * Math.sin(noStartRad)));
            dataModel.put("noStartY", String.valueOf(centerY - radius * Math.cos(noStartRad)));
            dataModel.put("noLargeArc", noAngle > 180 ? "1" : "0");
        }

        // 审查结论
        String conclusion = reviewResult != null && reviewResult.getConclusion() != null
                ? reviewResult.getConclusion() : "经系统审查，本合同暂未发现明显风险点。";
        dataModel.put("conclusion", conclusion);

        // 风险列表和所有法条汇总（单次遍历优化）
        List<RiskItemVO> riskItems = reviewResult != null ? reviewResult.getRisks() : null;
        List<Map<String, Object>> risks = convertRisks(riskItems);
        dataModel.put("risks", risks);
        dataModel.put("sortedRisks", risks);
        dataModel.put("uniqueLaws", collectUniqueLaws(riskItems));

        return dataModel;
    }

    private List<Map<String, Object>> convertRisks(List<RiskItemVO> riskItems) {
        List<Map<String, Object>> risks = new ArrayList<>();

        if (riskItems == null || riskItems.isEmpty()) {
            return risks;
        }

        for (RiskItemVO risk : riskItems) {
            Map<String, Object> riskMap = new HashMap<>();
            String level = risk.getLevel() != null ? risk.getLevel().toLowerCase() : "medium";

            riskMap.put("level", level);
            riskMap.put("levelText", getLevelText(level));
            riskMap.put("priorityText", getPriorityText(level));
            riskMap.put("clause", risk.getClause() != null ? risk.getClause() : "未命名条款");
            riskMap.put("locationText", risk.getLocation() != null && risk.getLocation().getText() != null
                    ? risk.getLocation().getText() : "");
            riskMap.put("description", risk.getDescription() != null ? risk.getDescription() : "");
            riskMap.put("suggestion", risk.getSuggestion() != null ? risk.getSuggestion() : "");

            // 相关法条
            List<Map<String, Object>> lawReferences = new ArrayList<>();
            if (risk.getLawReferences() != null) {
                for (LawReferenceVO law : risk.getLawReferences()) {
                    Map<String, Object> lawMap = new HashMap<>();
                    lawMap.put("name", law.getName() != null ? law.getName() : "未知法规");
                    lawMap.put("content", law.getContent() != null ? law.getContent() : "");
                    lawMap.put("interpretation", law.getInterpretation() != null ? law.getInterpretation() : "");
                    lawReferences.add(lawMap);
                }
            }
            riskMap.put("lawReferences", lawReferences);

            risks.add(riskMap);
        }

        return risks;
    }

    private List<Map<String, Object>> collectUniqueLaws(List<RiskItemVO> riskItems) {
        List<Map<String, Object>> uniqueLaws = new ArrayList<>();
        if (riskItems == null) return uniqueLaws;

        Set<String> uniqueKeys = new HashSet<>();
        for (RiskItemVO risk : riskItems) {
            if (risk.getLawReferences() != null) {
                for (LawReferenceVO law : risk.getLawReferences()) {
                    String name = law.getName() != null ? law.getName() : "未知法规";
                    String article = law.getArticle() != null ? law.getArticle() : "";
                    String key = name + "-" + article;
                    if (!uniqueKeys.contains(key)) {
                        uniqueKeys.add(key);
                        Map<String, Object> lawMap = new HashMap<>();
                        lawMap.put("name", name);
                        lawMap.put("article", article);
                        lawMap.put("content", law.getContent() != null ? law.getContent() : "");
                        lawMap.put("citationCount", 1);
                        uniqueLaws.add(lawMap);
                    } else {
                        // 增加引用次数
                        for (Map<String, Object> existingLaw : uniqueLaws) {
                            if (name.equals(existingLaw.get("name")) && article.equals(existingLaw.get("article"))) {
                                int count = (int) existingLaw.getOrDefault("citationCount", 1);
                                existingLaw.put("citationCount", count + 1);
                                break;
                            }
                        }
                    }
                }
            }
        }
        return uniqueLaws;
    }

    /**
     * 使用 FreeMarker 渲染模板
     */
    private String renderTemplate(String ftlTemplate, Map<String, Object> dataModel) throws Exception {
        Template template = new Template("report", new StringReader(ftlTemplate), freemarkerConfig);
        StringWriter writer = new StringWriter();
        template.process(dataModel, writer);
        return writer.toString();
    }

    /**
     * 将 HTML 转换为 PDF（支持中文）
     */
    private byte[] convertHtmlToPdf(String htmlContent) throws Exception {
        ByteArrayOutputStream outputStream = new ByteArrayOutputStream();

        try {
            // 清理 HTML 中可能导致 iText 崩溃的 CSS
            htmlContent = cleanHtmlForItext(htmlContent);

            // 配置中文字体
            com.itextpdf.layout.font.FontProvider fontProvider = new com.itextpdf.layout.font.FontProvider();

            // 尝试加载系统自带的中文字体
            String[] chineseFonts = {
                    "C:/Windows/Fonts/simhei.ttf",      // 黑体
                    "C:/Windows/Fonts/simsun.ttc",      // 宋体
                    "C:/Windows/Fonts/simkai.ttf",      // 楷体
                    "C:/Windows/Fonts/msyh.ttc",        // 微软雅黑
                    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",  // Linux 文泉驿
                    "/System/Library/Fonts/PingFang.ttc",            // Mac 苹方
                    "/System/Library/Fonts/STHeiti Light.ttc"        // Mac 黑体
            };

            boolean fontLoaded = false;
            for (String fontPath : chineseFonts) {
                try {
                    java.io.File fontFile = new java.io.File(fontPath);
                    if (fontFile.exists()) {
                        fontProvider.addFont(fontPath);
                        fontLoaded = true;
                        log.info("成功加载中文字体: {}", fontPath);
                        break;
                    }
                } catch (Exception e) {
                    log.debug("字体加载失败: {} - {}", fontPath, e.getMessage());
                }
            }

            if (!fontLoaded) {
                log.warn("未找到中文字体，PDF 中文可能显示为方框");
            }

            // 配置转换属性 - 禁用边距折叠避免空指针
            com.itextpdf.html2pdf.ConverterProperties properties = new com.itextpdf.html2pdf.ConverterProperties()
                    .setBaseUri("http://localhost:8080")
                    .setFontProvider(fontProvider);

            // 使用 iText 转换 HTML 为 PDF
            com.itextpdf.html2pdf.HtmlConverter.convertToPdf(htmlContent, outputStream, properties);

            return outputStream.toByteArray();
            
        } catch (NullPointerException e) {
            log.error("iText 转换 PDF 时发生空指针异常，尝试使用备用方案: {}", e.getMessage());
            // 如果失败，尝试使用简化版 HTML
            return convertHtmlToPdfSimple(htmlContent);
        }
    }

    /**
     * 清理 HTML 中 iText 不兼容的 CSS
     */
    private String cleanHtmlForItext(String html) {
        if (html == null) return "";

        html = html.replaceAll("conic-gradient\\([^)]+\\)", "#e5e7eb");

        html = html.replaceAll("gap\\s*:\\s*[^;]+;", "");
        html = html.replaceAll("row-gap\\s*:\\s*[^;]+;", "");
        html = html.replaceAll("column-gap\\s*:\\s*[^;]+;", "");

        html = html.replaceAll("display\\s*:\\s*flex;", "");
        html = html.replaceAll("flex-direction\\s*:\\s*[^;]+;", "");
        html = html.replaceAll("align-items\\s*:\\s*[^;]+;", "");
        html = html.replaceAll("justify-content\\s*:\\s*[^;]+;", "");
        html = html.replaceAll("flex\\s*:\\s*[^;]+;", "");
        html = html.replaceAll("flex-wrap\\s*:\\s*[^;]+;", "");
        html = html.replaceAll("flex-shrink\\s*:\\s*[^;]+;", "");

        html = html.replaceAll("\\$[a-zA-Z-]+", "");

        return html;
    }

    /**
     * 简化版 PDF 转换（备用方案）
     */
    private byte[] convertHtmlToPdfSimple(String htmlContent) throws Exception {
        ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
        
        // 使用最基本的配置，禁用所有高级特性
        com.itextpdf.html2pdf.ConverterProperties properties = new com.itextpdf.html2pdf.ConverterProperties()
                .setBaseUri("http://localhost:8080");
        
        // 简化 HTML，移除所有样式
        String simpleHtml = "<!DOCTYPE html><html><body>"
                + htmlContent.replaceAll("<style[^>]*>.*?</style>", "")
                .replaceAll("style=\"[^\"]*\"", "")
                + "</body></html>";
        
        com.itextpdf.html2pdf.HtmlConverter.convertToPdf(simpleHtml, outputStream, properties);
        
        return outputStream.toByteArray();
    }

    /**
     * 根据评分获取评估等级
     */
    private String getScoreAssessment(int score) {
        if (score >= 80) return "优秀";
        if (score >= 60) return "合格";
        return "需改进";
    }

    /**
     * 根据评分获取 CSS 类名
     */
    private String getScoreClass(int score) {
        if (score >= 80) return "excellent";
        if (score >= 60) return "good";
        return "poor";
    }

    private String getLevelText(String level) {
        if ("high".equals(level)) return "高风险";
        if ("medium".equals(level)) return "中风险";
        if ("low".equals(level)) return "低风险";
        return "无风险";
    }

    private String getPriorityText(String level) {
        if ("high".equals(level)) return "高";
        if ("medium".equals(level)) return "中";
        if ("low".equals(level)) return "低";
        return "低";
    }
}
