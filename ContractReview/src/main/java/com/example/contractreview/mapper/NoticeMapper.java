package com.example.contractreview.mapper;

import com.example.contractreview.model.entity.Notice;
import com.example.contractreview.model.vo.NoticeVO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * 公告Mapper接口
 */
@Mapper
public interface NoticeMapper {

    /**
     * 插入公告
     */
    int insert(Notice notice);

    /**
     * 根据ID查询公告
     */
    Notice selectById(@Param("id") Integer id);

    /**
     * 查询所有公告
     */
    List<NoticeVO> selectAll();

    /**
     * 更新公告
     */
    int update(@Param("notice") Notice notice, Integer id);

    /**
     * 删除公告
     */
    int deleteById(@Param("id") Integer id);

    /**
     * 置顶
     */
    void updateTop(Integer id, Integer isTop);
}
