# 智能合同审查系统 - 后端API开发文档

## 一、接口规范

### 1.1 基础信息
- **基础URL**: `http://localhost:8080/api`
- **请求格式**: JSON
- **响应格式**: JSON
- **字符编码**: UTF-8
- **认证方式**: Bearer Token (JWT)

### 1.2 响应格式
```json
{
  "code": 200,
  "message": "success",
  "data": {},
  "timestamp": 1704067200000
}
```

### 1.3 状态码说明
| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 401 | 未授权/Token无效 |
| 403 | 禁止访问 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

### 1.4 请求头
```
Content-Type: application/json
Authorization: Bearer {token}
```

---

## 二、认证模块 API

### 2.1 用户注册
**接口地址**: `POST /auth/register`

**请求参数**:
```json
{
  "username": "string",      // 用户名，必填，3-20字符
  "password": "string",      // 密码，必填，6-20字符
  "confirmPassword": "string", // 确认密码，必填
  "email": "string",         // 邮箱，选填
  "phone": "string",         // 手机号，选填
  "captcha": "string",       // 验证码，必填
  "registerType": "account"  // 注册类型: account/phone/email
}
```

**响应数据**:
```json
{
  "code": 200,
  "message": "注册成功",
  "data": {
    "userId": 1,
    "username": "admin",
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "expiresIn": 86400
  }
}
```

### 2.2 用户登录
**接口地址**: `POST /auth/login`

**请求参数**:
```json
{
  "username": "string",      // 用户名/手机号/邮箱
  "password": "string",      // 密码
  "loginType": "account",    // 登录类型: account/phone/email
  "code": "string"           // 验证码（手机号/邮箱登录时必填）
}
```

**响应数据**:
```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "expiresIn": 86400,
    "userInfo": {
      "id": 1,
      "username": "admin",
      "realName": "管理员",
      "email": "admin@example.com",
      "phone": "13800138000",
      "avatar": "https://...",
      "role": "admin",
      "department": "法务部"
    }
  }
}
```

### 2.3 发送验证码
**接口地址**: `POST /auth/send-code`

**请求参数**:
```json
{
  "target": "string",        // 手机号或邮箱
  "type": "string",          // 类型: login/register/reset_password
  "targetType": "phone"      // 目标类型: phone/email
}
```

**响应数据**:
```json
{
  "code": 200,
  "message": "验证码已发送",
  "data": {
    "expireSeconds": 60
  }
}
```

### 2.4 刷新Token
**接口地址**: `POST /auth/refresh`

**请求头**: `Authorization: Bearer {refreshToken}`

**响应数据**:
```json
{
  "code": 200,
  "message": "刷新成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "expiresIn": 86400
  }
}
```

### 2.5 退出登录
**接口地址**: `POST /auth/logout`

**请求头**: `Authorization: Bearer {token}`

**响应数据**:
```json
{
  "code": 200,
  "message": "退出成功",
  "data": null
}
```

### 2.6 获取当前用户信息
**接口地址**: `GET /auth/user-info`

**请求头**: `Authorization: Bearer {token}`

**响应数据**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "username": "admin",
    "realName": "管理员",
    "email": "admin@example.com",
    "phone": "13800138000",
    "avatar": "https://...",
    "role": "admin",
    "department": "法务部",
    "createdAt": "2024-01-01 00:00:00"
  }
}
```

### 2.7 修改密码
**接口地址**: `POST /auth/change-password`

**请求参数**:
```json
{
  "oldPassword": "string",   // 原密码
  "newPassword": "string",   // 新密码
  "confirmPassword": "string" // 确认新密码
}
```

**响应数据**:
```json
{
  "code": 200,
  "message": "密码修改成功",
  "data": null
}
```

---


## 三、用户设置 API

### 3.1 获取用户信息
**接口地址**: `GET /user/profile`

**响应数据**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "username": "admin",
    "realName": "管理员",
    "email": "admin@example.com",
    "phone": "13800138000",
    "avatar": "https://...",
    "department": "法务部",
    "createdAt": "2024-01-01 00:00:00"
  }
}
```

