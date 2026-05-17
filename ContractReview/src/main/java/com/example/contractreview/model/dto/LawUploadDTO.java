package com.example.contractreview.model.dto;

import com.example.contractreview.enums.LawType;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDate;

/**
 * 法律文档上传请求DTO
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class LawUploadDTO {

    /**
     * 文档类型: law-法律法规/interpretation-司法解释/template-合同范本/other-其他
     */
    @NotNull(message = "文档类型不能为空")
    private LawType type;

    /**
     * 生效日期
     */
    private LocalDate effectiveDate;

    /**
     * 文档说明
     */
    @Size(max = 500, message = "文档说明长度不能超过500字符")
    private String description;
}
