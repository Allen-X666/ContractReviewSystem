package com.example.contractreview.service.serviceImpl;

import com.example.contractreview.common.Result;
import com.example.contractreview.constant.KnowledgeConstant;
import com.example.contractreview.enums.LawCategory;
import com.example.contractreview.mapper.KnowledgeMapper;
import com.example.contractreview.mapper.LawMapper;
import com.example.contractreview.model.entity.LawArticle;
import com.example.contractreview.model.entity.LawRegulation;
import com.example.contractreview.model.vo.KnowledgeStatsVO;
import com.example.contractreview.model.vo.LawCategoryGroupVO;
import com.example.contractreview.model.vo.LawCategoryVO;
import com.example.contractreview.model.vo.LawRegulationDetailVO;
import com.example.contractreview.model.vo.LawRegulationVO;
import com.example.contractreview.service.KnowledgeService;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.pagehelper.PageHelper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;

@Service
@Slf4j
@RequiredArgsConstructor
public class KnowledgeServiceImpl implements KnowledgeService {

    private final KnowledgeMapper knowledgeMapper;
    private final LawMapper lawMapper;
    private final StringRedisTemplate stringRedisTemplate;
    private final ObjectMapper objectMapper;

    private static final long STATS_CACHE_EXPIRE_HOURS = 1;
    private static final long LAW_CACHE_EXPIRE_HOURS = 1;