### 3.2 更新用户信息
**接口地址**: `PUT /user/profile`

**请求参数**:
```json
{
  "realName": "string",      // 真实姓名
  "email": "string",         // 邮箱
  "phone": "string",         // 手机号
  "department": "string"     // 所属部门
}
```

**响应数据**:
```json
{
  "code": 200,
  "message": "更新成功",
  "data": null
}
```

### 3.3 上传头像  
**接口地址**: `POST /user/avatar`

**Content-Type**: `multipart/form-data`

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| file | File | 是 | 头像图片 |

**响应数据**:
```json
{
  "code": 200,
  "message": "上传成功",
  "data": {
    "avatarUrl": "https://..."
  }
}
```

### 3.4 获取通知设置
**接口地址**: `GET /user/notification-settings`

**响应数据**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "reviewComplete": true,
    "riskAlert": true,
    "systemNotice": true,
    "emailNotification": false
  }
}
```

### 3.5 更新通知设置
**接口地址**: `PUT /user/notification-settings`

**请求参数**:
```json
{
  "reviewComplete": true,
  "riskAlert": true,
  "systemNotice": true,
  "emailNotification": false
}
```

**响应数据**:
```json
{
  "code": 200,
  "message": "设置已保存",
  "data": null
}
```

---

## 四、合同管理 API

### 4.1 上传合同  
**接口地址**: `POST /contract/upload`

**Content-Type**: `multipart/form-data`

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| file | File | 是 | 合同文件(PDF/DOCX) |

**响应数据**:
```json
{
  "code": 200,
  "message": "上传成功",
  "data": {
    "contractId": 1,
    "fileName": "采购合同.pdf",
    "fileSize": 1024000,
    "fileType": "pdf",
    "uploadTime": "2024-01-01 12:00:00"
  }
}
```

### 4.2 批量上传合同
**接口地址**: `POST /contract/batch-upload`

**Content-Type**: `multipart/form-data`

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| files | File[] | 是 | 合同文件数组 |

**响应数据**:
```json
{
  "code": 200,
  "message": "上传成功",
  "data": {
    "success": 2,
    "failed": 0,
    "contracts": [
      {
        "contractId": 1,
        "fileName": "合同1.pdf",
        "status": "success"
      },
      {
        "contractId": 2,
        "fileName": "合同2.docx",
        "status": "success"
      }
    ]
  }
}
```

### 4.3 获取合同列表
**接口地址**: `GET /contract/list`

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| page | int | 否 | 页码，默认1 |
| pageSize | int | 否 | 每页数量，默认10 |
| keyword | string | 否 | 搜索关键词 |
| reviewStatus | string | 否 | 审查状态筛选 |
| riskLevel | string | 否 | 风险等级筛选 |
| startDate | string | 否 | 开始日期(YYYY-MM-DD) |
| endDate | string | 否 | 结束日期(YYYY-MM-DD) |

**响应数据**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "id": 1,
        "contractNo": "HT202401010001",
        "fileName": "采购合同.pdf",
        "fileSize": 1024000,
        "fileType": "pdf",
        "reviewStatus": "completed",
        "riskLevel": "medium",
        "reviewScore": 85,
        "createdAt": "2024-01-01 12:00:00"
      }
    ],
    "total": 100,
    "page": 1,
    "pageSize": 10
  }
}
```

### 4.4 获取合同详情
**接口地址**: `GET /contract/{id}`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | long | 是 | 合同ID |

