package com.example.contractreview.config;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.apache.ibatis.type.BaseTypeHandler;
import org.apache.ibatis.type.JdbcType;
import org.springframework.stereotype.Component;

import java.sql.CallableStatement;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.Map;

/**
 * MyBatis TypeHandler：JSON 字符串与 Map<String, Integer> 之间的转换
 * 用于处理数据库中 JSON 类型的 riskSummary 字段
 */
@Component
@RequiredArgsConstructor
public class JsonToMapTypeHandler extends BaseTypeHandler<Map<String, Integer>> {

    private static final ObjectMapper mapper = new ObjectMapper();

    @Override
    public void setNonNullParameter(PreparedStatement ps, int i, Map<String, Integer> parameter, JdbcType jdbcType) throws SQLException {
        try {
            ps.setString(i, mapper.writeValueAsString(parameter));
        } catch (Exception e) {
            throw new SQLException("Failed to convert Map to JSON string", e);
        }
    }

    @Override
    public Map<String, Integer> getNullableResult(ResultSet rs, String columnName) throws SQLException {
        String json = rs.getString(columnName);
        if (json == null || json.isEmpty()) {
            return null;
        }
        try {
            return mapper.readValue(json, new TypeReference<Map<String, Integer>>() {});
        } catch (Exception e) {
            throw new SQLException("Failed to parse JSON to Map, column: " + columnName + ", value: " + json, e);
        }
    }

    @Override
    public Map<String, Integer> getNullableResult(ResultSet rs, int columnIndex) throws SQLException {
        String json = rs.getString(columnIndex);
        if (json == null || json.isEmpty()) {
            return null;
        }
        try {
            return mapper.readValue(json, new TypeReference<Map<String, Integer>>() {});
        } catch (Exception e) {
            throw new SQLException("Failed to parse JSON to Map, columnIndex: " + columnIndex + ", value: " + json, e);
        }
    }

    @Override
    public Map<String, Integer> getNullableResult(CallableStatement cs, int columnIndex) throws SQLException {
        String json = cs.getString(columnIndex);
        if (json == null || json.isEmpty()) {
            return null;
        }
        try {
            return mapper.readValue(json, new TypeReference<Map<String, Integer>>() {});
        } catch (Exception e) {
            throw new SQLException("Failed to parse JSON to Map, columnIndex: " + columnIndex + ", value: " + json, e);
        }
    }
}
