package com.example.contractreview.enums;

import org.apache.ibatis.type.BaseTypeHandler;
import org.apache.ibatis.type.JdbcType;

import java.sql.CallableStatement;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

/**
 * UserStatus 枚举类型处理器
 * 用于 MyBatis 与数据库之间的枚举转换
 */
public class UserStatusTypeHandler extends BaseTypeHandler<UserStatus> {

    @Override
    public void setNonNullParameter(PreparedStatement ps, int i, UserStatus parameter, JdbcType jdbcType) throws SQLException {
        ps.setInt(i, parameter.getCode());
    }

    @Override
    public UserStatus getNullableResult(ResultSet rs, String columnName) throws SQLException {
        Integer code = rs.getInt(columnName);
        if (rs.wasNull()) {
            return null;
        }
        return getByCode(code);
    }

    @Override
    public UserStatus getNullableResult(ResultSet rs, int columnIndex) throws SQLException {
        Integer code = rs.getInt(columnIndex);
        if (rs.wasNull()) {
            return null;
        }
        return getByCode(code);
    }

    @Override
    public UserStatus getNullableResult(CallableStatement cs, int columnIndex) throws SQLException {
        Integer code = cs.getInt(columnIndex);
        if (cs.wasNull()) {
            return null;
        }
        return getByCode(code);
    }

    private UserStatus getByCode(Integer code) {
        if (code == null) {
            return null;
        }
        return UserStatus.getByCode(code);
    }
}
