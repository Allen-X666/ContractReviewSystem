package com.example.contractreview.utils;

import com.example.contractreview.enums.LawCategory;
import com.example.contractreview.enums.LawStatus;
import com.example.contractreview.model.entity.LawArticle;
import com.example.contractreview.model.entity.LawRegulation;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import lombok.extern.slf4j.Slf4j;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.nio.file.Path;
import java.time.LocalDate;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import static org.junit.jupiter.api.Assertions.*;

@Slf4j
@DisplayName("法律文本文件解析工具测试")
class LawFileParserTest {

    private static final Path REAL_FILE_PATH = Path.of(
            "E:\\Professional\\合同审查agent\\合同审查\\documents\\相关法规及对应司法解释.md"
    );

    @Nested
    @DisplayName("parseAll - 多法规段落解析")
    class ParseAllTests {

        @Test
        @DisplayName("全量输出解析结果（含所有法规元信息和法条完整内容）")
        void parseAll_fullOutput() throws IOException {
            List<LawFileParser.ParseResult> results = LawFileParser.parseAll(REAL_FILE_PATH);

            ObjectMapper mapper = new ObjectMapper()
                    .registerModule(new JavaTimeModule())
                    .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);

            List<Map<String, Object>> jsonOutput = results.stream().map(r -> {
                LawRegulation reg = r.getLawRegulation();
                Map<String, Object> regulationMap = new LinkedHashMap<>();
                regulationMap.put("name", reg.getName());
                regulationMap.put("issuer", reg.getIssuer());
                regulationMap.put("category", reg.getCategory() != null ? reg.getCategory().name() : null);
                regulationMap.put("categoryDesc", reg.getCategory() != null ? reg.getCategory().getDescription() : null);
                regulationMap.put("publishDate", reg.getPublishDate());
                regulationMap.put("effectiveDate", reg.getEffectiveDate());
                regulationMap.put("status", reg.getStatus());
                regulationMap.put("isNew", reg.getIsNew());
                regulationMap.put("description", reg.getDescription());

                List<Map<String, Object>> articleList = r.getLawArticles().stream().map(a -> {
                    Map<String, Object> articleMap = new LinkedHashMap<>();
                    articleMap.put("articleNo", a.getArticleNo());
                    articleMap.put("title", a.getTitle());
                    articleMap.put("content", a.getContent());
                    articleMap.put("interpretation", a.getInterpretation());
                    articleMap.put("createdAt", a.getCreatedAt());
                    return articleMap;
                }).collect(Collectors.toList());

                Map<String, Object> item = new LinkedHashMap<>();
                item.put("regulation", regulationMap);
                item.put("articles", articleList);
                return item;
            }).collect(Collectors.toList());

            String json = mapper.writerWithDefaultPrettyPrinter().writeValueAsString(jsonOutput);
            log.info("解析结果JSON：\n{}", json);

            assertFalse(results.isEmpty(), "解析结果不应为空");
            System.out.println("=".repeat(80));
            System.out.println("解析文件：" + REAL_FILE_PATH.toAbsolutePath());
            System.out.println("共解析到 " + results.size() + " 个法规段落");
            System.out.println("=".repeat(80));

            for (int i = 0; i < results.size(); i++) {
                LawFileParser.ParseResult result = results.get(i);
                LawRegulation reg = result.getLawRegulation();
                List<LawArticle> articles = result.getLawArticles();

                System.out.println();
                System.out.println("-".repeat(80));
                System.out.printf("【法规 %d/%d】%s%n", i + 1, results.size(), reg.getName());
                System.out.println("-".repeat(80));
                System.out.printf("  名称：%s%n", reg.getName());
                System.out.printf("  发布机构：%s%n", reg.getIssuer());
                System.out.printf("  分类：%s（%s）%n",
                        reg.getCategory() != null ? reg.getCategory().name() : "无",
                        reg.getCategory() != null ? reg.getCategory().getDescription() : "-");
                System.out.printf("  发布日期：%s%n", reg.getPublishDate());
                System.out.printf("  生效日期：%s%n", reg.getEffectiveDate());
                System.out.printf("  状态：%s%n", reg.getStatus());
                System.out.printf("  是否最新：%s%n", reg.getIsNew());
                System.out.printf("  简介：%s%n", reg.getDescription());
                System.out.println();

                for (int j = 0; j < articles.size(); j++) {
                    LawArticle article = articles.get(j);
                    System.out.printf("  法条 %d/%d [%s] %s%n",
                            j + 1, articles.size(), article.getArticleNo(), article.getTitle());
                    System.out.printf("    法规内容：%s%n", article.getContent());
                    System.out.printf("    司法解释：%s%n", article.getInterpretation());
                    System.out.printf("    创建时间：%s%n", article.getCreatedAt());
                    System.out.println();
                }
            }

