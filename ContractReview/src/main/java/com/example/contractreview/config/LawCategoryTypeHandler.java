package com.example.contractreview.config;

import com.example.contractreview.enums.LawCategory;
import org.apache.ibatis.type.BaseTypeHandler;
import org.apache.ibatis.type.JdbcType;
import org.apache.ibatis.type.MappedTypes;

import java.sql.CallableStatement;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;

/**
 * LawCategory 枚举类型处理器
 * 支持大小写不敏感的枚举映射
 */
@MappedTypes(LawCategory.class)
public class LawCategoryTypeHandler extends BaseTypeHandler<LawCategory> {

    @Override
    public void setNonNullParameter(PreparedStatement ps, int i, LawCategory parameter, JdbcType jdbcType) throws SQLException {
        ps.setString(i, parameter.getCode());
    }

    @Override
    public LawCategory getNullableResult(ResultSet rs, String columnName) throws SQLException {
        String value = rs.getString(columnName);
        return fromCode(value);
    }

    @Override
    public LawCategory getNullableResult(ResultSet rs, int columnIndex) throws SQLException {
        String value = rs.getString(columnIndex);
        return fromCode(value);
    }

    @Override
    public LawCategory getNullableResult(CallableStatement cs, int columnIndex) throws SQLException {
        String value = cs.getString(columnIndex);
        return fromCode(value);
    }

    /**
     * 根据 code 查找枚举，支持大小写不敏感
     */
    private LawCategory fromCode(String code) {
        if (code == null || code.trim().isEmpty()) {
            return null;
        }
        for (LawCategory category : LawCategory.values()) {
            if (category.getCode().equalsIgnoreCase(code.trim())) {
                return category;
            }
        }
        // 如果找不到匹配的 code，尝试按名称匹配（兼容旧数据）
        try {
            return LawCategory.valueOf(code.toUpperCase());
        } catch (IllegalArgumentException e) {
            return null;
        }
    }
}
