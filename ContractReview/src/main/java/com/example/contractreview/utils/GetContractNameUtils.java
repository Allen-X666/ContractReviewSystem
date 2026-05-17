package com.example.contractreview.utils;

import com.example.contractreview.mapper.ReviewMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
@Slf4j
public class GetContractNameUtils {

    private final ReviewMapper reviewMapper;

    /**
     * 获取合同名称（去除扩展名）
     */
    public String getContractName(Integer reviewId) {
        String contractName = reviewMapper.getContractTitle(reviewId);
        if (contractName == null || contractName.isEmpty()) {
            contractName = "合同文件_" + reviewId;
        } else if (contractName.lastIndexOf(".") > 0) {
            contractName = contractName.substring(0, contractName.lastIndexOf("."));
        }
        log.info("合同名称：{}", contractName);
        return contractName;
    }
}
