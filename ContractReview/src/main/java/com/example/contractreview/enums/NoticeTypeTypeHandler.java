package com.example.contractreview.enums;

import org.apache.ibatis.type.BaseTypeHandler;
import org.apache.ibatis.type.JdbcType;

import java.sql.CallableStatement;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

/**
 * NoticeType 枚举类型处理器
 * 用于 MyBatis 与数据库之间的枚举转换
 */
public class NoticeTypeTypeHandler extends BaseTypeHandler<NoticeType> {

    @Override
    public void setNonNullParameter(PreparedStatement ps, int i, NoticeType parameter, JdbcType jdbcType) throws SQLException {
        ps.setString(i, parameter.getCode());
    }

    @Override
    public NoticeType getNullableResult(ResultSet rs, String columnName) throws SQLException {
        String code = rs.getString(columnName);
        if (rs.wasNull()) {
            return null;
        }
        return getByCode(code);
    }

    @Override
    public NoticeType getNullableResult(ResultSet rs, int columnIndex) throws SQLException {
        String code = rs.getString(columnIndex);
        if (rs.wasNull()) {
            return null;
        }
        return getByCode(code);
    }

    @Override
    public NoticeType getNullableResult(CallableStatement cs, int columnIndex) throws SQLException {
        String code = cs.getString(columnIndex);
        if (cs.wasNull()) {
            return null;
        }
        return getByCode(code);
    }

    private NoticeType getByCode(String code) {
        if (code == null) {
            return null;
        }
        return NoticeType.getByCode(code);
    }
}
