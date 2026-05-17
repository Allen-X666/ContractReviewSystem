package com.example.contractreview.mapper;

import com.example.contractreview.model.dto.AdminUpdateUserDTO;
import com.example.contractreview.model.entity.SystemDocument;
import com.example.contractreview.model.entity.User;
import com.example.contractreview.enums.UserStatus;
import io.lettuce.core.dynamic.annotation.Param;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotNull;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

@Mapper
public interface AuthMapper {

    /**
     * 根据ID查询用户
     */
    User selectById(@Param("id") Integer id);

    /**
     * 插入用户
     */
    int insert(User user);

    /**
     * 更新用户
     */
    int update(User user);

    /**
     * 根据ID删除用户
     */
    int deleteById(@Param("id") Long id);

    /**
     * 根据用户名查询用户
     */
    User selectByUsername(@Param("username") String username);

    /**
     * 根据邮箱查询用户
     */
    User selectByEmail(@Param("email") String email);

    /**
     * 根据手机号查询用户
     */
    User selectByPhone(@Param("phone") String phone);

    /**
     * 判断用户名是否存在
     */
    boolean existsByUsername(@Param("username") String username);

    /**
     * 判断邮箱是否存在
     */
    boolean existsByEmail(@Param("email") String email);

    /**
     * 判断手机号是否存在
     */
    boolean existsByPhone(@Param("phone") String phone);

    /**
     * 查询所有用户
     */
    List<User> selectAllUsers();

    /**
     * 管理员更新用户信息
     */
    int updateByAdmin(@Param("userId") Long userId,
                      @Param("adminUpdateUserDTO") AdminUpdateUserDTO adminUpdateUserDTO);

    /**
     * 更新用户状态
     */
    int updateStatus(@Param("userId") Long userId,
                     @Param("status") UserStatus status);

    /**
     * 判断用户名是否存在（排除指定用户）
     */
    boolean existsByUsernameExcludeId(@Param("username") String username,
                                      @Param("excludeId") Long excludeId);

    /**
     * 判断邮箱是否存在（排除指定用户）
     */
    boolean existsByEmailExcludeId(@Param("email") String email,
                                   @Param("excludeId") Long excludeId);

    /**
     * 判断手机号是否存在（排除指定用户）
     */
    boolean existsByPhoneExcludeId(@Param("phone") String phone,
                                   @Param("excludeId") Long excludeId);

    /**
     * 修改密码
     */
    void updatePassword(@Email(message = "邮箱格式不正确") @NotNull(message = "邮箱不能为空") String email, String password);
}