**响应数据**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "contractNo": "HT202401010001",
    "fileName": "采购合同.pdf",
    "filePath": "/uploads/2024/01/xxx.pdf",
    "fileSize": 1024000,
    "fileType": "pdf",
    "content": "合同文本内容...",
    "reviewStatus": "completed",
    "riskLevel": "medium",
    "reviewScore": 85,
    "createdAt": "2024-01-01 12:00:00",
    "updatedAt": "2024-01-01 12:30:00"
  }
}
```

### 4.5 删除合同
**接口地址**: `DELETE /contract/{id}`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | long | 是 | 合同ID |

**响应数据**:
```json
{
  "code": 200,
  "message": "删除成功",
  "data": null
}
```

### 4.6 批量删除合同
**接口地址**: `POST /contract/batch-delete`

**请求参数**:
```json
{
  "ids": [1, 2, 3]  // 合同ID数组
}
```

**响应数据**:
```json
{
  "code": 200,
  "message": "删除成功",
  "data": {
    "deleted": 3
  }
}
```

### 4.7 下载合同文件
**接口地址**: `GET /contract/{id}/download`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | long | 是 | 合同ID |

**响应**: 文件流 (Content-Type: application/octet-stream)

### 4.8 预览合同文件
**接口地址**: `GET /contract/{id}/preview`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | long | 是 | 合同ID |

**响应**: 文件流或预览URL

---

## 五、合同审查 API

### 5.1 发起审查
**接口地址**: `POST /review/start`

**请求参数**:
```json
{
  "contractId": 1,           // 合同ID，必填
  "reviewOptions": {         // 审查选项，选填
    "checkInvalidClause": true,     // 检查无效条款
    "checkMissingClause": true,     // 检查缺失条款
    "checkUnreasonableClause": true, // 检查不合理条款
    "checkLegalRisk": true          // 检查法律风险
  }
}
```

**响应数据**:
```json
{
  "code": 200,
  "message": "审查任务已创建",
  "data": {
    "reviewId": 1,
    "reviewNo": "SC202401010001",
    "contractId": 1,
    "status": "processing",
    "progress": 0,
    "createdAt": "2024-01-01 12:00:00"
  }
}
```

### 5.2 获取审查进度 (SSE)
**接口地址**: `GET /review/{reviewId}/progress`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| reviewId | long | 是 | 审查ID |

**SSE 数据流**:
```
event: message
data: {"progress": 25, "stage": "parsing", "status": "processing", "message": "正在解析文档..."}

event: message
data: {"progress": 50, "stage": "retrieving", "status": "processing", "message": "正在检索相关法条..."}

event: message
data: {"progress": 75, "stage": "analyzing", "status": "processing", "message": "AI正在分析风险..."}

event: message
data: {"progress": 100, "stage": "generating", "status": "completed", "message": "审查完成"}
```

### 5.3 获取审查结果
**接口地址**: `GET /review/{reviewId}/result`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| reviewId | long | 是 | 审查ID |

**响应数据**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "reviewId": 1,
    "reviewNo": "SC202401010001",
    "contractId": 1,
    "status": "completed",
    "overallScore": 85,
    "conclusion": "经系统审查，本合同存在若干需要关注的风险点...",
    "riskSummary": {
      "high": 1,
      "medium": 2,
      "low": 3
    },
    "completedAt": "2024-01-01 12:05:00"
  }
}
```

### 5.4 获取风险列表
**接口地址**: `GET /review/{reviewId}/risks`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| reviewId | long | 是 | 审查ID |

**查询参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| level | string | 否 | 风险等级筛选: high/medium/low |
| type | string | 否 | 风险类型筛选 |
| page | int | 否 | 页码 |
| pageSize | int | 否 | 每页数量 |

