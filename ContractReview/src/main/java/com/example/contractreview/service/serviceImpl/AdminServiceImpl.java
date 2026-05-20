package com.example.contractreview.service.serviceImpl;

import com.example.contractreview.common.PageResult;
import com.example.contractreview.common.Result;
import com.example.contractreview.common.ResultCode;
import com.example.contractreview.constant.*;
import com.example.contractreview.enums.NoticeStatus;
import com.example.contractreview.enums.NotificationType;
import com.example.contractreview.enums.PublishType;
import com.example.contractreview.enums.UserStatus;
import com.example.contractreview.mapper.*;
import com.example.contractreview.model.dto.AdminUpdateUserDTO;
import com.example.contractreview.model.dto.LawUploadDTO;
import com.example.contractreview.model.dto.NoticePublishDTO;
import com.example.contractreview.model.dto.TopAnnounceDTO;
import com.example.contractreview.model.entity.*;
import com.example.contractreview.model.vo.NoticeVO;
import com.example.contractreview.client.FastApiClient;
import com.example.contractreview.model.vo.SelectSystemDocumentListVO;
import com.example.contractreview.service.AdminService;
import com.example.contractreview.sse.SseEmitterManager;
import com.example.contractreview.utils.GetUserSystemConfigUtils;
import com.example.contractreview.utils.LawFileParser;
import com.example.contractreview.utils.TokenUtils;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.github.pagehelper.PageHelper;
import com.github.pagehelper.PageInfo;
import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.LocalDateTime;
import java.util.*;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;

/**
 * 管理员服务实现类
 */
@Service
@Slf4j
@RequiredArgsConstructor
public class AdminServiceImpl implements AdminService {

    private final AuthMapper authMapper;
    private final AdminMapper adminMapper;
    private final SystemConfigMapper systemConfigMapper;
    private final LawMapper lawMapper;
    private final NoticeMapper noticeMapper;
    private final StringRedisTemplate stringRedisTemplate;
    private final TokenUtils tokenUtils;
    private final ObjectMapper objectMapper;
    private final FastApiClient fastApiClient;
    private final SseEmitterManager sseEmitterManager;
    private final GetUserSystemConfigUtils getUserSystemConfigUtils;

    /**
     * 获取用户列表
     * 优化：排序逻辑由 SQL ORDER BY 实现，避免内存排序
     */
    @Override
    public Result<PageResult<User>> getUserList(Integer pageNum, Integer pageSize) throws JsonProcessingException {
        pageNum = pageNum == null || pageNum < 1 ? 1 : pageNum;
        pageSize = pageSize == null || pageSize < 1 ? 10 : pageSize;
        PageHelper.startPage(pageNum, pageSize);
        // SQL 已按角色排序（ADMIN在前）和创建时间倒序
        List<User> userList = authMapper.selectAllUsers();
        PageInfo<User> pageInfo = new PageInfo<>(userList);
        PageResult<User> pageResult = PageResult.of(
                pageInfo.getPageNum(),
                pageInfo.getPageSize(),
                pageInfo.getTotal(),
                pageInfo.getList()
        );
        String key = UserConstant.USER_List;
        stringRedisTemplate.opsForValue().set(key,objectMapper.writeValueAsString(pageResult));
        return Result.success(pageResult);
    }

