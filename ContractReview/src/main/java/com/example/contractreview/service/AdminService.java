package com.example.contractreview.service;

import com.example.contractreview.common.PageResult;
import com.example.contractreview.common.Result;
import com.example.contractreview.model.dto.AdminUpdateUserDTO;
import com.example.contractreview.model.dto.LawUploadDTO;
import com.example.contractreview.model.dto.NoticePublishDTO;
import com.example.contractreview.model.dto.TopAnnounceDTO;
import com.example.contractreview.model.entity.LawDocument;
import com.example.contractreview.model.entity.Notice;
import com.example.contractreview.model.entity.SystemDocument;
import com.example.contractreview.model.entity.User;
import com.example.contractreview.enums.UserStatus;
import com.example.contractreview.model.vo.NoticeVO;
import com.example.contractreview.model.vo.SelectSystemDocumentListVO;
import com.fasterxml.jackson.core.JsonProcessingException;
import jakarta.validation.Valid;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

/**
 * 管理员服务接口
 */
public interface AdminService {

    // 获取用户列表
    Result<PageResult<User>> getUserList(Integer pageNum, Integer pageSize) throws JsonProcessingException;

    // 编辑用户
    Result<String> editUser(Long userId, AdminUpdateUserDTO dto);

    // 更新用户状态
    Result<String> updateUserStatus(Long userId, UserStatus status);

    // 删除用户
    Result<String> deleteUser(Long userId);

    // 上传法律文档
    Result<LawDocument> uploadLawDocument(Integer userId, MultipartFile file, LawUploadDTO dto, String authorization);

    // 获取法律文档列表
    Result<List<LawDocument>> getLawDocumentList() throws JsonProcessingException;

    // 删除法律文档
    Result<String> deleteLawDocument(Long id);

    // 获取法律文档
    Result<LawDocument> getLawDocumentById(Long id);

    // 发布公告
    Result<Notice> publishNotice(String authorization, @Valid NoticePublishDTO noticePublishDTO) throws JsonProcessingException;

    // 获取公告列表
    Result<List<NoticeVO>> getAnnouncementList() throws JsonProcessingException;

    // 删除公告
    Result<String> deleteAnnouncement(Integer id);

    // 修改公告
    Result<Notice> editNotice(Integer id, @Valid NoticePublishDTO noticePublishDTO);

    // 置顶/取消置顶
    Result<String> topAnnouncement(Integer id, TopAnnounceDTO topAnnounceDTO);

    // 上传系统文档
    Result<SystemDocument> uploadSystemDocument(String authorization, MultipartFile file, String category, List<String> tags, String description);

    // 获取系统文档列表
    Result<List<SelectSystemDocumentListVO>> getSystemDocumentList() throws JsonProcessingException;

    // 删除系统文档
    Result<String> deleteSystemDocument(Integer id);

    // 获取系统文档文件
    Result<SystemDocument> getSystemDocumentFile(Integer id);
}