            System.out.println("=".repeat(80));
            System.out.println("全量输出完成，共 " + results.size() + " 个法规，"
                    + results.stream().mapToInt(r -> r.getLawArticles().size()).sum() + " 条法条");
            System.out.println("=".repeat(80));

            assertFalse(results.isEmpty(), "解析结果不应为空");
        }

        @Test
        @DisplayName("解析实际法规文件，应包含3个法规段落")
        void parseAll_realFile_shouldReturn3Results() throws IOException {
            List<LawFileParser.ParseResult> results = LawFileParser.parseAll(REAL_FILE_PATH);

            log.info("解析结果：" + results);

            assertEquals(3, results.size(), "文件应包含3个法规段落");

            LawRegulation r1 = results.get(0).getLawRegulation();
            assertEquals("中华人民共和国民法典（总则编及相关合同编关联条款）", r1.getName());
            assertEquals("全国人民代表大会", r1.getIssuer());
            assertEquals(LawCategory.CIVIL, r1.getCategory());
            assertEquals(LocalDate.of(2020, 5, 28), r1.getPublishDate());
            assertEquals(LocalDate.of(2021, 1, 1), r1.getEffectiveDate());
            assertEquals(LawStatus.EFFECTIVE, r1.getStatus());
            assertTrue(r1.getIsNew());

            LawRegulation r2 = results.get(1).getLawRegulation();
            assertEquals("中华人民共和国公司法（2024年修订）", r2.getName());
            assertEquals("全国人民代表大会常务委员会", r2.getIssuer());
            assertEquals(LawCategory.COMPANY, r2.getCategory());
            assertEquals(LocalDate.of(2023, 12, 29), r2.getPublishDate());
            assertEquals(LocalDate.of(2024, 7, 1), r2.getEffectiveDate());

            LawRegulation r3 = results.get(2).getLawRegulation();
            assertEquals("最高人民法院关于适用《中华人民共和国民法典》有关担保制度的解释", r3.getName());
            assertEquals("最高人民法院", r3.getIssuer());
            assertEquals(LawCategory.CIVIL, r3.getCategory());
            assertEquals(LocalDate.of(2020, 12, 31), r3.getPublishDate());
            assertEquals(LocalDate.of(2021, 1, 1), r3.getEffectiveDate());
        }

        @Test
        @DisplayName("使用getFirst()获取第一个法规段落及其法条")
        void parseAll_getFirst_shouldReturnFirstRegulationAndArticles() throws IOException {
            List<LawFileParser.ParseResult> parseResults = LawFileParser.parseAll(REAL_FILE_PATH);

            LawRegulation lawRegulation = parseResults.getFirst().getLawRegulation();
            List<LawArticle> lawArticles = parseResults.getFirst().getLawArticles();

            log.info("第一个法规名称：{}", lawRegulation.getName());
            log.info("第一个法规发布机构：{}", lawRegulation.getIssuer());
            log.info("第一个法规分类：{}", lawRegulation.getCategory());
            log.info("第一个法规法条数量：{}", lawArticles.size());

            assertNotNull(lawRegulation, "法规信息不应为null");
            assertEquals("中华人民共和国民法典（总则编及相关合同编关联条款）", lawRegulation.getName());
            assertEquals("全国人民代表大会", lawRegulation.getIssuer());
            assertEquals(LawCategory.CIVIL, lawRegulation.getCategory());
            assertNotNull(lawArticles, "法条列表不应为null");
            assertFalse(lawArticles.isEmpty(), "法条列表不应为空");
            assertEquals(34, lawArticles.size(), "应包含34条法条");

            LawArticle firstArticle = lawArticles.getFirst();
            assertEquals("1", firstArticle.getArticleNo());
            assertEquals("第一条 立法目的", firstArticle.getTitle());
            assertNotNull(firstArticle.getContent());
            assertNotNull(firstArticle.getInterpretation());
        }

        @Test
        @DisplayName("民法典段落应解析出34条法条")
        void parseAll_civilCode_shouldHave34Articles() throws IOException {
            List<LawFileParser.ParseResult> results = LawFileParser.parseAll(REAL_FILE_PATH);

            List<LawArticle> articles = results.get(0).getLawArticles();
            assertFalse(articles.isEmpty(), "民法典段落应包含法条");
            assertEquals(34, articles.size(), "民法典段落应包含34条法条");
        }