    /**
     * 编辑用户信息
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public Result<String> editUser(Long userId, AdminUpdateUserDTO dto) {
        Result<String> existsResult = validateUserExists(userId);
        if (!existsResult.isSuccess()) {
            return Result.error(existsResult.getCode(), existsResult.getMessage());
        }

        Result<String> uniqueResult = validateFieldUnique("username", dto.getUsername(), userId,
                ResultCode.USER_ALREADY_EXISTS, "用户名已存在");
        if (!uniqueResult.isSuccess()) {
            return Result.error(uniqueResult.getCode(), uniqueResult.getMessage());
        }

        uniqueResult = validateFieldUnique("email", dto.getEmail(), userId,
                ResultCode.EMAIL_ALREADY_EXISTS, "邮箱已被使用");
        if (!uniqueResult.isSuccess()) {
            return Result.error(uniqueResult.getCode(), uniqueResult.getMessage());
        }

        uniqueResult = validateFieldUnique("phone", dto.getPhone(), userId,
                ResultCode.PHONE_ALREADY_EXISTS, "手机号已被使用");
        if (!uniqueResult.isSuccess()) {
            return Result.error(uniqueResult.getCode(), uniqueResult.getMessage());
        }

        int affectedRows = authMapper.updateByAdmin(userId, dto);
        return handleOperationResult(affectedRows, "更新成功", "更新失败",
                () -> {
                    clearUserCache(userId);
                    log.info("管理员更新用户信息成功, userId: {}", userId);
                });
    }

    /**
     * 启用/禁用用户
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public Result<String> updateUserStatus(Long userId, UserStatus status) {
        Result<String> existsResult = validateUserExists(userId);
        if (!existsResult.isSuccess()) {
            return Result.error(existsResult.getCode(), existsResult.getMessage());
        }

        int affectedRows = authMapper.updateStatus(userId, status);
        String action = status == UserStatus.ENABLED ? "启用" : "禁用";
        return handleOperationResult(affectedRows, action + "成功", "操作失败",
                () -> {
                    clearUserCache(userId);
                    log.info("管理员{}用户成功, userId: {}", action, userId);
                });
    }

    /**
     * 删除用户
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public Result<String> deleteUser(Long userId) {
        Result<String> existsResult = validateUserExists(userId);
        if (!existsResult.isSuccess()) {
            return Result.error(existsResult.getCode(), existsResult.getMessage());
        }

        // 1. 删除用户存储设置（外键关联数据）
        systemConfigMapper.deleteByUserId(userId);
        log.debug("删除用户存储设置, userId: {}", userId);

        // 2. 删除用户
        int affectedRows = authMapper.deleteById(userId);
        return handleOperationResult(affectedRows, "删除成功", "删除失败",
                () -> {
                    clearUserCache(userId);
                    log.info("管理员删除用户成功, userId: {}", userId);
                });
    }

    /**
     * 校验用户是否存在，不存在则返回错误结果
     */
    private Result<String> validateUserExists(Long userId) {
        User existingUser = authMapper.selectById(userId.intValue());
        if (existingUser == null) {
            return Result.error(ResultCode.USER_NOT_FOUND, "用户不存在");
        }
        return Result.success();
    }

    /**
     * 校验字段唯一性
     */
    private Result<String> validateFieldUnique(String field, String value, Long excludeId,
                                                ResultCode errorCode, String errorMsg) {
        if (!StringUtils.hasText(value)) {
            return Result.success();
        }

        boolean exists = switch (field) {
            case "username" -> authMapper.existsByUsernameExcludeId(value, excludeId);
            case "email" -> authMapper.existsByEmailExcludeId(value, excludeId);
            case "phone" -> authMapper.existsByPhoneExcludeId(value, excludeId);
            default -> false;
        };

        if (exists) {
            return Result.error(errorCode, errorMsg);
        }
        return Result.success();
    }

    /**
     * 处理数据库操作结果
     */
    private Result<String> handleOperationResult(int affectedRows, String successMsg,
                                                  String errorMsg, Runnable afterSuccess) {
        if (affectedRows > 0) {
            if (afterSuccess != null) {
                afterSuccess.run();
            }
            return Result.success(successMsg);
        }
        return Result.error(errorMsg);
    }

    /**
     * 清除用户相关缓存
     */
    private void clearUserCache(Long userId) {

        try {
            String userListKey = UserConstant.USER_List;
            String userInfoKey = UserConstant.USER_INFO + userId;
            String userTokenKey = UserConstant.USER_TOKEN_MAP + userId;
            String notificationKey = UserConstant.USER_NOTIFICATION_SETTINGS + userId;
            String storageUploadKey = StorageConstant.UPLOAD_PATH_KEY + userId;
            String storageDownloadKey = StorageConstant.DOWNLOAD_PATH_KEY + userId;

            stringRedisTemplate.delete(userListKey);
            stringRedisTemplate.delete(userInfoKey);
            stringRedisTemplate.delete(userTokenKey);
            stringRedisTemplate.delete(notificationKey);
            stringRedisTemplate.delete(storageUploadKey);
            stringRedisTemplate.delete(storageDownloadKey);

            log.debug("清除用户缓存成功, userId: {}", userId);
        } catch (Exception e) {
            log.warn("清除用户缓存失败, userId: {}, error: {}", userId, e.getMessage());
        }
    }

