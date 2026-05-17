package com.example.contractreview.mapper;

import com.example.contractreview.model.entity.Contract;
import com.example.contractreview.model.entity.ContractStats;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * 合同数据访问层
 */
@Mapper
public interface ContractMapper {

    /**
     * 根据ID查询合同
     *
     * @param id 合同ID
     * @return 合同实体
     */
    Contract selectById(@Param("id") Long id);

    /**
     * 根据用户ID查询合同列表
     *
     * @param userId 用户ID
     * @return 合同列表
     */
    List<Contract> selectByUserId(@Param("userId") Long userId, String keyword);

    /**
     * 插入合同
     *
     * @param contract 合同实体
     * @return 影响行数
     */
    int insert(@Param("contract") Contract contract);

    /**
     * 更新合同
     *
     * @param contract 合同实体
     * @return 影响行数
     */
    int update(@Param("contract") Contract contract);

    /**
     * 根据ID删除合同
     *
     * @param id 合同ID
     * @return 影响行数
     */
    int deleteById(@Param("id") Long id);

    /**
     * 批量删除合同
     *
     * @param ids 合同ID列表
     * @return 影响行数
     */
    int batchDelete(@Param("ids") List<Long> ids);

    /**
     * 查询所有合同
     *
     * @return 合同列表
     */
    List<Contract> selectAll();

    /**
     * 查询合同统计数据
     *
     * @param userId 用户ID
     * @return 合同统计数据
     */
    ContractStats selectStatsByUserId(@Param("userId") Long userId);

    /**
     * 查询用户在指定时间范围内的合同数量
     *
     * @param userId    用户ID
     * @param startTime 开始时间
     * @param endTime   结束时间
     * @return 合同数量
     */
    Long selectCountByUserIdAndTimeRange(@Param("userId") Long userId,
                                          @Param("startTime") String startTime,
                                          @Param("endTime") String endTime);

    /**
     * 查询用户在指定时间范围内的合同统计数据
     *
     * @param userId    用户ID
     * @param startTime 开始时间
     * @param endTime   结束时间
     * @return 合同统计数据
     */
    ContractStats selectStatsByUserIdAndTimeRange(@Param("userId") Long userId,
                                                   @Param("startTime") String startTime,
                                                   @Param("endTime") String endTime);

    /**
     * 根据ID查询文件名
     *
     * @param id 合同ID
     * @return 文件名
     */
    String selectFileNameById(@Param("id") Long id);

    /**
     * 重置合同审查状态（用于重新审查）
     *
     * @param id 合同ID
     * @return 影响行数
     */
    int resetReviewStatus(@Param("id") Long id);
}