        @Test
        @DisplayName("民法典第一条应正确解析")
        void parseAll_firstArticle_shouldParseCorrectly() throws IOException {
            List<LawFileParser.ParseResult> results = LawFileParser.parseAll(REAL_FILE_PATH);

            LawArticle first = results.get(0).getLawArticles().get(0);
            assertEquals("1", first.getArticleNo());
            assertEquals("第一条 立法目的", first.getTitle());
            assertNotNull(first.getContent());
            assertTrue(first.getContent().contains("为了保护民事主体的合法权益"));
            assertNotNull(first.getInterpretation());
            assertTrue(first.getInterpretation().contains("本条明确了《民法典》的立法初衷"));
        }

        @Test
        @DisplayName("民法典最后一条（第34条）应正确解析")
        void parseAll_lastArticle_shouldParseCorrectly() throws IOException {
            List<LawFileParser.ParseResult> results = LawFileParser.parseAll(REAL_FILE_PATH);

            LawArticle last = results.get(0).getLawArticles().get(33);
            assertEquals("34", last.getArticleNo());
            assertEquals("第一百九十二条 诉讼时效期间届满的法律效果", last.getTitle());
            assertNotNull(last.getContent());
            assertTrue(last.getContent().contains("诉讼时效期间届满"));
        }

        @Test
        @DisplayName("公司法段落应解析出法条")
        void parseAll_companyLaw_shouldHaveArticles() throws IOException {
            List<LawFileParser.ParseResult> results = LawFileParser.parseAll(REAL_FILE_PATH);

            List<LawArticle> articles = results.get(1).getLawArticles();
            assertFalse(articles.isEmpty(), "公司法段落应包含法条");

            LawArticle first = articles.get(0);
            assertEquals("1", first.getArticleNo());
            assertEquals("第一条 立法目的", first.getTitle());
            assertTrue(first.getContent().contains("为了规范公司的组织和行为"));
        }

        @Test
        @DisplayName("担保制度解释段落应解析出法条")
        void parseAll_guaranteeLaw_shouldHaveArticles() throws IOException {
            List<LawFileParser.ParseResult> results = LawFileParser.parseAll(REAL_FILE_PATH);

            List<LawArticle> articles = results.get(2).getLawArticles();
            assertFalse(articles.isEmpty(), "担保制度解释段落应包含法条");
        }