    /**
     * 上传法律文档
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public Result<LawDocument> uploadLawDocument(Integer userId, MultipartFile file, LawUploadDTO dto, String authorization) {
        // 1. 校验文件
        if (file == null || file.isEmpty()) {
            return Result.error(ResultCode.BAD_REQUEST.getCode(), "文件不能为空");
        }

        // 校验文件类型
        String originalFilename = file.getOriginalFilename();
        if (originalFilename == null) {
            return Result.error(ResultCode.BAD_REQUEST.getCode(), "文件名不能为空");
        }

        String fileExtension = getFileExtension(originalFilename).toLowerCase();
        if (!isValidLawFileType(fileExtension)) {
            return Result.error(ResultCode.FILE_TYPE_NOT_SUPPORTED.getCode(), "不支持的文件类型，仅支持 PDF、DOC、MarkDown 格式");
        }

        // 校验文件大小 (50MB)
        long maxSize = 50 * 1024 * 1024;
        if (file.getSize() > maxSize) {
            return Result.error(ResultCode.FILE_TOO_LARGE.getCode(), "文件大小不能超过50MB");
        }

        // 2. 调用FastAPI上传法律文档
        try {
            String effectiveDateStr = dto.getEffectiveDate() != null ? dto.getEffectiveDate().toString() : null;
            String documentType = dto.getType() != null ? dto.getType().name().toLowerCase() : "other";

            var fastApiResult = fastApiClient.uploadLawDocument(
                    file,
                    documentType,
                    effectiveDateStr,
                    dto.getDescription(),
                    authorization
            );

            if (fastApiResult == null || fastApiResult.getCode() != 200) {
                String errorMsg = fastApiResult != null ? fastApiResult.getMessage() : "FastAPI返回结果为空";
                log.error("FastAPI上传法律文档失败: {}", errorMsg);
                return Result.error(ResultCode.ERROR.getCode(), "上传法律文档到AI服务失败: " + errorMsg);
            }

            log.info("FastAPI上传法律文档成功, result: {}", fastApiResult.getData());

            List<LawFileParser.ParseResult> parseResults = LawFileParser.parseAll(file);
            if (parseResults.isEmpty()) {
                return Result.error(ResultCode.ERROR.getCode(), "无法解析法律文档");
            }

            // 1. 收集所有法规名称
            List<String> regulationNames = parseResults.stream()
                    .map(r -> r.getLawRegulation().getName())
                    .toList();

            // 2. 批量查询已存在的法规
            List<LawRegulation> existingRegulations = adminMapper.selectByNames(regulationNames);
            Map<String, Long> nameToIdMap = existingRegulations.stream()
                    .collect(Collectors.toMap(LawRegulation::getName, LawRegulation::getId));

            // 3. 分离需要插入的新法规
            List<LawRegulation> newRegulations = parseResults.stream()
                    .map(LawFileParser.ParseResult::getLawRegulation)
                    .filter(r -> !nameToIdMap.containsKey(r.getName()))
                    .toList();

            // 4. 批量插入新法规
            if (!newRegulations.isEmpty()) {
                adminMapper.insertLawRegulation(newRegulations);
                // 将新插入的法规ID加入映射
                for (LawRegulation reg : newRegulations) {
                    nameToIdMap.put(reg.getName(), reg.getId());
                    log.info("插入新法规，生成ID: {}，名称: {}", reg.getId(), reg.getName());
                }
            }

            log.info("法规处理完成，共 {} 个，其中已存在 {} 个，新插入 {} 个",
                    regulationNames.size(), existingRegulations.size(), newRegulations.size());

            // 5. 收集所有法条并设置law_id
            List<LawArticle> allLawArticles = new ArrayList<>();
            for (LawFileParser.ParseResult parseResult : parseResults) {
                String regName = parseResult.getLawRegulation().getName();
                Long lawId = nameToIdMap.get(regName);

                for (LawArticle article : parseResult.getLawArticles()) {
                    article.setLawId(lawId);
                    allLawArticles.add(article);
                }
            }

            // 6. 批量插入所有法条
            if (!allLawArticles.isEmpty()) {
                adminMapper.insertLawArticles(allLawArticles);
                log.info("批量插入法条共 {} 条", allLawArticles.size());
            }

            // 3. 获取存储路径（本地备份）
            String basePath = getStoragePath(userId);
            if (basePath == null || basePath.isEmpty()) {
                return Result.error(ResultCode.ERROR.getCode(), "无法获取存储路径");
            }

            // 4. 构建 LowDocuments 文件夹路径
            Path legalDocsPath = Paths.get(basePath, "LowDocuments");
            try {
                // 如果文件夹不存在则创建
                if (!Files.exists(legalDocsPath)) {
                    Files.createDirectories(legalDocsPath);
                    log.info("创建 LowDocuments 文件夹: {}", legalDocsPath);
                }
            } catch (IOException e) {
                log.error("创建 LowDocuments 文件夹失败: {}", legalDocsPath, e);
                return Result.error(ResultCode.ERROR.getCode(), "创建存储目录失败");
            }

            // 5. 生成唯一文件名
            String uniqueFileName = UUID.randomUUID().toString().replace("-", "") + "." + fileExtension;
            Path targetPath = legalDocsPath.resolve(uniqueFileName);

            // 6. 保存文件到本地
            try {
                file.transferTo(targetPath.toFile());
                String key = LawConstant.LAW_LIST_KEY_PREFIX;
                String statusKey = KnowledgeConstant.KNOWLEDGE_STATS_KEY;
                stringRedisTemplate.delete(key);
                stringRedisTemplate.delete(statusKey);
                Set<String> keys = stringRedisTemplate.keys(KnowledgeConstant.LAW_DETAIL_KEY_PREFIX); // 获取所有以 a 开头的 key
                if (keys != null && !keys.isEmpty()) {
                    stringRedisTemplate.delete(keys);
                }
                log.info("法律文档本地保存成功: {}", targetPath);
            } catch (IOException e) {
                log.error("保存法律文档到本地失败: {}", targetPath, e);
                return Result.error(ResultCode.FILE_UPLOAD_ERROR.getCode(), "文件本地保存失败");
            }

            // 7. 保存到数据库
            LawDocument document = LawDocument.builder()
                    .name(originalFilename)
                    .type(dto.getType())
                    .filePath(targetPath.toString())
                    .fileSize(file.getSize())
                    .fileType(fileExtension)
                    .effectiveDate(dto.getEffectiveDate())
                    .description(dto.getDescription())
                    .uploadUserId(userId)
                    .build();

            int affectedRows = lawMapper.insertLawDocument(document);
            if (affectedRows <= 0) {
                // 删除已保存的文件
                try {
                    Files.deleteIfExists(targetPath);
                } catch (IOException e) {
                    log.warn("删除失败文件失败: {}", targetPath, e);
                }
                return Result.error(ResultCode.ERROR.getCode(), "保存文档信息失败");
            }

            log.info("法律文档上传成功, documentId: {}, userId: {}", document.getId(), userId);
            return Result.success(document);

        } catch (Exception e) {
            log.error("调用FastAPI上传法律文档异常: {}", e.getMessage(), e);
            return Result.error(ResultCode.ERROR.getCode(), "AI服务调用失败: " + e.getMessage());
        }
    }

    /**
     * 获取法律文档列表
     */
    @Override
    public Result<List<LawDocument>> getLawDocumentList() throws JsonProcessingException {
        String key = LawConstant.LAW_LIST_KEY_PREFIX;
        String cachLawDocument = stringRedisTemplate.opsForValue().get(key);
        if (cachLawDocument != null) {
            List<LawDocument> documents = objectMapper.readValue(cachLawDocument, new TypeReference<List<LawDocument>>() {});
            return Result.success(documents, (long) documents.size());
        }
        List<LawDocument> documents = lawMapper.selectAllLawDocuments();
        stringRedisTemplate.opsForValue().set(key, objectMapper.writeValueAsString(documents));
        return Result.success(documents, (long) documents.size());
    }

