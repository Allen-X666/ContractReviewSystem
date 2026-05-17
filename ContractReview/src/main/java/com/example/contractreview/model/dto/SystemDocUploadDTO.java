package com.example.contractreview.model.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class SystemDocUploadDTO {
    @NotNull(message = "文件不能为空")
    private MultipartFile file;

    @NotNull(message = "文档分类不能为空")
    private String category;

    @NotNull(message = "文档标签不能为空")
    private List<String> tags;          // 文档标签

    @Size(max = 500, message = "文档说明长度不能超过500字符")
    private String description;
}