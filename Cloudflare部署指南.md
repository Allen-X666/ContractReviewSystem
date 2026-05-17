# Cloudflare 部署前后端分离项目指南

## 项目概述

本项目是一个智能合同审查AI系统，采用前后端分离架构：

### 技术栈
- **前端**: Vue 3 + Vite + Element Plus
- **Python后端**: FastAPI + DashScope（阿里云百炼）
- **Java后端**: Spring Boot（可选）
- **数据库**: MySQL
- **缓存**: Redis
- **AI模型**: DashScope API、HuggingFace

### 项目结构
```
合同审查agent/
├── frontend/                 # Vue 3 前端
│   ├── src/                 # 源码
│   ├── dist/                # 构建输出
│   └── vite.config.js       # Vite配置
├── 合同审查/                # Python FastAPI后端
│   ├── app/
│   ├── requirements.txt     # Python依赖
│   └── .env                # 环境变量
├── ContractReview/          # Java Spring Boot后端
├── data/                   # 数据文件
└── docs/                   # 文档
```

## 部署架构选择

### 方案一：全栈Cloudflare部署（推荐）
1. **前端** → Cloudflare Pages
2. **Python API** → Cloudflare Workers（Python运行时）
3. **Java API** → 保留在云服务器或使用其他托管
4. **数据库** → PlanetScale或Supabase
5. **缓存** → Cloudflare KV

### 方案二：混合部署
1. **前端** → Cloudflare Pages
2. **后端API** → VPS/云服务器 + Cloudflare Tunnel
3. **数据库** → 云数据库服务

### 方案三：传统部署 + Cloudflare CDN
1. **前端** → Cloudflare Pages或R2存储
2. **后端** → 云服务器
3. **CDN/代理** → Cloudflare

**推荐使用方案一**，充分利用Cloudflare生态，降低成本并提高性能。

---

## 准备工作