    /**
     * 删除法律文档
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public Result<String> deleteLawDocument(Long id) {
        // 查询文档
        LawDocument document = lawMapper.selectLawDocumentById(id);
        if (document == null) {
            return Result.error(ResultCode.NOT_FOUND, "文档不存在");
        }

        // 删除数据库记录
        int affectedRows = lawMapper.deleteLawDocumentById(id);
        if (affectedRows <= 0) {
            return Result.error(ResultCode.ERROR.getCode(), "删除文档记录失败");
        }

        // 删除物理文件
        try {
            Path filePath = Paths.get(document.getFilePath());
            Files.deleteIfExists(filePath);
            log.info("删除法律文档文件成功: {}", filePath);
        } catch (IOException e) {
            log.warn("删除法律文档文件失败: {}", document.getFilePath(), e);
            // 文件删除失败不影响返回成功，因为数据库记录已删除
        }
        String key = LawConstant.LAW_LIST_KEY_PREFIX;
        stringRedisTemplate.delete(key);
        log.info("法律文档删除成功, documentId: {}", id);
        return Result.success("删除成功");
    }

    /**
     * 根据ID获取法律文档
     */
    @Override
    public Result<LawDocument> getLawDocumentById(Long id) {
        LawDocument document = lawMapper.selectLawDocumentById(id);
        return Result.success(document);
    }

