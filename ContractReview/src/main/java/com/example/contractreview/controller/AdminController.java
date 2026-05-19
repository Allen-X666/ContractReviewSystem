package com.example.contractreview.controller;

import com.example.contractreview.common.PageResult;
import com.example.contractreview.common.Result;
import com.example.contractreview.enums.UserStatus;
import com.example.contractreview.model.dto.*;
import com.example.contractreview.model.entity.LawDocument;
import com.example.contractreview.model.entity.Notice;
import com.example.contractreview.model.entity.SystemDocument;
import com.example.contractreview.model.entity.User;
import com.example.contractreview.model.vo.NoticeVO;
import com.example.contractreview.model.vo.SelectSystemDocumentListVO;
import com.example.contractreview.service.AdminService;
import com.example.contractreview.utils.TokenUtils;
import com.fasterxml.jackson.core.JsonProcessingException;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.core.io.Resource;
import org.springframework.core.io.UrlResource;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.net.MalformedURLException;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;

@RestController
@RequestMapping("/admin")
@RequiredArgsConstructor
@Tag(name = "系统管理")
public class AdminController {

    private final AdminService adminService;
    private final TokenUtils tokenUtils;

    /**
     * 上传法律文档
     */
    @PostMapping(value = "/law/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    @Operation(summary = "上传法律文档")
    public Result<LawDocument> uploadLaw(
            @Parameter(description = "文件", required = true)
            @RequestParam("file") MultipartFile file,
            @Parameter(description = "文档类型: law-法律法规/interpretation-司法解释/template-合同范本/other-其他", required = true)
            @RequestParam("type") String type,
            @Parameter(description = "生效日期(yyyy-MM-dd)")
            @RequestParam(required = false) String effectiveDate,
            @Parameter(description = "文档说明")
            @RequestParam(required = false) String description,
            @RequestHeader("Authorization") String authorization) {
        Integer userId = tokenUtils.getUserId(authorization);
        if (userId == null) {
            return Result.error(401, "未登录或token已过期");
        }

        LawUploadDTO dto = new LawUploadDTO();
        dto.setType(parseLawType(type));
        if (effectiveDate != null && !effectiveDate.isEmpty()) {
            dto.setEffectiveDate(java.time.LocalDate.parse(effectiveDate));
        }
        dto.setDescription(description);

        return adminService.uploadLawDocument(userId, file, dto, authorization);
    }

    /**
     * 获取法律列表
     */
    @GetMapping("/law/list")
    @Operation(summary = "获取法律列表")
    public Result<List<LawDocument>> lawList() throws JsonProcessingException {
        return adminService.getLawDocumentList();
    }

    /**
     * 删除文档
     */
    @DeleteMapping("/law/{id}")
    @Operation(summary = "删除文档")
    public Result<String> deleteLaw(@PathVariable Long id) {
        return adminService.deleteLawDocument(id);
    }

    /**
     * 解析法律文档类型
     */
    private com.example.contractreview.enums.LawType parseLawType(String type) {
        try {
            return com.example.contractreview.enums.LawType.valueOf(type.toUpperCase());
        } catch (Exception e) {
            return com.example.contractreview.enums.LawType.OTHER;
        }
    }

    /**
     * 预览文档 - 获取文件内容
     */
    @GetMapping("/law/{id}/file")
    @Operation(summary = "获取法律文档文件")
    public ResponseEntity<Resource> getLawFile(@PathVariable Long id) {
        // 获取文档信息
        Result<LawDocument> result = adminService.getLawDocumentById(id);
        if (result.getCode() != 200 || result.getData() == null) {
            return ResponseEntity.notFound().build();
        }

        LawDocument doc = result.getData();
        Path path = Paths.get(doc.getFilePath());
        Resource resource;
        try {
            resource = new UrlResource(path.toUri());
        } catch (MalformedURLException e) {
            return ResponseEntity.notFound().build();
        }

        if (!resource.exists() || !resource.isReadable()) {
            return ResponseEntity.notFound().build();
        }

        // 确定Content-Type
        String contentType = determineContentType(doc.getFileType());
        String encodedFileName = URLEncoder.encode(doc.getName(), StandardCharsets.UTF_8)
                .replace("+", "%20");

        return ResponseEntity.ok()
                .contentType(MediaType.parseMediaType(contentType))
                .header(HttpHeaders.CONTENT_DISPOSITION, "inline; filename*=UTF-8''" + encodedFileName)
                .body(resource);
    }

    /**
     * 确定文件Content-Type
     */
    private String determineContentType(String fileType) {
        if (fileType == null) {
            return MediaType.APPLICATION_OCTET_STREAM_VALUE;
        }
        return switch (fileType.toLowerCase()) {
            case "pdf" -> MediaType.APPLICATION_PDF_VALUE;
            case "docx" -> "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
            case "doc" -> "application/msword";
            default -> MediaType.APPLICATION_OCTET_STREAM_VALUE;
        };
    }

    /**
     * 系统公告发布
     */
    @PostMapping("/announcement")
    @Operation(summary = "系统公告发布")
    public Result<Notice> announcement(@RequestHeader("Authorization") String authorization,
                                       @RequestBody @Valid NoticePublishDTO noticePublishDTO) throws JsonProcessingException {
        return adminService.publishNotice(authorization, noticePublishDTO);
    }

    /**
     * 获取公告列表
     */
    @GetMapping("/announcement/list")
    @Operation(summary = "获取公告列表")
    public Result<List<NoticeVO>> announcementList() throws JsonProcessingException {
        return adminService.getAnnouncementList();
    }

    /**
     * 编辑公告
     */
    @PutMapping("/announcement/{id}")
    @Operation(summary = "编辑公告")
    public Result<Notice> editAnnouncement(@RequestBody @Valid NoticePublishDTO noticePublishDTO,
                                           @PathVariable Integer id) {
        return adminService.editNotice(id, noticePublishDTO);
    }

    /**
     * 删除公告
     */
    @DeleteMapping("/announcement/{id}")
    @Operation(summary = "删除公告")
    public Result<String> deleteAnnouncement(@PathVariable Integer id) {
        return adminService.deleteAnnouncement(id);
    }

    /**
     * 置顶/取消置顶
     */
    @PutMapping("/announcement/{id}/top")
    @Operation(summary = "置顶/取消置顶")
    public Result<String> topAnnouncement(@PathVariable Integer id,
                                  @RequestBody TopAnnounceDTO topAnnounceDTO) {
        return adminService.topAnnouncement(id, topAnnounceDTO);
    }

    /**
     * 获取用户列表
     */
    @GetMapping("/users")
    @Operation(summary = "获取用户列表")
    public Result<PageResult<User>> userList(
            @Parameter(description = "页码，默认1")
            @RequestParam(required = false, defaultValue = "1") Integer pageNum,
            @Parameter(description = "每页大小，默认10")
            @RequestParam(required = false, defaultValue = "10") Integer pageSize) throws JsonProcessingException {
        return adminService.getUserList(pageNum, pageSize);
    }

    /**
     * 编辑用户信息
     */
    @PutMapping("/users/{id}")
    @Operation(summary = "编辑用户信息")
    public Result<String> editUser(
            @Parameter(description = "用户ID")
            @PathVariable Long id,
            @Valid @RequestBody AdminUpdateUserDTO dto) {
        return adminService.editUser(id, dto);
    }

    /**
     * 启用/禁用用户
     */
    @PutMapping("/users/{id}/status")
    @Operation(summary = "启用/禁用用户")
    public Result<String> statusUser(
            @Parameter(description = "用户ID") @PathVariable Long id,
            @Parameter(description = "状态：ENABLED-启用，DISABLED-禁用") @RequestParam UserStatus status) {
        return adminService.updateUserStatus(id, status);
    }

    /**
     * 删除用户
     */
    @DeleteMapping("/users/{id}")
    @Operation(summary = "删除用户")
    public Result<String> deleteUser(
            @Parameter(description = "用户ID")
            @PathVariable Long id) {
        return adminService.deleteUser(id);
    }

    /**
     * 上传系统文档
     */
    @PostMapping(value = "/system-docs/upload", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    @Operation(summary = "上传系统文档")
    public Result<SystemDocument> uploadSystemDoc(@RequestParam("file") MultipartFile file,
                                                  @RequestParam("category") String category,
                                                  @RequestParam(required = false) List<String> tags,
                                                  @RequestParam(required = false) String description,
                                                  @RequestHeader("Authorization") String authorization){
        return adminService.uploadSystemDocument(authorization, file, category, tags, description);
    }

    /**
     * 获取系统文档列表
     */
    @GetMapping("/system-docs/list")
    @Operation(summary = "获取系统文档列表")
    public Result<List<SelectSystemDocumentListVO>> getSystemDocList() throws JsonProcessingException {
        return adminService.getSystemDocumentList();
    }

    /**
     * 删除系统文档
     */
    @DeleteMapping("/system-docs/{id}")
    @Operation(summary = "删除系统文档")
    public Result<String> deleteSystemDoc(@PathVariable Integer id){
        return adminService.deleteSystemDocument(id);
    }

    /**
     * 获取系统文档文件 - 用于预览
     */
    @GetMapping("/system-docs/{id}/file")
    @Operation(summary = "获取系统文档文件")
    public ResponseEntity<Resource> getSystemDoc(@PathVariable Integer id) {
        // 如果id为0，返回示例文件
        if (id == 0) {
            return getSystemDocExampleFile();
        }

        // 获取文档信息
        Result<SystemDocument> result = adminService.getSystemDocumentFile(id);
        if (result.getCode() != 200 || result.getData() == null) {
            return ResponseEntity.notFound().build();
        }

        SystemDocument doc = result.getData();
        Path path = Paths.get(doc.getFilePath());
        Resource resource;
        try {
            resource = new UrlResource(path.toUri());
        } catch (MalformedURLException e) {
            return ResponseEntity.notFound().build();
        }

        if (!resource.exists() || !resource.isReadable()) {
            return ResponseEntity.notFound().build();
        }

        // 确定Content-Type
        String fileType = getFileExtension(doc.getName());
        String contentType = determineContentType(fileType);
        String encodedFileName = URLEncoder.encode(doc.getName(), StandardCharsets.UTF_8)
                .replace("+", "%20");

        return ResponseEntity.ok()
                .contentType(MediaType.parseMediaType(contentType))
                .header(HttpHeaders.CONTENT_DISPOSITION, "inline; filename*=UTF-8''" + encodedFileName)
                .body(resource);
    }

    /**
     * 获取系统文档示例文件
     */
    private ResponseEntity<Resource> getSystemDocExampleFile() {
        // 示例文件路径 - 相对于项目根目录
        Path examplePath = Paths.get("upload/example/system-doc-example.md");
        Resource resource;
        try {
            resource = new UrlResource(examplePath.toUri());
        } catch (MalformedURLException e) {
            return ResponseEntity.notFound().build();
        }

        // 如果示例文件不存在，尝试使用类路径下的资源
        if (!resource.exists() || !resource.isReadable()) {
            try {
                resource = new org.springframework.core.io.ClassPathResource("example/system-doc-example.md");
            } catch (Exception ex) {
                return ResponseEntity.notFound().build();
            }
        }

        if (!resource.exists() || !resource.isReadable()) {
            return ResponseEntity.notFound().build();
        }

        String contentType = "text/markdown; charset=UTF-8";
        String encodedFileName = URLEncoder.encode("系统文档示例.md", StandardCharsets.UTF_8)
                .replace("+", "%20");

        return ResponseEntity.ok()
                .contentType(MediaType.parseMediaType(contentType))
                .header(HttpHeaders.CONTENT_DISPOSITION, "inline; filename*=UTF-8''" + encodedFileName)
                .body(resource);
    }

    /**
     * 获取文件扩展名
     */
    private String getFileExtension(String fileName) {
        if (fileName == null || !fileName.contains(".")) {
            return "";
        }
        return fileName.substring(fileName.lastIndexOf(".") + 1).toLowerCase();
    }
}