        @Test
        @DisplayName("每条法条都应包含法规内容和司法解释")
        void parseAll_everyArticle_shouldHaveContentAndInterpretation() throws IOException {
            List<LawFileParser.ParseResult> results = LawFileParser.parseAll(REAL_FILE_PATH);

            for (int r = 0; r < results.size(); r++) {
                final int ri = r;
                List<LawArticle> articles = results.get(r).getLawArticles();
                for (int a = 0; a < articles.size(); a++) {
                    final int ai = a;
                    LawArticle article = articles.get(a);
                    assertNotNull(article.getContent(), () ->
                            String.format("法规[%d]法条[%d] content 不应为 null", ri, ai));
                    assertFalse(article.getContent().isEmpty(), () ->
                            String.format("法规[%d]法条[%d] content 不应为空", ri, ai));
                    assertNotNull(article.getInterpretation(), () ->
                            String.format("法规[%d]法条[%d] interpretation 不应为 null", ri, ai));
                    assertFalse(article.getInterpretation().isEmpty(), () ->
                            String.format("法规[%d]法条[%d] interpretation 不应为空", ri, ai));
                }
            }
        }
    }

    @Nested
    @DisplayName("parse - 单法规段落解析（兼容旧接口）")
    class ParseSingleTests {

        @Test
        @DisplayName("单段落解析应返回第一个法规段落")
        void parse_realFile_shouldReturnFirstResult() throws IOException {
            LawFileParser.ParseResult result = LawFileParser.parse(REAL_FILE_PATH);

            assertNotNull(result);
            assertNotNull(result.getLawRegulation());
            assertNotNull(result.getLawArticles());
            assertEquals("中华人民共和国民法典（总则编及相关合同编关联条款）", result.getLawRegulation().getName());
        }

        @Test
        @DisplayName("toMap 应返回兼容结构")
        void parse_toMap_shouldReturnCompatibleStructure() throws IOException {
            LawFileParser.ParseResult result = LawFileParser.parse(REAL_FILE_PATH);

            Map<String, Object> map = result.toMap();
            assertTrue(map.containsKey("law_regulation"));
            assertTrue(map.containsKey("law_article"));

            @SuppressWarnings("unchecked")
            List<LawRegulation> regulations = (List<LawRegulation>) map.get("law_regulation");
            assertEquals(1, regulations.size());
            assertEquals(result.getLawRegulation().getName(), regulations.get(0).getName());

            @SuppressWarnings("unchecked")
            List<LawArticle> articles = (List<LawArticle>) map.get("law_article");
            assertEquals(result.getLawArticles().size(), articles.size());
        }
    }

    @Nested
    @DisplayName("parseCategory - 分类解析")
    class ParseCategoryTests {

        @Test
        @DisplayName("通过枚举code匹配民法分类")
        void parseCategory_civilCode_shouldReturnCivil() {
            assertEquals(LawCategory.CIVIL, LawFileParser.parseCategory("civil"));
        }

        @Test
        @DisplayName("通过枚举code匹配公司法分类")
        void parseCategory_companyCode_shouldReturnCompany() {
            assertEquals(LawCategory.COMPANY, LawFileParser.parseCategory("company"));
        }

        @Test
        @DisplayName("通过枚举code匹配合同法分类")
        void parseCategory_contractCode_shouldReturnContract() {
            assertEquals(LawCategory.CONTRACT, LawFileParser.parseCategory("contract"));
        }

        @Test
        @DisplayName("通过中文描述匹配分类")
        void parseCategory_chineseDesc_shouldMatch() {
            assertEquals(LawCategory.CIVIL, LawFileParser.parseCategory("民法"));
            assertEquals(LawCategory.COMPANY, LawFileParser.parseCategory("公司法"));
            assertEquals(LawCategory.CONTRACT, LawFileParser.parseCategory("合同法"));
        }

        @Test
        @DisplayName("空值应返回null")
        void parseCategory_null_shouldReturnNull() {
            assertNull(LawFileParser.parseCategory(null));
            assertNull(LawFileParser.parseCategory(""));
            assertNull(LawFileParser.parseCategory("   "));
        }

        @Test
        @DisplayName("无法匹配的分类应返回null")
        void parseCategory_unknown_shouldReturnNull() {
            assertNull(LawFileParser.parseCategory("未知分类"));
        }
    }

    @Nested
    @DisplayName("parseDate - 日期解析")
    class ParseDateTests {

        @Test
        @DisplayName("解析中文日期格式")
        void parseDate_chineseFormat_shouldParse() {
            assertEquals(LocalDate.of(2020, 5, 28), LawFileParser.parseDate("2020年5月28日"));
            assertEquals(LocalDate.of(2021, 1, 1), LawFileParser.parseDate("2021年1月1日"));
            assertEquals(LocalDate.of(2023, 12, 29), LawFileParser.parseDate("2023年12月29日"));
        }

        @Test
        @DisplayName("解析标准日期格式")
        void parseDate_standardFormat_shouldParse() {
            assertEquals(LocalDate.of(2020, 5, 28), LawFileParser.parseDate("2020-05-28"));
            assertEquals(LocalDate.of(2021, 1, 1), LawFileParser.parseDate("2021-01-01"));
        }

        @Test
        @DisplayName("空值应返回null")
        void parseDate_null_shouldReturnNull() {
            assertNull(LawFileParser.parseDate(null));
            assertNull(LawFileParser.parseDate(""));
            assertNull(LawFileParser.parseDate("   "));
        }

        @Test
        @DisplayName("无法解析的日期应返回null")
        void parseDate_invalid_shouldReturnNull() {
            assertNull(LawFileParser.parseDate("无效日期"));
            assertNull(LawFileParser.parseDate("2020/05/28"));
        }
    }

    @Nested
    @DisplayName("异常场景")
    class ExceptionTests {

        @Test
        @DisplayName("null内容应抛出IllegalArgumentException")
        void parse_nullContent_shouldThrow() {
            assertThrows(IllegalArgumentException.class, () -> LawFileParser.parse((String) null));
        }

        @Test
        @DisplayName("空白内容应抛出IllegalArgumentException")
        void parse_blankContent_shouldThrow() {
            assertThrows(IllegalArgumentException.class, () -> LawFileParser.parse("   "));
        }

        @Test
        @DisplayName("无法规名称的内容应抛出IllegalArgumentException")
        void parse_noLawName_shouldThrow() {
            String content = "这不是一个合法的法规文件";
            assertThrows(IllegalArgumentException.class, () -> LawFileParser.parse(content));
        }

        @Test
        @DisplayName("不存在的文件应抛出IOException")
        void parse_nonExistentFile_shouldThrow() {
            Path badPath = Path.of("不存在的文件.txt");
            assertThrows(IOException.class, () -> LawFileParser.parse(badPath));
        }
    }
}