**响应数据**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "id": 1,
        "riskType": "invalid_clause",
        "riskLevel": "high",
        "clauseTitle": "违约金条款",
        "clauseContent": "违约金为合同金额的50%",
        "riskDescription": "违约金约定过高，可能被法院认定为无效条款",
        "suggestion": "建议将违约金调整为不超过合同金额的30%",
        "relatedLaws": [
          {
            "lawId": 1,
            "lawName": "《中华人民共和国民法典》",
            "articleNo": "第585条",
            "content": "约定的违约金过分高于造成的损失的，人民法院或者仲裁机构可以根据当事人的请求予以适当减少..."
          }
        ],
        "paragraphIndex": 5
      }
    ],
    "total": 6
  }
}
```

### 5.5 获取审查历史
**接口地址**: `GET /review/history`

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| page | int | 否 | 页码，默认1 |
| pageSize | int | 否 | 每页数量，默认10 |
| contractId | long | 否 | 合同ID筛选 |
| status | string | 否 | 状态筛选 |
| startDate | string | 否 | 开始日期 |
| endDate | string | 否 | 结束日期 |

**响应数据**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "reviewId": 1,
        "reviewNo": "SC202401010001",
        "contractId": 1,
        "contractName": "采购合同.pdf",
        "fileSize": 1024000,
        "status": "completed",
        "riskSummary": {
          "high": 1,
          "medium": 2,
          "low": 3
        },
        "overallScore": 85,
        "createdAt": "2024-01-01 12:00:00",
        "completedAt": "2024-01-01 12:05:00"
      }
    ],
    "total": 50,
    "stats": {
      "total": 50,
      "thisMonth": 10,
      "avgScore": 82,
      "totalIssues": 120
    }
  }
}
```

### 5.6 重新审查
**接口地址**: `POST /review/{reviewId}/re-review`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| reviewId | long | 是 | 审查ID |

**响应数据**:
```json
{
  "code": 200,
  "message": "重新审查已启动",
  "data": {
    "reviewId": 1,
    "status": "processing",
    "progress": 0
  }
}
```

### 5.7 取消审查
**接口地址**: `POST /review/{reviewId}/cancel`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| reviewId | long | 是 | 审查ID |

**响应数据**:
```json
{
  "code": 200,
  "message": "审查已取消",
  "data": null
}
```

---

## 六、报告管理 API

### 6.1 生成报告
**接口地址**: `POST /report/generate`

**请求参数**:
```json
{
  "reviewId": 1,             // 审查ID，必填
  "reportOptions": {         // 报告选项，选填
    "includeCover": true,           // 包含封面
    "includeOverview": true,        // 包含概览
    "includeRiskDetails": true,     // 包含风险详情
    "includeLawReferences": true,   // 包含法条引用
    "includeSuggestions": true      // 包含修改建议
  }
}
```

**响应数据**:
```json
{
  "code": 200,
  "message": "报告生成成功",
  "data": {
    "reportId": 1,
    "reportNo": "BG202401010001",
    "reviewId": 1,
    "reportTitle": "采购合同审查报告",
    "createdAt": "2024-01-01 12:10:00"
  }
}
```

### 6.2 获取报告详情
**接口地址**: `GET /report/{reportId}`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| reportId | long | 是 | 报告ID |

**响应数据**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "reportId": 1,
    "reportNo": "BG202401010001",
    "reviewId": 1,
    "contractId": 1,
    "contractName": "采购合同.pdf",
    "reportTitle": "采购合同审查报告",
    "overallScore": 85,
    "riskSummary": {
      "high": 1,
      "medium": 2,
      "low": 3
    },
    "conclusion": "经系统审查，本合同存在若干需要关注的风险点...",
    "risks": [...],
    "createdAt": "2024-01-01 12:10:00"
  }
}
```

### 6.3 导出 Word 报告
**接口地址**: `GET /report/{reportId}/export/word`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| reportId | long | 是 | 报告ID |

**响应**: 文件流 (Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document)

**文件名**: `审查报告_{reportNo}.docx`

### 6.4 导出 PDF 报告
**接口地址**: `GET /report/{reportId}/export/pdf`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| reportId | long | 是 | 报告ID |

**响应**: 文件流 (Content-Type: application/pdf)

**文件名**: `审查报告_{reportNo}.pdf`

### 6.5 获取报告列表
**接口地址**: `GET /report/list`

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| page | int | 否 | 页码，默认1 |
| pageSize | int | 否 | 每页数量，默认10 |
| contractId | long | 否 | 合同ID筛选 |
| startDate | string | 否 | 开始日期 |
| endDate | string | 否 | 结束日期 |

**响应数据**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "reportId": 1,
        "reportNo": "BG202401010001",
        "reviewId": 1,
        "contractId": 1,
        "contractName": "采购合同.pdf",
        "reportTitle": "采购合同审查报告",
        "downloadCount": 5,
        "createdAt": "2024-01-01 12:10:00"
      }
    ],
    "total": 30
  }
}
```

