package com.example.contractreview.enums;

import org.apache.ibatis.type.BaseTypeHandler;
import org.apache.ibatis.type.JdbcType;

import java.sql.CallableStatement;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

/**
 * UserRole 枚举类型处理器
 * 用于 MyBatis 与数据库之间的枚举转换
 */
public class UserRoleTypeHandler extends BaseTypeHandler<UserRole> {

    @Override
    public void setNonNullParameter(PreparedStatement ps, int i, UserRole parameter, JdbcType jdbcType) throws SQLException {
        ps.setString(i, parameter.getCode());
    }

    @Override
    public UserRole getNullableResult(ResultSet rs, String columnName) throws SQLException {
        String code = rs.getString(columnName);
        if (rs.wasNull()) {
            return null;
        }
        return getByCode(code);
    }

    @Override
    public UserRole getNullableResult(ResultSet rs, int columnIndex) throws SQLException {
        String code = rs.getString(columnIndex);
        if (rs.wasNull()) {
            return null;
        }
        return getByCode(code);
    }

    @Override
    public UserRole getNullableResult(CallableStatement cs, int columnIndex) throws SQLException {
        String code = cs.getString(columnIndex);
        if (cs.wasNull()) {
            return null;
        }
        return getByCode(code);
    }

    private UserRole getByCode(String code) {
        if (code == null) {
            return null;
        }
        return UserRole.getByCode(code);
    }
}
