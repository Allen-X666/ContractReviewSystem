package com.example.contractreview.service;

import com.example.contractreview.common.Result;
import com.example.contractreview.model.vo.ContractPreviewVO;
import com.example.contractreview.model.vo.ContractStatsVO;
import com.example.contractreview.model.vo.ContractVOPackage.UploadResultVO;
import com.example.contractreview.model.vo.ContractVO;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.constraints.NotNull;
import org.springframework.core.io.Resource;
import org.springframework.http.ResponseEntity;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

public interface ContractService {

    // 上传合同
    Result<UploadResultVO> uploadContract(String authorization, @NotNull(message = "文件不能为空") MultipartFile file);

    // 批量上传合同
    Result<List<UploadResultVO>> batchUploadContracts(String authorization, List<MultipartFile> files);

    // 获取合同列表
    Result<List<ContractVO>> getContractList(String authorization, Integer page, Integer pageSize, String keyword);

    // 删除合同
    Result<String> deleteContract(String authorization, Long contractId);

    // 批量删除合同
    Result<String> batchDeleteContracts(String authorization, List<Long> contractIds);

    // 获取合同统计数据
    Result<ContractStatsVO> getContractStats(String authorization);

    // 获取合同预览信息
    Result<ContractPreviewVO> getContractPreview(String authorization, Long contractId);

    // 获取合同文件（用于预览）
    ResponseEntity<Resource> getContractFile(String authorization, Long contractId, HttpServletRequest request);

    // 下载合同文件
    ResponseEntity<Resource> downloadContractFile(String authorization, Long contractId, HttpServletRequest request);
}
