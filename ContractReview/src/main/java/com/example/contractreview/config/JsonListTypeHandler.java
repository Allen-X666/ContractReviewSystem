package com.example.contractreview.config;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.apache.ibatis.type.BaseTypeHandler;
import org.apache.ibatis.type.JdbcType;
import org.springframework.stereotype.Component;

import java.sql.CallableStatement;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.List;

/**
 * MyBatis TypeHandler：JSON 字符串与 List<String> 之间的转换
 * 用于处理数据库中 JSON 类型的 tags 字段
 */
@Component
@Slf4j
public class JsonListTypeHandler extends BaseTypeHandler<List<String>> {

    private static final ObjectMapper mapper = new ObjectMapper();

    @Override
    public void setNonNullParameter(PreparedStatement ps, int i, List<String> parameter, JdbcType jdbcType) throws SQLException {
        try {
            ps.setString(i, mapper.writeValueAsString(parameter));
        } catch (Exception e) {
            log.error("Failed to convert List to JSON string, parameter: {}", parameter, e);
            throw new SQLException("Failed to convert List to JSON string", e);
        }
    }

    @Override
    public List<String> getNullableResult(ResultSet rs, String columnName) throws SQLException {
        String json = rs.getString(columnName);
        if (json == null || json.isEmpty()) {
            return null;
        }
        try {
            return mapper.readValue(json, new TypeReference<List<String>>() {});
        } catch (Exception e) {
            log.error("Failed to parse JSON to List, column: {}, value: {}", columnName, json, e);
            throw new SQLException("Failed to parse JSON to List, column: " + columnName + ", value: " + json, e);
        }
    }

    @Override
    public List<String> getNullableResult(ResultSet rs, int columnIndex) throws SQLException {
        String json = rs.getString(columnIndex);
        if (json == null || json.isEmpty()) {
            return null;
        }
        try {
            return mapper.readValue(json, new TypeReference<List<String>>() {});
        } catch (Exception e) {
            log.error("Failed to parse JSON to List, columnIndex: {}, value: {}", columnIndex, json, e);
            throw new SQLException("Failed to parse JSON to List, columnIndex: " + columnIndex + ", value: " + json, e);
        }
    }

    @Override
    public List<String> getNullableResult(CallableStatement cs, int columnIndex) throws SQLException {
        String json = cs.getString(columnIndex);
        if (json == null || json.isEmpty()) {
            return null;
        }
        try {
            return mapper.readValue(json, new TypeReference<List<String>>() {});
        } catch (Exception e) {
            log.error("Failed to parse JSON to List, columnIndex: {}, value: {}", columnIndex, json, e);
            throw new SQLException("Failed to parse JSON to List, columnIndex: " + columnIndex + ", value: " + json, e);
        }
    }
}
