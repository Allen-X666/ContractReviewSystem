package com.example.contractreview.utils;

import com.example.contractreview.enums.LawCategory;
import com.example.contractreview.enums.LawStatus;
import com.example.contractreview.model.entity.LawArticle;
import com.example.contractreview.model.entity.LawRegulation;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.time.format.DateTimeParseException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * 法律文本文件解析工具类
 * <p>
 * 读取法律文本文件，自动解析成结构化的法规实体和法条实体列表。
 * 支持单个或多个法规段落的文件，每个段落以 {@code # N、法规名称} 开头。
 * <p>
 * 文本格式要求：
 * <pre>
 * # 一、法规名称
 *
 * 发布机构：xxx
 * 类型：xxx
 * 发布时间：yyyy年M月d日
 * 生效时间：yyyy年M月d日
 * 核心应用：xxx
 *
 * ## 条款内容及司法解释
 *
 * 1\. 第一条 标题
 * 法规内容：xxx
 * 司法解释：xxx
 * 相关条款：xxx
 * </pre>
 */
@Slf4j
public class LawFileParser {

    private static final DateTimeFormatter STANDARD_DATE_FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd");

    private static final Pattern CHINESE_DATE_PATTERN = Pattern.compile("(\\d{4})年(\\d{1,2})月(\\d{1,2})日");

    private static final Pattern SECTION_SPLIT_PATTERN = Pattern.compile("(?=^# [一二三四五六七八九十]+、)", Pattern.MULTILINE);

    private static final Pattern LAW_NAME_PATTERN = Pattern.compile("# [一二三四五六七八九十]+、(.*?)\\n");

    private static final Pattern ISSUER_PATTERN = Pattern.compile("发布机构：(.*?)\\n");
    private static final Pattern CATEGORY_PATTERN = Pattern.compile("类型：(.*?)\\n");
    private static final Pattern PUBLISH_DATE_PATTERN = Pattern.compile("发布时间：(.*?)\\n");
    private static final Pattern EFFECTIVE_DATE_PATTERN = Pattern.compile("生效时间：(.*?)\\n");
    private static final Pattern DESCRIPTION_PATTERN = Pattern.compile("核心应用：(.*?)\\n");

    private static final Pattern ARTICLE_SPLIT_PATTERN = Pattern.compile("\\n\\d+\\\\\\. ");
    private static final Pattern ARTICLE_NO_PATTERN = Pattern.compile("^(\\d+) ");

    /**
     * 解析法律文本文件（支持多法规段落）
     *
     * @param filePath 文件路径
     * @return 解析结果列表，每个元素对应文件中的一个法规段落
     * @throws IOException              文件读取异常
     * @throws IllegalArgumentException 文件格式不合法
     */
    public static List<ParseResult> parseAll(Path filePath) throws IOException {
        String content = Files.readString(filePath, StandardCharsets.UTF_8);
        return parseAll(content);
    }

    /**
     * 解析MultipartFile（支持多法规段落）
     *
     * @param file 上传的文件
     * @return 解析结果列表，每个元素对应文件中的一个法规段落
     * @throws IOException              文件读取异常
     * @throws IllegalArgumentException 文件格式不合法或文件为空
     */
    public static List<ParseResult> parseAll(MultipartFile file) throws IOException {
        if (file == null || file.isEmpty()) {
            throw new IllegalArgumentException("上传的文件不能为空");
        }
        String content = new String(file.getBytes(), StandardCharsets.UTF_8);
        return parseAll(content);
    }

    /**
     * 解析法律文本内容（支持多法规段落）
     *
     * @param content 文本内容
     * @return 解析结果列表，每个元素对应文本中的一个法规段落
     * @throws IllegalArgumentException 文本格式不合法
     */
    public static List<ParseResult> parseAll(String content) {
        if (content == null || content.isBlank()) {
            throw new IllegalArgumentException("法律文本内容不能为空");
        }

        String[] sections = SECTION_SPLIT_PATTERN.split(content);
        List<ParseResult> results = new ArrayList<>();

        for (String section : sections) {
            String trimmed = section.trim();
            if (trimmed.isEmpty() || !LAW_NAME_PATTERN.matcher(trimmed).find()) {
                continue;
            }

            LawRegulation regulation = parseRegulation(trimmed);
            List<LawArticle> articles = parseArticles(trimmed);

            log.info("解析完成，法规：{}，条款数量：{}", regulation.getName(), articles.size());
            results.add(new ParseResult(regulation, articles));
        }

        if (results.isEmpty()) {
            throw new IllegalArgumentException("未找到任何法规段落，请检查文件格式");
        }

        return results;
    }

    /**
     * 解析法律文本文件（单法规段落，兼容旧接口）
     *
     * @param filePath 文件路径
     * @return 解析结果
     * @throws IOException              文件读取异常
     * @throws IllegalArgumentException 文件格式不合法
     */
    public static ParseResult parse(Path filePath) throws IOException {
        String content = Files.readString(filePath, StandardCharsets.UTF_8);
        return parse(content);
    }

    /**
     * 解析MultipartFile（单法规段落，兼容旧接口）
     *
     * @param file 上传的文件
     * @return 解析结果
     * @throws IOException              文件读取异常
     * @throws IllegalArgumentException 文件格式不合法或文件为空
     */
    public static ParseResult parse(MultipartFile file) throws IOException {
        List<ParseResult> results = parseAll(file);
        return results.get(0);
    }

    /**
     * 解析法律文本内容（单法规段落，兼容旧接口）
     *
     * @param content 文本内容
     * @return 解析结果
     * @throws IllegalArgumentException 文本格式不合法
     */
    public static ParseResult parse(String content) {
        List<ParseResult> results = parseAll(content);
        return results.get(0);
    }

    /**
     * 解析法规基本信息
     */
    private static LawRegulation parseRegulation(String section) {
        String lawName = extractGroup(LAW_NAME_PATTERN, section);
        if (lawName == null) {
            throw new IllegalArgumentException("无法找到法规名称，请检查文件格式是否包含 '# N、法规名称'");
        }

        String issuer = extractGroup(ISSUER_PATTERN, section);
        String categoryStr = extractGroup(CATEGORY_PATTERN, section);
        String publishDateStr = extractGroup(PUBLISH_DATE_PATTERN, section);
        String effectiveDateStr = extractGroup(EFFECTIVE_DATE_PATTERN, section);
        String description = extractGroup(DESCRIPTION_PATTERN, section);

        return LawRegulation.builder()
                .name(lawName.trim())
                .category(parseCategory(categoryStr))
                .issuer(issuer != null ? issuer.trim() : "")
                .publishDate(parseDate(publishDateStr))
                .effectiveDate(parseDate(effectiveDateStr))
                .status(LawStatus.EFFECTIVE)
                .description(description != null ? description.trim() : "")
                .isNew(true)
                .createdAt(LocalDateTime.now())
                .build();
    }

    /**
     * 解析法条列表
     */
    private static List<LawArticle> parseArticles(String section) {
        String[] blocks = ARTICLE_SPLIT_PATTERN.split(section);
        List<LawArticle> articles = new ArrayList<>();

        for (int i = 1; i < blocks.length; i++) {
            String block = blocks[i].trim();
            if (block.isEmpty()) {
                continue;
            }

            LawArticle article = parseArticleBlock(block, i);
            if (article != null) {
                articles.add(article);
            }
        }

        return articles;
    }

    /**
     * 解析单个法条块
     * <p>
     * 解析规则：
     * - articleNo: 从"相关条款："提取，如"民法典合同编第四百六十三条"
     * - title: 从第一行提取，去掉"第一条"等序号前缀，如"立法目的"
     * - content: 法规内容
     * - interpretation: 司法解释
     */
    private static LawArticle parseArticleBlock(String block, int index) {
        String[] lines = block.split("\\n");
        if (lines.length == 0) {
            return null;
        }

        // 解析第一行获取 title（去掉序号前缀）
        String firstLine = lines[0].trim();
        String title = parseTitle(firstLine);

        // 从"相关条款："提取 articleNo
        String articleNo = extractRelatedLaw(block);
        if (articleNo == null || articleNo.isBlank()) {
            // 如果未找到相关条款，使用序号作为 fallback
            Matcher noMatcher = ARTICLE_NO_PATTERN.matcher(firstLine);
            articleNo = noMatcher.find() ? noMatcher.group(1) : String.valueOf(index);
        }

        String articleContent = extractBetween(block, "法规内容：", "司法解释：");
        String interpretation = extractBetween(block, "司法解释：", "相关条款：");

        return LawArticle.builder()
                .articleNo(articleNo)
                .title(title)
                .content(articleContent)
                .interpretation(interpretation)
                .createdAt(LocalDateTime.now())
                .build();
    }

    /**
     * 从第一行解析 title，去掉序号前缀
     * 例如："第一条 立法目的" -> "立法目的"
     */
    private static String parseTitle(String firstLine) {
        // 匹配 "第X条" 或数字开头的序号
        Pattern titlePattern = Pattern.compile("^(\\d+|第[一二三四五六七八九十百千]+条)\\s*");
        Matcher matcher = titlePattern.matcher(firstLine);
        if (matcher.find()) {
            return firstLine.substring(matcher.end()).trim();
        }
        return firstLine;
    }

    /**
     * 从"相关条款："提取关联法条作为 articleNo
     * 例如："相关条款：民法典合同编第四百六十三条" -> "民法典合同编第四百六十三条"
     */
    private static String extractRelatedLaw(String block) {
        Pattern relatedLawPattern = Pattern.compile("相关条款：(.*?)($|\\n)");
        Matcher matcher = relatedLawPattern.matcher(block);
        if (matcher.find()) {
            return matcher.group(1).trim();
        }
        return null;
    }

    /**
     * 提取正则匹配的第一个分组
     */
    private static String extractGroup(Pattern pattern, String content) {
        Matcher matcher = pattern.matcher(content);
        return matcher.find() ? matcher.group(1) : null;
    }

    /**
     * 提取两个标记之间的文本
     */
    private static String extractBetween(String text, String startMarker, String endMarker) {
        int startIdx = text.indexOf(startMarker);
        if (startIdx < 0) {
            return "";
        }
        startIdx += startMarker.length();

        int endIdx = endMarker != null ? text.indexOf(endMarker, startIdx) : -1;
        if (endIdx < 0) {
            return text.substring(startIdx).trim();
        }
        return text.substring(startIdx, endIdx).trim();
    }

    /**
     * 解析分类字符串为枚举
     * 支持枚举code（如 "civil"）和中文描述（如 "民法"）两种匹配方式
     */
    static LawCategory parseCategory(String categoryStr) {
        if (categoryStr == null || categoryStr.isBlank()) {
            return null;
        }
        String trimmed = categoryStr.trim();
        LawCategory byCode = LawCategory.getByCode(trimmed);
        if (byCode != null) {
            return byCode;
        }
        for (LawCategory category : LawCategory.values()) {
            if (category.getDescription().equals(trimmed)) {
                return category;
            }
        }
        log.debug("无法匹配法规分类：{}，将返回null", trimmed);
        return null;
    }

    /**
     * 解析日期字符串为LocalDate
     * 支持 "yyyy-MM-dd" 和 "yyyy年M月d日" 两种格式
     */
    static LocalDate parseDate(String dateStr) {
        if (dateStr == null || dateStr.isBlank()) {
            return null;
        }
        String trimmed = dateStr.trim();

        try {
            return LocalDate.parse(trimmed, STANDARD_DATE_FORMATTER);
        } catch (DateTimeParseException ignored) {
        }

        Matcher matcher = CHINESE_DATE_PATTERN.matcher(trimmed);
        if (matcher.find()) {
            int year = Integer.parseInt(matcher.group(1));
            int month = Integer.parseInt(matcher.group(2));
            int day = Integer.parseInt(matcher.group(3));
            return LocalDate.of(year, month, day);
        }

        log.debug("日期解析失败：{}", trimmed);
        return null;
    }

    /**
     * 解析结果
     */
    public static class ParseResult {

        private final LawRegulation lawRegulation;
        private final List<LawArticle> lawArticles;

        public ParseResult(LawRegulation lawRegulation, List<LawArticle> lawArticles) {
            this.lawRegulation = lawRegulation;
            this.lawArticles = lawArticles;
        }

        public LawRegulation getLawRegulation() {
            return lawRegulation;
        }

        public List<LawArticle> getLawArticles() {
            return lawArticles;
        }

        /**
         * 转换为Map结构（兼容旧接口）
         */
        public Map<String, Object> toMap() {
            Map<String, Object> map = new HashMap<>();
            map.put("law_regulation", List.of(lawRegulation));
            map.put("law_article", lawArticles);
            return map;
        }
    }
}