    /**
     * 构建公告实体（从DTO）
     */
    private Notice buildNoticeFromDTO(NoticePublishDTO dto, Long authorId) {
        Notice notice = Notice.builder()
                .title(dto.getTitle())
                .type(dto.getType())
                .content(dto.getContent())
                .publishType(dto.getPublishType())
                .isTop(dto.getIsTop() != null ? dto.getIsTop() : false)
                .build();

        if (authorId != null) {
            notice.setAuthorId(authorId);
        }

        // 处理发布时间和状态
        if (dto.getPublishType() == PublishType.IMMEDIATE) {
            notice.setPublishTime(LocalDateTime.now());
            notice.setStatus(NoticeStatus.PUBLISHED);
        } else {
            notice.setPublishTime(dto.getPublishTime());
            notice.setStatus(NoticeStatus.PENDING);
        }

        return notice;
    }

    /**
     * 验证公告发布时间
     */
    private Result<Void> validatePublishTime(NoticePublishDTO dto) {
        if (dto.getPublishType() == PublishType.SCHEDULED && dto.getPublishTime() == null) {
            return Result.error(ResultCode.BAD_REQUEST.getCode(), "定时发布时间不能为空");
        }
        return Result.success();
    }

    /**
     * 清除公告列表缓存
     */
    private void clearAnnouncementCache() {
        String key = AnnouncementConstant.ANNOUNCEMENT_LIST_KEY;
        stringRedisTemplate.delete(key);
    }

    /**
     * 发布系统公告
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public Result<Notice> publishNotice(String authorization,
                                        NoticePublishDTO noticePublishDTO) throws JsonProcessingException {
        Integer userId = tokenUtils.getUserId(authorization);
        if (userId == null) {
            return Result.error(ResultCode.UNAUTHORIZED.getCode(), "用户未登录");
        }

        // 验证发布时间
        Result<Void> validationResult = validatePublishTime(noticePublishDTO);
        if (!validationResult.isSuccess()) {
            return Result.error(validationResult.getCode(), validationResult.getMessage());
        }

        // 构建并保存公告
        Notice notice = buildNoticeFromDTO(noticePublishDTO, userId.longValue());
        int affectedRows = noticeMapper.insert(notice);

        clearAnnouncementCache();

        if (affectedRows <= 0) {
            log.error("公告发布失败, userId: {}, title: {}", userId, noticePublishDTO.getTitle());
            return Result.error(ResultCode.ERROR.getCode(), "公告发布失败");
        }
        Map<String, String> userSystemConfig = getUserSystemConfigUtils.getUserSystemConfig(userId);
        String message = userSystemConfig.get("message");
        if (message.equals("获取用户系统配置成功")) {
            String systemNotice = userSystemConfig.get("systemNotice");
            if (systemNotice.equals("true")) {
                log.info("开始发送系统公告提示");
                // 发送SSE系统公告通知给所有在线用户
                try {
                    // 使用 broadcastSystemAnnouncement 方法广播给所有在线用户
                    int connectionCount = sseEmitterManager.broadcastSystemAnnouncement(
                            notice.getTitle(),
                            notice.getContent()
                    );
                    log.info("系统公告SSE通知已广播, noticeId: {}, title: {}, 目标用户数: {}",
                            notice.getId(), notice.getTitle(), connectionCount);
                } catch (Exception e) {
                    log.error("发送系统公告SSE通知失败, noticeId: {}", notice.getId(), e);
                }
            }
            else {
                log.info("用户未开启邮件通知");
            }
        }
        log.info("公告发布成功, noticeId: {}, userId: {}, title: {}", notice.getId(), userId, notice.getTitle());
        return Result.success("发布成功", notice);
    }

    /**
     * 获取系统公告列表
     */
    @Override
    public Result<List<NoticeVO>> getAnnouncementList() throws JsonProcessingException {
        List<NoticeVO> notices;
        if (stringRedisTemplate.hasKey(AnnouncementConstant.ANNOUNCEMENT_LIST_KEY)) {
            String cachedNotices = stringRedisTemplate.opsForValue().get(AnnouncementConstant.ANNOUNCEMENT_LIST_KEY);
            notices = objectMapper.readValue(cachedNotices, new TypeReference<List<NoticeVO>>() {});
            return Result.success(notices, (long) notices.size());
        }
        try {
            notices = noticeMapper.selectAll();
        } catch (Exception e){
            log.error("获取系统公告列表失败", e);
            return Result.error(ResultCode.ERROR.getCode(), "获取系统公告列表失败");
        }
        String key = AnnouncementConstant.ANNOUNCEMENT_LIST_KEY;
        stringRedisTemplate.opsForValue().set(key, objectMapper.writeValueAsString(notices));
        return Result.success(notices, (long) notices.size());
    }