### 6.6 删除报告
**接口地址**: `POST /report/{reportId}/delete`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| reportId | long | 是 | 报告ID |

**响应数据**:
```json
{
  "code": 200,
  "message": "删除成功",
  "data": null
}
```

---

## 七、法律知识库 API

### 7.1 搜索法条
**接口地址**: `GET /knowledge/laws/search`

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| keyword | string | 是 | 搜索关键词 |
| category | string | 否 | 分类筛选 |
| page | int | 否 | 页码，默认1 |
| pageSize | int | 否 | 每页数量，默认10 |

**响应数据**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "id": 1,
        "name": "《中华人民共和国民法典》",
        "category": "contract",
        "issuer": "全国人民代表大会",
        "publishDate": "2020-05-28",
        "effectiveDate": "2021-01-01",
        "status": "effective",
        "description": "民法典是新中国第一部以法典命名的法律...",
        "articleCount": 1260,
        "isNew": true
      }
    ],
    "total": 100
  }
}
```

### 7.2 获取法条详情
**接口地址**: `GET /knowledge/laws/{lawId}`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| lawId | long | 是 | 法规ID |

**响应数据**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "lawNo": "主席令第四十五号",
    "name": "《中华人民共和国民法典》",
    "category": "contract",
    "issuer": "全国人民代表大会",
    "publishDate": "2020-05-28",
    "effectiveDate": "2021-01-01",
    "status": "effective",
    "description": "民法典是新中国第一部以法典命名的法律...",
    "articles": [
      {
        "id": 1,
        "articleNo": "第465条",
        "title": "依法成立的合同效力",
        "content": "依法成立的合同，受法律保护。依法成立的合同，仅对当事人具有法律约束力...",
        "interpretation": "本条规定了合同的法律效力..."
      }
    ]
  }
}
```

### 7.3 获取法条分类列表
**接口地址**: `GET /knowledge/laws/categories`

**响应数据**:
```json
{
  "code": 200,
  "message": "success",
  "data": [
    {
      "id": "contract",
      "name": "合同法",
      "count": 50
    },
    {
      "id": "labor",
      "name": "劳动法",
      "count": 30
    },
    {
      "id": "intellectual_property",
      "name": "知识产权",
      "count": 20
    }
  ]
}
```

### 7.4 获取模板列表
**接口地址**: `GET /knowledge/templates`

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| category | string | 否 | 分类筛选 |
| page | int | 否 | 页码，默认1 |
| pageSize | int | 否 | 每页数量，默认10 |

**响应数据**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "list": [
      {
        "id": 1,
        "name": "标准采购合同模板",
        "category": "purchase",
        "description": "适用于一般货物采购的标准合同模板",
        "fileSize": 25600,
        "downloadCount": 128,
        "updatedAt": "2024-01-01 00:00:00"
      }
    ],
    "total": 50
  }
}
```

### 7.5 上传模板
**接口地址**: `POST /knowledge/templates/upload`

**Content-Type**: `multipart/form-data`

**请求参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| file | File | 是 | 模板文件 |
| name | string | 是 | 模板名称 |
| category | string | 是 | 模板分类 |
| description | string | 否 | 模板描述 |

**响应数据**:
```json
{
  "code": 200,
  "message": "上传成功",
  "data": {
    "templateId": 1,
    "name": "标准采购合同模板",
    "category": "purchase"
  }
}
```

### 7.6 删除模板
**接口地址**: `DELETE /knowledge/templates/{templateId}`

**路径参数**:
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| templateId | long | 是 | 模板ID |

**响应数据**:
```json
{
  "code": 200,
  "message": "删除成功",
  "data": null
}
```

### 7.7 获取知识库统计
**接口地址**: `GET /knowledge/stats`

**响应数据**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "totalLaws": 100,
    "totalArticles": 5000,
    "totalTemplates": 50,
    "lastUpdate": "2024-01-01"
  }
}
```

