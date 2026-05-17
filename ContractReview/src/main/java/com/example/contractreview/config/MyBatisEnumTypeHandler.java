package com.example.contractreview.config;

import com.example.contractreview.enums.LawCategory;
import com.example.contractreview.enums.LawStatus;
import org.apache.ibatis.type.BaseTypeHandler;
import org.apache.ibatis.type.JdbcType;
import org.apache.ibatis.type.MappedTypes;

import java.sql.CallableStatement;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

/**
 * MyBatis 枚举类型处理器（支持大小写转换）
 */
@MappedTypes({LawCategory.class, LawStatus.class})
public class MyBatisEnumTypeHandler<E extends Enum<E>> extends BaseTypeHandler<E> {

    private final Class<E> type;

    public MyBatisEnumTypeHandler(Class<E> type) {
        if (type == null) {
            throw new IllegalArgumentException("Type argument cannot be null");
        }
        this.type = type;
    }

    @Override
    public void setNonNullParameter(PreparedStatement ps, int i, E parameter, JdbcType jdbcType) throws SQLException {
        ps.setString(i, parameter.name().toLowerCase());
    }

    @Override
    public E getNullableResult(ResultSet rs, String columnName) throws SQLException {
        String value = rs.getString(columnName);
        return value == null ? null : Enum.valueOf(type, value.toUpperCase());
    }

    @Override
    public E getNullableResult(ResultSet rs, int columnIndex) throws SQLException {
        String value = rs.getString(columnIndex);
        return value == null ? null : Enum.valueOf(type, value.toUpperCase());
    }

    @Override
    public E getNullableResult(CallableStatement cs, int columnIndex) throws SQLException {
        String value = cs.getString(columnIndex);
        return value == null ? null : Enum.valueOf(type, value.toUpperCase());
    }
}