    /**
     * 删除系统公告
     */
    @Override
    public Result<String> deleteAnnouncement(@NotBlank Integer id) {
        int affectedRows = noticeMapper.deleteById(id);
        if (affectedRows <= 0) {
            return Result.error(ResultCode.ERROR.getCode(), "删除系统公告失败");
        }
        clearAnnouncementCache();
        return Result.success("删除公告成功");
    }

    /**
     * 编辑公告
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public Result<Notice> editNotice(Integer id, @Valid NoticePublishDTO noticePublishDTO) {
        // 1. 查询公告是否存在
        Notice existingNotice = noticeMapper.selectById(id);
        if (existingNotice == null) {
            return Result.error(ResultCode.NOT_FOUND.getCode(), "公告不存在");
        }

        // 2. 验证发布时间
        Result<Void> validationResult = validatePublishTime(noticePublishDTO);
        if (!validationResult.isSuccess()) {
            return Result.error(validationResult.getCode(), validationResult.getMessage());
        }

        // 3. 构建更新后的公告实体（编辑时不修改作者）
        Notice notice = buildNoticeFromDTO(noticePublishDTO, null);
        notice.setId(id.longValue());

        // 4. 更新数据库
        int affectedRows = noticeMapper.update(notice, id);
        if (affectedRows <= 0) {
            log.error("公告编辑失败, id: {}, title: {}", id, noticePublishDTO.getTitle());
            return Result.error(ResultCode.ERROR.getCode(), "公告编辑失败");
        }

        // 5. 清除缓存
        clearAnnouncementCache();

        log.info("公告编辑成功, id: {}, title: {}", id, noticePublishDTO.getTitle());
        return Result.success("编辑成功", notice);
    }

    // 置顶/取消置顶
    @Override
    public Result<String> topAnnouncement(Integer id, TopAnnounceDTO topAnnounceDTO) {
        int isTop;
        if (topAnnounceDTO.getIsTop() == true) {
            isTop = 1;
            noticeMapper.updateTop(id, isTop);
            clearAnnouncementCache();
            return Result.success("置顶成功");
        } else {
            isTop = 0;
            noticeMapper.updateTop(id, isTop);
            clearAnnouncementCache();
            return Result.success("取消置顶成功");
        }
    }

    /**
     *  上传系统文档
     */
    @Override
    @Transactional(rollbackFor = Exception.class)
    public Result<SystemDocument> uploadSystemDocument(String authorization,
                                                       MultipartFile file,
                                                       String category,
                                                       List<String> tags,
                                                       String description) {
        Integer userId = tokenUtils.getUserId(authorization);
        // 校验文件
        if (file == null || file.isEmpty()) {
            return Result.error(ResultCode.BAD_REQUEST.getCode(), "文件不能为空");
        }

        // 校验文件类型
        String originalFilename = file.getOriginalFilename();
        if (originalFilename == null) {
            return Result.error(ResultCode.BAD_REQUEST.getCode(), "文件名不能为空");
        }

        String fileExtension = getFileExtension(originalFilename).toLowerCase();
        if (!isValidLawSystemFileType(fileExtension)) {
            return Result.error(ResultCode.FILE_TYPE_NOT_SUPPORTED.getCode(), "不支持的文件类型，仅支持 DOCX、MarkDown 格式");
        }

        // 校验文件大小 (50MB)
        long maxSize = 50 * 1024 * 1024;
        if (file.getSize() > maxSize) {
            return Result.error(ResultCode.FILE_TOO_LARGE.getCode(), "文件大小不能超过50MB");
        }

        // 获取存储路径（本地备份）
        String basePath = getStoragePath(userId);
        if (basePath == null || basePath.isEmpty()) {
            return Result.error(ResultCode.ERROR.getCode(), "无法获取存储路径");
        }

        // 构建 SystemDocument 文件夹路径
        Path legalDocsPath = Paths.get(basePath, "SystemDocument");
        try {
            // 如果文件夹不存在则创建
            if (!Files.exists(legalDocsPath)) {
                Files.createDirectories(legalDocsPath);
                log.info("创建 LowDocuments 文件夹: {}", legalDocsPath);
            }
        } catch (IOException e) {
            log.error("创建 LowDocuments 文件夹失败: {}", legalDocsPath, e);
            return Result.error(ResultCode.ERROR.getCode(), "创建存储目录失败");
        }

        // 生成唯一文件名
        String uniqueFileName = UUID.randomUUID().toString().replace("-", "") + "." + fileExtension;
        Path targetPath = legalDocsPath.resolve(uniqueFileName);

        // 保存文件到本地
        try {
            file.transferTo(targetPath.toFile());
            String key = StorageConstant.SYSTEM_DOCUMENT_LIST_KEY;
            stringRedisTemplate.delete(key);
            log.info("法律文档本地保存成功: {}", targetPath);
        } catch (IOException e) {
            log.error("保存法律文档到本地失败: {}", targetPath, e);
            return Result.error(ResultCode.FILE_UPLOAD_ERROR.getCode(), "文件本地保存失败");
        }

        // 保存元数据到数据库
        SystemDocument document = SystemDocument.builder()
                .name(file.getOriginalFilename())
                .category(category)
                .tags(tags)
                .description(description)
                .filePath(targetPath.toString())
                .fileSize(file.getSize())
                .status(1)
                .build();

        adminMapper.insertSystemDocument(document);

        // 4. 异步调用FastAPI进行文档向量化（使用本地文件路径）
        asyncProcessSystemDocVector(targetPath.toString(), document, authorization);

        return Result.success(document);
    }

