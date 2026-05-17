package com.example.contractreview.controller;

import com.example.contractreview.common.Result;
import com.example.contractreview.model.vo.ContractPreviewVO;
import com.example.contractreview.model.vo.ContractStatsVO;
import com.example.contractreview.model.vo.ContractVO;
import com.example.contractreview.model.vo.ContractVOPackage.UploadResultVO;
import com.example.contractreview.service.ContractService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.validation.constraints.NotNull;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.core.io.Resource;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

@RestController
@RequestMapping("/contract")
@Slf4j
@RequiredArgsConstructor
@Tag(name = "合同接口")
public class ContractController {

    private final ContractService contractService;

    // 上传合同
    @PostMapping("/upload")
    @Operation(summary = "上传合同")
    public Result<UploadResultVO> uploadContract(@RequestHeader("Authorization") String authorization,
                                                 @RequestParam @NotNull(message = "文件不能为空") MultipartFile file) {
        return contractService.uploadContract(authorization, file);
    }

    // 批量上传合同
    @PostMapping("/batch-upload")
    @Operation(summary = "批量上传合同")
    public Result<List<UploadResultVO>> batchUploadContracts(@RequestHeader("Authorization") String authorization,
                                                             @RequestParam @NotNull(message = "文件不能为空") List<MultipartFile> files) {
        return contractService.batchUploadContracts(authorization, files);
    }

    // 获取合同列表
    @GetMapping("/list")
    @Operation(summary = "获取合同列表")
    public Result<List<ContractVO>> getContractList(@RequestHeader("Authorization") String authorization,
                                                    @RequestParam(required = false, defaultValue = "1") Integer page,
                                                    @RequestParam(required = false, defaultValue = "10") Integer pageSize,
                                                    @RequestParam(required = false) String keyword) {
        return contractService.getContractList(authorization, page, pageSize, keyword);
    }

    // 删除合同
    @DeleteMapping("/{id}")
    @Operation(summary = "删除合同")
    public Result<String> deleteContract(@RequestHeader("Authorization") String authorization,
                                       @PathVariable("id") Long id) {
        return contractService.deleteContract(authorization, id);
    }

    // 批量删除合同
    @DeleteMapping("/batch")
    @Operation(summary = "批量删除合同")
    public Result<String> batchDeleteContracts(@RequestHeader("Authorization") String authorization,
                                               @RequestParam List<Long> ids) {
        return contractService.batchDeleteContracts(authorization, ids);
    }

    // 获取合同统计数据
    @GetMapping("/stats")
    @Operation(summary = "获取合同统计数据")
    public Result<ContractStatsVO> getContractStats(@RequestHeader("Authorization") String authorization) {
        return contractService.getContractStats(authorization);
    }

    // 获取合同预览信息
    @GetMapping("/preview/{contractId}")
    @Operation(summary = "获取合同预览信息")
    public Result<ContractPreviewVO> getContractPreview(@RequestHeader("Authorization") String authorization,
                                                        @PathVariable("contractId") Long contractId) {
        return contractService.getContractPreview(authorization, contractId);
    }

    // 获取合同文件（用于预览）
    @GetMapping("/file/{contractId}")
    @Operation(summary = "获取合同文件")
    public ResponseEntity<Resource> getContractFile(@RequestHeader("Authorization") String authorization,
                                                    @PathVariable("contractId") Long contractId,
                                                    HttpServletRequest request) {
        return contractService.getContractFile(authorization, contractId, request);
    }

    // 下载合同文件
    @GetMapping("/download/{contractId}")
    @Operation(summary = "下载合同文件")
    public ResponseEntity<Resource> downloadContractFile(@RequestHeader("Authorization") String authorization,
                                                         @PathVariable("contractId") Long contractId,
                                                         HttpServletRequest request) {
        return contractService.downloadContractFile(authorization, contractId, request);
    }

}
