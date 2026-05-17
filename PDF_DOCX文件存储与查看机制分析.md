# 合同审查系统中PDF和DOCX文件的存储与查看机制分析

## 一、概述

本项目是一个智能合同审查系统，支持上传PDF和DOCX格式的合同文件，并提供合同内容查看、审查等功能。本文档详细分析系统中PDF和DOCX类型文件的存储方式和内容查看机制。

---

## 二、文件上传与存储机制

### 2.1 支持的文件类型

系统目前仅支持以下两种文件格式：
- **PDF** (`.pdf`)
- **DOCX** (`.docx`)

代码验证位置：[ContractServiceImpl.java](file:///e:/Professional/合同审查agent/ContractReview/src/main/java/com/example/contractreview/service/serviceImpl/ContractServiceImpl.java#L213-L215)

```java
private boolean isSupportedFileType(String extension) {
    return "pdf".equals(extension) || "docx".equals(extension);
}
```

### 2.2 文件存储流程

#### 1. 上传接口
- **接口地址**: `POST /contract/upload`
- **控制器**: [ContractController.java](file:///e:/Professional/合同审查agent/ContractReview/src/main/java/com/example/contractreview/controller/ContractController.java#L25-L30)

#### 2. 存储过程

文件上传后的处理流程如下：

```
用户上传文件 → 文件类型校验 → 生成存储路径 → 保存到本地磁盘 → 写入数据库
```

详细实现见：[ContractServiceImpl.java](file:///e:/Professional/合同审查agent/ContractReview/src/main/java/com/example/contractreview/service/serviceImpl/ContractServiceImpl.java#L43-L107)

**关键步骤说明**:

| 步骤 | 说明 | 代码位置 |
|------|------|----------|
| 获取上传路径 | 根据用户ID生成独立的上传目录 | `systemConfigService.getUploadPath(userId)` |
| 生成文件名 | 使用UUID生成唯一文件名，保留原扩展名 | `generateFileName(fileExtension)` |
| 保存文件 | 将文件保存到本地磁盘 | `file.transferTo(destFile)` |
| 记录元数据 | 将文件信息写入contract表 | `contractMapper.insert(contract)` |

#### 3. 数据库表结构

合同文件元数据存储在 `contract` 表中：

```sql
CREATE TABLE contract (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '合同ID',
    contract_no VARCHAR(50) COMMENT '合同编号',
    file_name VARCHAR(255) NOT NULL COMMENT '文件名',
    file_path VARCHAR(500) NOT NULL COMMENT '文件存储路径',
    file_size BIGINT NOT NULL COMMENT '文件大小(字节)',
    file_type VARCHAR(20) NOT NULL COMMENT '文件类型: pdf/docx',
    content LONGTEXT COMMENT '合同文本内容',
    user_id BIGINT NOT NULL COMMENT '上传用户ID',
    review_status VARCHAR(20) DEFAULT 'pending' COMMENT '审查状态',
    risk_level VARCHAR(20) COMMENT '风险等级',
    review_score INT COMMENT '审查得分(0-100)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

完整表结构见：[schema.sql](file:///e:/Professional/合同审查agent/database/schema.sql#L35-L58)

**重要字段说明**:
- `file_path`: 文件在服务器本地磁盘上的绝对路径
- `content`: 合同文本内容（当前为空，需要进一步实现文本提取功能）
- `file_type`: 存储文件扩展名（pdf或docx）

---

## 三、合同内容查看机制

### 3.1 当前实现方式

目前系统采用**模拟数据**的方式在前端展示合同内容，尚未实现从PDF/DOCX文件中提取真实文本内容的功能。

#### 前端实现

合同详情页面：[Detail.vue](file:///e:/Professional/合同审查agent/frontend/src/views/contract/Detail.vue)

**内容展示逻辑**:

```vue
<div class="preview-container">
  <div v-if="!contractContent" class="preview-placeholder">
    <el-icon class="placeholder-icon"><Document /></el-icon>
    <p>合同内容加载中...</p>
  </div>
  <div v-else class="preview-content">
    <div
      v-for="(paragraph, index) in contractParagraphs"
      :key="index"
      class="preview-paragraph"
    >
      <span class="para-number">{{ index + 1 }}</span>
      <span class="para-text">{{ paragraph }}</span>
    </div>
  </div>
</div>
```

**模拟数据加载**:

```javascript
function loadContractContent() {
  // 模拟加载
  contractParagraphs.value = [
    '第一条 合同双方',
    '甲方（采购方）：某某科技有限公司',
    '乙方（供应方）：某某商贸有限公司',
    // ... 更多模拟数据
  ]
  contractContent.value = contractParagraphs.value.join('\n')
}
```

### 3.2 合同列表展示

合同列表页面显示文件基本信息，通过文件扩展名显示不同的图标：

```vue
<el-icon class="file-icon">
  <Document v-if="row.fileName?.endsWith('.pdf')" />
  <DocumentCopy v-else />
</el-icon>
```

代码位置：[List.vue](file:///e:/Professional/合同审查agent/frontend/src/views/contract/List.vue#L130-L137)

---

## 四、缺失的功能与改进建议

### 4.1 当前缺失的功能

1. **PDF文本提取**: 未实现从PDF文件中提取文本内容
2. **DOCX文本提取**: 未实现从DOCX文件中提取文本内容
3. **文件预览**: 未实现在线预览PDF/DOCX原始文件
4. **文件下载**: 未实现合同文件下载功能

### 4.2 建议的实现方案

#### 方案一：后端文本提取（推荐）

在文件上传时，使用第三方库提取文本内容并存储到数据库的 `content` 字段。

**所需依赖**:

```xml
<!-- PDF解析 -->
<dependency>
    <groupId>org.apache.pdfbox</groupId>
    <artifactId>pdfbox</artifactId>
    <version>3.0.1</version>
</dependency>

<!-- DOCX解析 -->
<dependency>
    <groupId>org.apache.poi</groupId>
    <artifactId>poi-ooxml</artifactId>
    <version>5.2.5</version>
</dependency>
```

**实现思路**:

```java
@Service
public class DocumentParserService {
    
    public String extractText(String filePath, String fileType) {
        switch (fileType.toLowerCase()) {
            case "pdf":
                return extractPdfText(filePath);
            case "docx":
                return extractDocxText(filePath);
            default:
                throw new UnsupportedOperationException("不支持的文件类型");
        }
    }
    
    private String extractPdfText(String filePath) {
        try (PDDocument document = Loader.loadPDF(new File(filePath))) {
            PDFTextStripper stripper = new PDFTextStripper();
            return stripper.getText(document);
        }
    }
    
    private String extractDocxText(String filePath) {
        try (XWPFDocument document = new XWPFDocument(new FileInputStream(filePath))) {
            XWPFWordExtractor extractor = new XWPFWordExtractor(document);
            return extractor.getText();
        }
    }
}
```

#### 方案二：前端文件预览

使用第三方库在前端直接预览PDF文件：

- **PDF预览**: 使用 `pdf.js` 或 `vue-pdf` 组件
- **DOCX预览**: 使用 `mammoth.js` 将DOCX转换为HTML预览

#### 方案三：文件下载查看

提供文件下载接口，让用户下载后在本地查看：

```java
@GetMapping("/download/{contractId}")
public ResponseEntity<Resource> downloadContract(@PathVariable Long contractId) {
    Contract contract = contractMapper.selectById(contractId);
    Path path = Paths.get(contract.getFilePath());
    Resource resource = new UrlResource(path.toUri());
    
    return ResponseEntity.ok()
        .contentType(MediaType.APPLICATION_OCTET_STREAM)
        .header(HttpHeaders.CONTENT_DISPOSITION, 
                "attachment; filename=\"" + contract.getFileName() + "\"")
        .body(resource);
}
```

---

## 五、相关代码文件清单

### 后端代码

| 文件 | 说明 |
|------|------|
| [ContractController.java](file:///e:/Professional/合同审查agent/ContractReview/src/main/java/com/example/contractreview/controller/ContractController.java) | 合同接口控制器 |
| [ContractServiceImpl.java](file:///e:/Professional/合同审查agent/ContractReview/src/main/java/com/example/contractreview/service/serviceImpl/ContractServiceImpl.java) | 合同服务实现 |
| [Contract.java](file:///e:/Professional/合同审查agent/ContractReview/src/main/java/com/example/contractreview/model/entity/Contract.java) | 合同实体类 |
| [ContractVO.java](file:///e:/Professional/合同审查agent/ContractReview/src/main/java/com/example/contractreview/model/vo/ContractVO.java) | 合同视图对象 |
| [ContractDetailVO.java](file:///e:/Professional/合同审查agent/ContractReview/src/main/java/com/example/contractreview/model/vo/ContractDetailVO.java) | 合同详情VO |
| [ContractMapper.java](file:///e:/Professional/合同审查agent/ContractReview/src/main/java/com/example/contractreview/mapper/ContractMapper.java) | 合同数据访问层 |

### 前端代码

| 文件 | 说明 |
|------|------|
| [Detail.vue](file:///e:/Professional/合同审查agent/frontend/src/views/contract/Detail.vue) | 合同详情页面 |
| [List.vue](file:///e:/Professional/合同审查agent/frontend/src/views/contract/List.vue) | 合同列表页面 |
| [Upload.vue](file:///e:/Professional/合同审查agent/frontend/src/views/contract/Upload.vue) | 合同上传页面 |

### 数据库

| 文件 | 说明 |
|------|------|
| [schema.sql](file:///e:/Professional/合同审查agent/database/schema.sql) | 数据库表结构 |

---

## 六、总结

当前项目中PDF和DOCX文件的存储与查看机制总结如下：

1. **存储方面**: 文件以原始格式存储在服务器本地磁盘，元数据（文件名、路径、大小、类型）存储在MySQL数据库中

2. **查看方面**: 目前使用前端模拟数据展示，尚未实现真实的文件内容提取和查看功能

3. **待完善**: 需要实现PDF/DOCX文本提取功能，或集成文件预览组件，才能真正实现合同内容的查看

4. **数据库设计**: 已预留 `content` 字段用于存储提取的文本内容，为后续功能扩展提供了基础