    @Override
    public Result<KnowledgeStatsVO> getKnowledgeStats() {
        String cacheKey = KnowledgeConstant.KNOWLEDGE_STATS_KEY;

        try {
            String cachedStats = stringRedisTemplate.opsForValue().get(cacheKey);
            if (cachedStats != null) {
                KnowledgeStatsVO statsVO = objectMapper.readValue(cachedStats, KnowledgeStatsVO.class);
                return Result.success(statsVO);
            }
        } catch (Exception e) {
            log.warn("从Redis读取知识库统计数据失败, error: {}", e.getMessage());
        }

        KnowledgeStatsVO statsVO = knowledgeMapper.selectKnowledgeStats();

        if (statsVO == null) {
            statsVO = KnowledgeStatsVO.builder()
                    .totalLaws(0)
                    .totalArticles(0)
                    .totalTemplates(0)
                    .lastUpdate(LocalDate.now())
                    .build();
        }

        if (statsVO.getTotalLaws() == null) {
            statsVO.setTotalLaws(0);
        }
        if (statsVO.getTotalArticles() == null) {
            statsVO.setTotalArticles(0);
        }
        if (statsVO.getTotalTemplates() == null) {
            statsVO.setTotalTemplates(0);
        }
        if (statsVO.getLastUpdate() == null) {
            statsVO.setLastUpdate(LocalDate.now());
        }

        try {
            String statsJson = objectMapper.writeValueAsString(statsVO);
            stringRedisTemplate.opsForValue().set(cacheKey, statsJson, STATS_CACHE_EXPIRE_HOURS, TimeUnit.HOURS);
        } catch (Exception e) {
            log.warn("缓存知识库统计数据到Redis失败, error: {}", e.getMessage());
        }
        return Result.success(statsVO);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Result<List<LawCategoryVO>> getLawCategories() {
        String cacheKey = KnowledgeConstant.LAW_CATEGORIES_KEY;

        try {
            String cachedData = stringRedisTemplate.opsForValue().get(cacheKey);
            if (cachedData != null) {
                List<LawCategoryVO> categories = objectMapper.readValue(cachedData, new TypeReference<List<LawCategoryVO>>() {});
                return Result.success(categories);
            }
        } catch (Exception e) {
            log.warn("从Redis读取法规分类列表失败, error: {}", e.getMessage());
        }

        List<LawCategoryVO> categories = Arrays.stream(LawCategory.values())
                .map(cat -> LawCategoryVO.builder()
                        .id(cat.name())
                        .name(cat.getDescription())
                        .build())
                .collect(Collectors.toList());

        try {
            String categoriesJson = objectMapper.writeValueAsString(categories);
            stringRedisTemplate.opsForValue().set(cacheKey, categoriesJson, LAW_CACHE_EXPIRE_HOURS, TimeUnit.HOURS);
        } catch (Exception e) {
            log.warn("缓存法规分类列表到Redis失败, error: {}", e.getMessage());
        }

        log.info("从数据库查询法规分类列表");
        return Result.success(categories);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Result<List<LawCategoryGroupVO>> searchLawsGroupedByCategory(String keyword, Integer page, Integer pageSize) {
        // 查询所有法规（不按分类过滤）
        PageHelper.startPage(page != null ? page : 1, pageSize != null ? pageSize : 100);
        List<LawRegulation> laws = lawMapper.searchLaws(keyword, null);

        // 转换为VO并按分类分组
        Map<LawCategory, List<LawRegulationVO>> groupedMap = laws.stream()
                .map(this::convertToVO)
                .collect(Collectors.groupingBy(LawRegulationVO::getCategory, LinkedHashMap::new, Collectors.toList()));

        // 构建分组结果列表
        List<LawCategoryGroupVO> result = new ArrayList<>();
        for (Map.Entry<LawCategory, List<LawRegulationVO>> entry : groupedMap.entrySet()) {
            LawCategory category = entry.getKey();
            result.add(LawCategoryGroupVO.builder()
                    .categoryId(category.name())
                    .categoryName(category.getDescription())
                    .laws(entry.getValue())
                    .build());
        }
        return Result.success(result);
    }

    @Override
    public Result<LawRegulationDetailVO> getLawDetail(Long lawId) {
        String cacheKey = KnowledgeConstant.LAW_DETAIL_KEY_PREFIX + lawId;

        try {
            String cachedData = stringRedisTemplate.opsForValue().get(cacheKey);
            if (cachedData != null) {
                LawRegulationDetailVO detailVO = objectMapper.readValue(cachedData, LawRegulationDetailVO.class);
                return Result.success(detailVO);
            }
        } catch (Exception e) {
            log.warn("从Redis读取法规详情失败, lawId: {}, error: {}", lawId, e.getMessage());
        }

        LawRegulation law = lawMapper.selectById(lawId);
        if (law == null) {
            log.warn("法规不存在, lawId: {}", lawId);
            return Result.error("法规不存在");
        }

        List<LawArticle> articles = lawMapper.selectArticlesByLawId(lawId);

        LawRegulationDetailVO detailVO = convertToDetailVO(law, articles);

        try {
            String detailJson = objectMapper.writeValueAsString(detailVO);
            stringRedisTemplate.opsForValue().set(cacheKey, detailJson, LAW_CACHE_EXPIRE_HOURS, TimeUnit.HOURS);
        } catch (Exception e) {
            log.warn("缓存法规详情到Redis失败, lawId: {}, error: {}", lawId, e.getMessage());
        }

        log.info("从数据库查询法规详情, lawId: {}", lawId);
        return Result.success(detailVO);
    }

    private LawRegulationVO convertToVO(LawRegulation law) {
        return LawRegulationVO.builder()
                .id(law.getId())
                .name(law.getName())
                .category(law.getCategory())
                .issuer(law.getIssuer())
                .publishDate(law.getPublishDate())
                .effectiveDate(law.getEffectiveDate())
                .status(law.getStatus())
                .description(law.getDescription())
                .articleCount(law.getArticleCount())
                .isNew(law.getIsNew())
                .build();
    }

    private LawRegulationDetailVO convertToDetailVO(LawRegulation law, List<LawArticle> articles) {
        List<LawRegulationDetailVO.LawArticleVO> articleVOList = articles.stream()
                .map(article -> LawRegulationDetailVO.LawArticleVO.builder()
                        .id(article.getId())
                        .articleNo(article.getArticleNo())
                        .title(article.getTitle())
                        .content(article.getContent())
                        .interpretation(article.getInterpretation())
                        .build())
                .collect(Collectors.toList());

        return LawRegulationDetailVO.builder()
                .id(law.getId())
                .name(law.getName())
                .category(law.getCategory())
                .issuer(law.getIssuer())
                .publishDate(law.getPublishDate())
                .effectiveDate(law.getEffectiveDate())
                .status(law.getStatus())
                .description(law.getDescription())
                .isNew(law.getIsNew())
                .createdAt(law.getCreatedAt())
                .articles(articleVOList)
                .build();
    }
}