    /**
     * 异步处理文档向量化
     */
    @Async
    public void asyncProcessSystemDocVector(String filePath, SystemDocument document, String authorization) {
        try {
            // 调用FastAPI进行向量化（直接传递文件路径）
            fastApiClient.uploadSystemDocumentByPath(
                    filePath,
                    document.getCategory(),
                    String.valueOf(document.getTags()),
                    document.getDescription(),
                    authorization
            );
            log.info("系统文档向量化成功, documentId: {}", document.getId());
        } catch (Exception e) {
            log.error("系统文档向量化异常, documentId: {}, filePath: {}", document.getId(), filePath, e);
        }
    }

    /**
     * 获取系统文档列表
     */
    @Override
    public Result<List<SelectSystemDocumentListVO>> getSystemDocumentList() throws JsonProcessingException {
        String key = StorageConstant.SYSTEM_DOCUMENT_LIST_KEY;
        String cacheValue = stringRedisTemplate.opsForValue().get(key);
        if (cacheValue != null) {
            List<SelectSystemDocumentListVO> documents = objectMapper.readValue(cacheValue, new TypeReference<List<SelectSystemDocumentListVO>>() {});
            return Result.success(documents);
        }

        List<SelectSystemDocumentListVO> documents = adminMapper.selectSystemDocumentList();
        stringRedisTemplate.opsForValue().set(key, objectMapper.writeValueAsString(documents));
        return Result.success(documents);
    }