### 1. Cloudflare账户
- 注册 [Cloudflare账户](https://dash.cloudflare.com/sign-up)
- 验证邮箱并完成初始设置

### 2. 域名准备
- 拥有一个域名（可在Cloudflare购买或转移现有域名）
- 将域名DNS服务器指向Cloudflare

### 3. 代码仓库
- 将项目推送到GitHub、GitLab或Bitbucket
- 确保仓库包含完整项目结构

### 4. 环境变量整理
整理项目所需的环境变量：

#### 前端环境变量（`.env.production`）
```bash
VITE_API_BASE_URL=https://api.yourdomain.com
VITE_APP_TITLE=智能合同审查助手
VITE_UPLOAD_MAX_SIZE=52428800
VITE_APP_VERSION=1.0.0
```

#### Python后端环境变量
```bash
# DashScope配置
DASHSCOPE_API_KEY=your-dashscope-api-key

# 数据库配置
DATABASE_URL=mysql://user:password@host:port/database

# Redis配置
REDIS_URL=redis://:password@host:port/db

# 安全配置
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

## 前端部署到Cloudflare Pages

### 步骤1：配置构建设置

1. 进入Cloudflare Dashboard → Pages → 创建项目
2. 连接Git仓库
3. 配置构建设置：
   - **构建命令**: `npm run build`
   - **构建输出目录**: `dist`
   - **根目录**: `frontend/`
   - **Node版本**: `18` 或更高

### 步骤2：环境变量配置
在Pages设置中添加环境变量：
```
VITE_API_BASE_URL = https://api.yourdomain.com
VITE_APP_TITLE = 智能合同审查助手
VITE_UPLOAD_MAX_SIZE = 52428800
VITE_APP_VERSION = 1.0.0
```

### 步骤3：自定义域名
1. 进入Pages项目的自定义域名设置
2. 添加域名：`yourdomain.com` 和 `www.yourdomain.com`
3. Cloudflare会自动配置SSL证书

### 步骤4：部署触发
- **自动部署**: 推送到主分支时自动构建
- **预览部署**: 每个Pull Request生成预览环境
- **手动部署**: 可通过Dashboard手动触发

---

## Python后端部署到Cloudflare Workers

### 步骤1：准备Worker配置

创建 `worker-config.json`：
```json
{
  "name": "contract-review-api",
  "compatibility_date": "2024-01-01",
  "compatibility_flags": ["nodejs_compat"],
  "main": "src/index.py",
  "build": {
    "command": "pip install -r requirements.txt -t ./python",
    "cwd": "合同审查"
  }
}
```

### 步骤2：创建Worker入口文件

创建 `src/index.py`：
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import os

# 适配Cloudflare Workers环境
try:
    from mangum import Mangum
    from pyodide import to_js
except ImportError:
    pass

app = FastAPI(title="Contract Review API")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 导入现有路由
try:
    from app.main import app as original_app
    app.include_router(original_app.router)
except ImportError as e:
    @app.get("/")
    async def root():
        return {"message": "API is running", "error": str(e)}

# Cloudflare Workers适配器
async def fetch(request):
    """处理Workers请求"""
    from starlette.requests import Request
    from starlette.responses import JSONResponse
    
    # 将Workers请求转换为FastAPI请求
    body = await request.text()
    headers = dict(request.headers)
    method = request.method
    url = str(request.url)
    
    # 创建Starlette请求对象
    scope = {
        "type": "http",
        "method": method,
        "path": url.path,
        "query_string": url.query.encode(),
        "headers": [(k.encode(), v.encode()) for k, v in headers.items()],
        "body": body.encode() if body else b"",
    }
    
    request_obj = Request(scope)
    response = await app(request_obj)
    
    # 返回Workers响应
    return Response(
        await response.body(),
        status=response.status_code,
        headers=dict(response.headers)
    )
```

### 步骤3：配置Wrangler

创建 `wrangler.toml`：
```toml
name = "contract-review-api"
compatibility_date = "2024-01-01"
compatibility_flags = ["nodejs_compat"]

[vars]
DASHSCOPE_API_KEY = "{{DASHSCOPE_API_KEY}}"
DATABASE_URL = "{{DATABASE_URL}}"

[[kv_namespaces]]
binding = "KV_CACHE"
id = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### 步骤4：部署Worker

```bash
# 安装Wrangler CLI
npm install -g wrangler

# 登录Cloudflare
wrangler login

# 部署Worker
wrangler deploy
```

### 步骤5：配置自定义域
```bash
# 为Worker添加自定义域
wrangler routes create api.yourdomain.com/* --service contract-review-api
```

---

## 数据库和缓存部署

### 选项1：使用PlanetScale（MySQL兼容）
1. 注册 [PlanetScale账户](https://planetscale.com)
2. 创建数据库
3. 获取连接字符串
4. 在Worker环境变量中配置

### 选项2：使用Supabase（PostgreSQL）
1. 注册 [Supabase账户](https://supabase.com)
2. 创建项目
3. 获取连接信息
4. 修改Python代码适配PostgreSQL

### 选项3：使用Cloudflare D1（SQLite）
适合小型应用，需修改数据层代码。

### Redis缓存
使用Cloudflare KV作为缓存层：

```python
# 在Worker中使用KV
import os

class KVCache:
    def __init__(self, binding_name="KV_CACHE"):
        self.kv = binding_name
    
    async def get(self, key):
        return await self.kv.get(key)
    
    async def set(self, key, value, ttl=3600):
        await self.kv.put(key, value, expirationTtl=ttl)
```

---

## Java后端处理方案

由于Java应用不适合直接部署到Cloudflare Workers，建议：

### 方案A：保留在云服务器
- 部署到VPS（如DigitalOcean、Linode）
- 使用Cloudflare Tunnel暴露服务
- 配置负载均衡

### 方案B：容器化部署
1. 创建Docker镜像
2. 部署到：
   - Google Cloud Run
   - AWS Fargate
   - Azure Container Instances
3. 通过Cloudflare Tunnel连接

### 方案C：重构为Python
考虑将Java功能逐步迁移到Python后端，实现统一技术栈。

---

## 域名和SSL配置

### 1. DNS配置
在Cloudflare DNS设置中添加记录：
```
类型    名称                内容                   代理状态
A       @                  服务器IP               代理
A       api                服务器IP或Worker      代理
CNAME   www                yourdomain.com        代理
```

### 2. SSL配置
- **灵活SSL**（推荐）：Cloudflare提供免费SSL证书
- **完全SSL**：上传自定义证书
- **SSL/TLS模式**：设置为"完全（严格）"

### 3. 页面规则配置
创建页面规则优化性能：
1. 缓存静态资源：`yourdomain.com/assets/*`
2. 禁用API缓存：`api.yourdomain.com/*`
3. 启用Brotli压缩

---

## 环境变量管理

### Cloudflare Workers环境变量
```bash
# 通过Wrangler设置
wrangler secret put DASHSCOPE_API_KEY
wrangler secret put DATABASE_URL
wrangler secret put REDIS_URL
```

### 本地开发环境
创建 `.dev.vars` 文件：
```bash
DASHSCOPE_API_KEY=local-test-key
DATABASE_URL=mysql://root:password@localhost:3306/contract_review
REDIS_URL=redis://localhost:6379/0
```

### 多环境配置
| 环境       | 域名                    | 用途         |
|------------|-------------------------|--------------|
| 生产环境   | yourdomain.com          | 正式用户使用 |
| 预发布环境 | staging.yourdomain.com  | 测试验证     |
| 开发环境   | dev.yourdomain.com      | 开发调试     |

---

## 持续集成/部署（CI/CD）

### GitHub Actions配置
创建 `.github/workflows/deploy.yml`：

```yaml
name: Deploy to Cloudflare

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          
      - name: Install dependencies
        run: npm ci
        working-directory: frontend
        
      - name: Build
        run: npm run build
        working-directory: frontend
        env:
          VITE_API_BASE_URL: ${{ secrets.VITE_API_BASE_URL }}
          
      - name: Deploy to Cloudflare Pages
        uses: cloudflare/pages-action@v1
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          projectName: contract-review-frontend
          directory: frontend/dist
          gitHubToken: ${{ secrets.GITHUB_TOKEN }}

  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install Wrangler
        run: npm install -g wrangler
        
      - name: Deploy to Cloudflare Workers
        run: wrangler deploy
        working-directory: 合同审查
        env:
          CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          CLOUDFLARE_ACCOUNT_ID: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
```

### 密钥管理
在GitHub仓库设置中添加Secrets：
- `CLOUDFLARE_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`
- `DASHSCOPE_API_KEY`
- `DATABASE_URL`

---

## 性能优化

### 1. 前端优化
- **图片优化**: 使用Cloudflare Images或WebP格式
- **代码分割**: Vite自动代码分割
- **预加载**: 关键资源预加载

### 2. API优化
- **缓存策略**: 使用Cloudflare CDN缓存静态API响应
- **压缩**: 启用Brotli压缩
- **连接复用**: HTTP/2和HTTP/3支持

### 3. 数据库优化
- **连接池**: 合理配置数据库连接池
- **查询优化**: 添加必要索引
- **读写分离**: 考虑主从复制

### 4. 监控和日志
- **Cloudflare Analytics**: 监控流量和性能
- **Workers日志**: 使用`wrangler tail`查看实时日志
- **错误追踪**: 集成Sentry或LogRocket

---

## 安全配置

### 1. 访问控制
- **API密钥**: 使用环境变量管理敏感信息
- **CORS配置**: 严格限制允许的源
- **速率限制**: 配置Cloudflare Rate Limiting

### 2. 数据安全
- **SSL/TLS**: 强制HTTPS连接
- **数据加密**: 敏感数据加密存储
- **SQL注入防护**: 使用参数化查询

### 3. 网络安全
- **防火墙规则**: 配置Cloudflare WAF
- **DDoS防护**: 启用Cloudflare DDoS防护
- **Bot管理**: 使用Bot Fight Mode

---

## 故障排除

### 常见问题

#### 1. CORS错误
**症状**: 前端无法访问API
**解决**: 检查后端CORS配置，确保包含前端域名

#### 2. 数据库连接失败
**症状**: Worker无法连接数据库
**解决**: 
- 检查数据库连接字符串
- 确保数据库允许Cloudflare IP访问
- 使用连接池避免连接数超限

#### 3. 环境变量未加载
**症状**: 应用无法读取环境变量
**解决**: 
- 检查变量名是否正确
- 确认在正确的作用域设置变量
- 重启Worker使变量生效

#### 4. 静态资源404
**症状**: 图片、CSS、JS文件加载失败
**解决**: 
- 检查构建输出目录
- 确认文件路径正确
- 检查Pages构建配置

### 调试工具
```bash
# 查看Worker日志
wrangler tail

# 本地测试Worker
wrangler dev

# 检查部署状态
wrangler deployments list

# 测试API端点
curl https://api.yourdomain.com/health
```

---

## 成本估算

### Cloudflare免费套餐
- **Pages**: 无限请求，500次构建/月
- **Workers**: 100,000次请求/天
- **KV**: 1GB存储，100,000次读取/天
- **DNS**: 无限域名
- **SSL**: 免费证书

### 可能产生的费用
1. **数据库**: PlanetScale免费套餐（10GB存储）
2. **域名**: 域名注册费（约$10-15/年）
3. **额外流量**: 超过免费额度后的费用

### 优化成本建议
- 使用缓存减少数据库查询
- 压缩静态资源减少带宽
- 合理设置Worker超时时间
- 监控使用量设置告警

---

## 后续优化建议

### 1. 性能监控
- 集成Google Analytics或Plausible
- 使用Cloudflare Web Analytics
- 设置性能预算监控

### 2. 渐进式Web应用（PWA）
- 添加manifest.json
- 实现Service Worker
- 支持离线功能

### 3. 国际化
- 添加多语言支持
- 配置区域化域名
- 内容本地化

### 4. 自动化测试
- 单元测试和集成测试
- 端到端测试
- 性能回归测试

---

## 总结

通过Cloudflare部署前后端分离项目具有以下优势：

### 优势
1. **成本效益**: 免费套餐覆盖大部分需求
2. **性能优异**: 全球边缘网络加速
3. **安全可靠**: 内置DDoS防护和WAF
4. **易于管理**: 统一的管理界面
5. **扩展灵活**: 按需扩展，无需维护服务器

### 注意事项
1. **冷启动时间**: Workers可能有冷启动延迟
2. **运行时长限制**: Workers最多运行30秒
3. **数据库兼容性**: 需要适配无服务器数据库
4. **文件系统限制**: Workers无传统文件系统

### 开始部署
1. 从Cloudflare Pages部署前端开始
2. 逐步迁移API到Workers
3. 迁移数据库到云服务
4. 配置域名和SSL
5. 设置监控和告警

按照本指南步骤操作，您可以在几天内完成整个项目的Cloudflare部署。如有问题，请参考Cloudflare官方文档或社区论坛。

---

*最后更新: 2025年1月*
*文档版本: 1.0*
*适用项目: 智能合同审查AI系统*