---

## 八、仪表盘 API

### 8.1 获取仪表盘统计数据
**接口地址**: `GET /dashboard/stats`

**响应数据**:
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "totalContracts": 150,
    "completedReviews": 120,
    "pendingReviews": 10,
    "highRiskCount": 5,
    "trends": {
      "contracts": { "value": 12, "type": "up" },
      "completed": { "value": 8, "type": "up" },
      "highRisk": { "value": 5, "type": "down" }
    },
    "recentActivity": [
      {
        "type": "upload",
        "description": "上传了采购合同.pdf",
        "time": "2024-01-01 12:00:00"
      },
      {
        "type": "review_complete",
        "description": "完成了合同审查",
        "time": "2024-01-01 11:30:00"
      }
    ],
    "monthlyStats": [
      { "month": "1月", "contracts": 10, "reviews": 8 },
      { "month": "2月", "contracts": 15, "reviews": 12 }
    ]
  }
}
```

---

## 九、枚举值定义

### 9.1 审查状态 (reviewStatus)
| 值 | 说明 |
|----|------|
| pending | 待审查 |
| processing | 审查中 |
| completed | 已完成 |
| failed | 审查失败 |
| cancelled | 已取消 |

### 9.2 风险等级 (riskLevel)
| 值 | 说明 |
|----|------|
| high | 高风险 |
| medium | 中风险 |
| low | 低风险 |

### 9.3 风险类型 (riskType)
| 值 | 说明 |
|----|------|
| invalid_clause | 无效条款 |
| missing_clause | 缺失条款 |
| unreasonable_clause | 不合理条款 |
| legal_risk | 法律风险 |

### 9.4 审查阶段 (reviewStage)
| 值 | 说明 |
|----|------|
| parsing | 解析文档 |
| retrieving | 检索法条 |
| analyzing | AI分析 |
| generating | 生成报告 |

### 9.5 合同分类 (contractCategory)
| 值 | 说明 |
|----|------|
| purchase | 采购合同 |
| service | 服务协议 |
| labor | 劳动合同 |
| lease | 租赁合同 |
| confidentiality | 保密协议 |
| cooperation | 合作协议 |

### 9.6 法规分类 (lawCategory)
| 值 | 说明 |
|----|------|
| contract | 合同法 |
| labor | 劳动法 |
| intellectual_property | 知识产权 |
| company | 公司法 |
| civil | 民法 |
| criminal | 刑法 |

---

## 十、错误码定义

| 错误码 | 说明 |
|--------|------|
| 400001 | 请求参数错误 |
| 400002 | 参数校验失败 |
| 401001 | Token无效或过期 |
| 401002 | 用户名或密码错误 |
| 401003 | 账号已被禁用 |
| 403001 | 权限不足 |
| 404001 | 用户不存在 |
| 404002 | 合同不存在 |
| 404003 | 审查任务不存在 |
| 404004 | 报告不存在 |
| 409001 | 用户名已存在 |
| 409002 | 邮箱已注册 |
| 409003 | 手机号已注册 |
| 422001 | 验证码错误 |
| 422002 | 验证码已过期 |
| 500001 | 文件上传失败 |
| 500002 | 文件解析失败 |
| 500003 | AI服务调用失败 |
| 500004 | 报告生成失败 |
| 500005 | 系统内部错误 |