    /**
     * 删除系统文档
     */
    @Override
    public Result<String> deleteSystemDocument(Integer id) {
        // 查询文档
        SystemDocument document = adminMapper.selectLawDocumentById(id);
        if (document == null) {
            return Result.error(ResultCode.NOT_FOUND, "文档不存在");
        }

        // 删除数据库记录
        int affectedRows = adminMapper.deleteLawDocumentById(id);
        if (affectedRows <= 0) {
            return Result.error(ResultCode.ERROR.getCode(), "删除文档记录失败");
        }

        // 删除物理文件
        try {
            Path filePath = Paths.get(document.getFilePath());
            Files.deleteIfExists(filePath);
            log.info("删除法律文档文件成功: {}", filePath);
        } catch (IOException e) {
            log.warn("删除法律文档文件失败: {}", document.getFilePath(), e);
            // 文件删除失败不影响返回成功，因为数据库记录已删除
        }
        String key = StorageConstant.SYSTEM_DOCUMENT_LIST_KEY;
        stringRedisTemplate.delete(key);
        log.info("法律文档删除成功, documentId: {}", id);
        return Result.success("删除成功");
    }

    /**
     * 获取系统文档文件
     */
    @Override
    public Result<SystemDocument> getSystemDocumentFile(Integer id) {
        SystemDocument document = adminMapper.selectLawDocumentById(id);
        return Result.success(document);
    }

    /**
     * 获取存储路径
     */
    private String getStoragePath(Integer userId) {
        // 1. 先从 Redis 查询
        String redisKey = StorageConstant.UPLOAD_PATH_KEY + userId;
        String path = stringRedisTemplate.opsForValue().get(redisKey);

        if (path != null && !path.isEmpty()) {
            log.debug("从 Redis 获取存储路径, userId: {}", userId);
            return path;
        }

        // 2. Redis 没有则从数据库查询
        path = systemConfigMapper.selectUploadPathByUserId(userId);

        if (path != null && !path.isEmpty()) {
            // 缓存到 Redis
            try {
                stringRedisTemplate.opsForValue().set(redisKey, path, 1, TimeUnit.HOURS);
                log.debug("存储路径缓存到 Redis, userId: {}", userId);
            } catch (Exception e) {
                log.warn("缓存存储路径到 Redis 失败, userId: {}", userId, e);
            }
        }

        return path;
    }

    /**
     * 获取文件扩展名
     */
    private String getFileExtension(String filename) {
        int lastDotIndex = filename.lastIndexOf(".");
        return lastDotIndex == -1 ? "" : filename.substring(lastDotIndex + 1);
    }

    /**
     * 校验是否为有效的法律文档文件类型
     */
    private boolean isValidLawFileType(String extension) {
        return "pdf".equals(extension) || "doc".equals(extension) || "docx".equals(extension) || "md".equals(extension);
    }

    private boolean isValidLawSystemFileType(String extension) {
        return "docx".equals(extension) || "md".equals(extension);
    }

    /**
     * 根据文件扩展名确定Content-Type
     */
    private String determineContentType(String fileExtension) {
        return switch (fileExtension.toLowerCase()) {
            case "pdf" -> "application/pdf";
            case "doc" -> "application/msword";
            case "docx" -> "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
            case "md" -> "text/markdown";
            case "txt" -> "text/plain";
            case "jpg", "jpeg" -> "image/jpeg";
            case "png" -> "image/png";
            case "gif" -> "image/gif";
            default -> "application/octet-stream";
        };
    }

    /**
     * 构建系统公告SSE通知数据
     *
     * @param notice 公告实体
     * @return SSE通知数据
     */
    private Map<String, Object> buildAnnouncementSseData(Notice notice) {
        Map<String, Object> data = new HashMap<>();
        data.put("type", "system_announcement");
        data.put("announcementId", notice.getId());
        data.put("title", notice.getTitle());
        data.put("content", notice.getContent());
        data.put("publishTime", notice.getPublishTime());
        data.put("timestamp", LocalDateTime.now());
        return data;
    }
}
