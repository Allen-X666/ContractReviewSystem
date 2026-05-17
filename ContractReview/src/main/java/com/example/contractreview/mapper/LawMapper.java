package com.example.contractreview.mapper;

import com.example.contractreview.enums.LawCategory;
import com.example.contractreview.model.entity.LawArticle;
import com.example.contractreview.model.entity.LawDocument;
import com.example.contractreview.model.entity.LawRegulation;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * 法律法规数据访问层
 */
@Mapper
public interface LawMapper {

    /**
     * 获取所有法规分类
     *
     * @return 分类列表
     */
    List<String> selectAllCategories();

    /**
     * 搜索法规
     *
     * @param keyword  关键词
     * @param category 分类
     * @return 法规列表
     */
    List<LawRegulation> searchLaws(@Param("keyword") String keyword,
                                   @Param("category") String category);

    /**
     * 根据ID查询法规
     *
     * @param lawId 法规ID
     * @return 法规实体
     */
    LawRegulation selectById(@Param("lawId") Long lawId);

    /**
     * 根据法规ID查询法条列表
     *
     * @param lawId 法规ID
     * @return 法条列表
     */
    List<LawArticle> selectArticlesByLawId(@Param("lawId") Long lawId);

    /**
     * 插入法律文档
     *
     * @param document 法律文档实体
     * @return 影响行数
     */
    int insertLawDocument(LawDocument document);

    /**
     * 查询所有法律文档列表
     *
     * @return 文档列表
     */
    List<LawDocument> selectAllLawDocuments();

    /**
     * 根据ID查询法律文档
     *
     * @param id 文档ID
     * @return 文档实体
     */
    LawDocument selectLawDocumentById(@Param("id") Long id);

    /**
     * 根据ID删除法律文档
     *
     * @param id 文档ID
     * @return 影响行数
     */
    int deleteLawDocumentById(@Param("id") Long id);
}
