package com.example.contractreview.mapper;

import com.example.contractreview.model.entity.LawArticle;
import com.example.contractreview.model.entity.LawRegulation;
import com.example.contractreview.model.entity.SystemDocument;
import com.example.contractreview.model.vo.SelectSystemDocumentListVO;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

@Mapper
public interface AdminMapper {

    // 根据名称批量查询法规
    List<LawRegulation> selectByNames(List<String> names);

    // 批量插入法规
    void insertLawRegulation(List<LawRegulation> lawRegulation);

    // 批量插入法规条款
    void insertLawArticles(List<LawArticle> lawArticles);

    // 批量插入系统文档
    void insertSystemDocument(SystemDocument document);

    // 查询系统文档列表
    List<SelectSystemDocumentListVO> selectSystemDocumentList();

    // 根据id查询系统文档
    SystemDocument selectLawDocumentById(Integer id);

    // 删除系统文档
    int deleteLawDocumentById(Integer id);
}
