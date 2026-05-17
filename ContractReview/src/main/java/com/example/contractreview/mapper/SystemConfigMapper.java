package com.example.contractreview.mapper;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

@Mapper
public interface SystemConfigMapper {
    // 查询上传路径
    String selectUploadPathByUserId(Integer userId);

    // 查询审查路径
    String selectReviewPathByUserId(Integer userId);

    // 更新路径
    void updatePath(Integer userId, String uploadPath, String reviewPath);

    // 插入上传路径
    void insertUploadPath(Integer userId, String uploadPath);

    // 插入审查路径
    void insertReviewPath(Integer userId, String reviewPath);

    /**
     * 删除用户存储设置
     * @param userId 用户ID
     */
    void deleteByUserId(@Param("userId") Long userId);
}
