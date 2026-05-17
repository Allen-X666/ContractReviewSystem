package com.example.contractreview.mapper;

import com.example.contractreview.model.vo.KnowledgeStatsVO;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface KnowledgeMapper {

    /**
     * 查询知识库统计数据
     *
     * @return 知识库统计数据
     */
    KnowledgeStatsVO selectKnowledgeStats();
}
