# Contract Review AI Assistant (智能合同审查助手)

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Spring Boot](https://img.shields.io/badge/Spring%20Boot-4.0.5-brightgreen)
![FastAPI](https://img.shields.io/badge/FastAPI-0.135.3-009688)
![Vue.js](https://img.shields.io/badge/Vue.js-3.4.0-4FC08D)
![MySQL](https://img.shields.io/badge/MySQL-8.0-blue)
![Redis](https://img.shields.io/badge/Redis-7.0-red)

[中文版本](README.md) | [Architecture](ARCHITECTURE.md)

## 📋 Project Overview

The Contract Review AI Assistant is an enterprise legal compliance solution powered by artificial intelligence. It automatically reviews contract documents, identifies risk clauses, missing clauses, and violation clauses, associates relevant laws and regulations, and generates professional review reports. This significantly reduces legal workload and improves enterprise contract compliance.

### ✨ Core Features

- **Intelligent Contract Review**: Automatically parses PDF/DOCX contract documents and identifies risk clauses
- **Legal Knowledge Base**: RAG-enhanced retrieval, associating relevant laws, regulations, and judicial interpretations
- **Real-time Progress Updates**: SSE technology for real-time review progress tracking
- **Multi-format Reports**: Automatic generation of Word/PDF format review reports
- **AI Chat Assistant**: Integrated AI chatbot for legal-related queries
- **User Management**: Complete RBAC permission control system
- **Notification System**: Email and system notification mechanisms

### 🎯 Use Cases

- Enterprise legal department contract review
- Law firm contract analysis
- Financial institution compliance checks
- E-commerce platform merchant contract auditing

## 📸 Screenshots

<table>
  <tr>
    <td align="center"><b>Contract Management</b></td>
    <td align="center"><b>Review History</b></td>
  </tr>
  <tr>
    <td><img src="front/1.png" alt="Contract Management" width="100%"/></td>
    <td><img src="front/2.png" alt="Review History" width="100%"/></td>
  </tr>
  <tr>
    <td align="center" colspan="2"><b>System Settings</b></td>
  </tr>
  <tr>
    <td colspan="2" align="center"><img src="front/3.png" alt="System Settings" width="50%"/></td>
  </tr>
</table>

## 🏗️ System Architecture

### Three-tier Architecture Design

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Layer (Vue.js)                  │
│                    http://localhost:3000                    │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│               SpringBoot Gateway Layer (Java)               │
│                    http://localhost:8080                    │
│         Unified Authentication, Authorization, API Routing  │
└──────────────────────────────┬──────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────┐
│               FastAPI AI Service Layer (Python)             │
│                    http://localhost:8001                    │
│          Contract Parsing, Risk Analysis, AI Inference      │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology Stack | Description |
|-----------|------------------|-------------|
| **Frontend** | Vue 3 + Element Plus + Vite + Pinia | Modern SPA with responsive design |
| **API Gateway** | Spring Boot 4.0.5 + MyBatis + MySQL + Redis | Business logic processing, data persistence |
| **AI Service** | FastAPI + LangChain + DashScope + RAG | AI model inference, vector retrieval |
| **Database** | MySQL 8.0 + Redis 7.0 | Relational data + cache/session management |
| **File Storage** | Local Storage / Alibaba Cloud OSS | Contract document storage |
| **Vector Database** | Chroma / FAISS | Legal knowledge base vector retrieval |

## 🚀 Quick Start

### Prerequisites

- **JDK**: 25+
- **Python**: 3.9+
- **Node.js**: 18+
- **MySQL**: 8.0+
- **Redis**: 7.0+

### 1. Clone the Repository

```bash
git clone <repository-url>
cd contract-review-agent
```

### 2. Database Initialization

```bash
# Create MySQL database
mysql -u root -p -e "CREATE DATABASE contract_review CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Execute initialization script (if available)
mysql -u root -p contract_review < docs/database/init.sql
```

### 3. Start Backend Service (SpringBoot)

```bash
cd ContractReview

# Configure database
# Modify database connection in src/main/resources/application.yml

# Start service
mvn spring-boot:run
# Or
mvn clean package -DskipTests
java -jar target/ContractReview-0.0.1-SNAPSHOT.jar
```

Access the service at: http://localhost:8080/api

### 4. Start AI Service (FastAPI)

```bash
cd 合同审查

# Create virtual environment (recommended)
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env file to set API keys, etc.

# Start service
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

Access the service at: http://localhost:8001/docs

### 5. Start Frontend

```bash
cd frontend

# Install dependencies
npm install

# Configure API address
# Modify VITE_API_BASE_URL in .env file

# Start development server
npm run dev
```

### 6. Access the Application

- **Frontend Interface**: http://localhost:3000
- **SpringBoot API**: http://localhost:8080/api
- **FastAPI API**: http://localhost:8001/api/v1
- **API Documentation**: http://localhost:8080/swagger-ui.html

## 📁 Project Structure

```
contract-review-agent/
├── frontend/                    # Vue 3 Frontend Project
│   ├── src/
│   │   ├── api/               # API interfaces
│   │   ├── assets/            # Static assets
│   │   ├── components/        # Components
│   │   ├── router/            # Routing configuration
│   │   ├── store/             # Pinia state management
│   │   └── views/             # Page views
│   ├── package.json
│   └── vite.config.js
│
├── ContractReview/             # SpringBoot Backend Project
│   ├── src/main/java/com/example/contractreview/
│   │   ├── config/           # Configuration classes
│   │   ├── controller/       # Controllers
│   │   ├── service/          # Business services
│   │   ├── mapper/           # Data access
│   │   ├── entity/           # Entity classes
│   │   └── utils/            # Utility classes
│   ├── src/main/resources/
│   │   ├── application.yml   # Main configuration file
│   │   └── mapper/           # MyBatis XML
│   └── pom.xml
│
├── 合同审查/                   # Python AI Service
│   ├── app/
│   │   ├── api/              # API routes
│   │   ├── core/             # Core configuration
│   │   ├── models/           # Data models
│   │   ├── services/         # Business logic
│   │   └── utils/            # Utility functions
│   ├── requirements.txt
│   └── main.py
│
├── docs/                      # Project documentation
│   ├── API文档.md
│   ├── 部署指南.md
│   └── 架构设计.md
│
└── README.md                  # This document
```

## 🔧 Configuration

### SpringBoot Configuration (`application.yml`)

```yaml
server:
  port: 8080
  servlet:
    context-path: /api

spring:
  datasource:
    url: jdbc:mysql://localhost:3306/contract_review?useUnicode=true&characterEncoding=utf8&serverTimezone=Asia/Shanghai
    username: root
    password: your_password
    driver-class-name: com.mysql.cj.jdbc.Driver
  
  redis:
    host: localhost
    port: 6379
    database: 0
    password: 
    timeout: 6000ms

# FastAPI service configuration
fastapi:
  base-url: http://localhost:8001
  api-prefix: /api/v1
  timeout: 30000
  connect-timeout: 5000

# File upload configuration
upload:
  max-file-size: 50MB
  allowed-types: pdf,docx,doc
  storage-path: ./uploads
```

### FastAPI Configuration (`.env`)

```env
# Application configuration
APP_NAME=Contract Review AI Service
APP_VERSION=1.0.0
APP_DEBUG=false

# Server configuration
HOST=0.0.0.0
PORT=8001

# API configuration
API_PREFIX=/api/v1

# Security configuration
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS configuration
BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]

# Model configuration
DASHSCOPE_API_KEY=your_dashscope_api_key
LLM_MODEL_DEFAULT=qwen3.6-flash
LLM_MODEL_REVIEW=qwen3.6-flash
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
EMBEDDING_TYPE=huggingface

# Database configuration
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=contract_review

# Redis configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# Vector database configuration
VECTOR_STORE_PATH=./vector_store
CHROMA_PERSIST_DIRECTORY=./chroma_db

# File storage configuration
UPLOAD_DIR=./uploads
MAX_FILE_SIZE=52428800
```

### Frontend Configuration (`.env`)

```env
# Development environment
VITE_API_BASE_URL=http://localhost:8080/api
VITE_AI_API_URL=http://localhost:8001/api/v1

# Production environment (modify when deploying)
# VITE_API_BASE_URL=https://your-domain.com/api
# VITE_AI_API_URL=https://your-domain.com/ai/api/v1
```

## 📊 Database Design

### Core Table Structure

| Table Name | Description |
|------------|-------------|
| `sys_user` | User information |
| `contract` | Contract information |
| `review_task` | Review task records |
| `risk_item` | Risk items identified |
| `report` | Report information |
| `law_regulation` | Laws and regulations |
| `law_article` | Legal articles/statutes |
| `contract_template` | Contract templates |
| `sys_operation_log` | Operation logs |
| `chatbot_conversation` | Chat conversation records |
| `notification` | Notification messages |

Detailed database design in [后端开发文档.md](后端开发文档.md)

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd contract-review-agent

# Create environment configuration file
cp .env.example .env
# Edit .env file to configure database password and API keys

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Docker Compose Configuration

```yaml
version: '3.8'

services:
  mysql:
    image: mysql:8.0
    container_name: contract-mysql
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD:-root123}
      MYSQL_DATABASE: contract_review
      TZ: Asia/Shanghai
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./docs/database/init.sql:/docker-entrypoint-initdb.d/init.sql
    command: --default-authentication-plugin=mysql_native_password
    networks:
      - contract-network

  redis:
    image: redis:7.0-alpine
    container_name: contract-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    networks:
      - contract-network

  springboot:
    build: 
      context: ./ContractReview
      dockerfile: Dockerfile
    container_name: contract-java
    ports:
      - "8080:8080"
    environment:
      SPRING_PROFILES_ACTIVE: prod
      SPRING_DATASOURCE_URL: jdbc:mysql://mysql:3306/contract_review?useUnicode=true&characterEncoding=utf8
      SPRING_DATASOURCE_USERNAME: root
      SPRING_DATASOURCE_PASSWORD: ${MYSQL_ROOT_PASSWORD:-root123}
      SPRING_REDIS_HOST: redis
      SPRING_REDIS_PORT: 6379
      FASTAPI_BASE_URL: http://fastapi:8001
    depends_on:
      - mysql
      - redis
    networks:
      - contract-network

  fastapi:
    build: 
      context: ./合同审查
      dockerfile: Dockerfile
    container_name: contract-python
    ports:
      - "8001:8001"
    environment:
      MYSQL_HOST: mysql
      MYSQL_PORT: 3306
      MYSQL_USER: root
      MYSQL_PASSWORD: ${MYSQL_ROOT_PASSWORD:-root123}
      MYSQL_DB: contract_review
      REDIS_HOST: redis
      REDIS_PORT: 6379
      DASHSCOPE_API_KEY: ${DASHSCOPE_API_KEY}
    volumes:
      - ./uploads:/app/uploads
      - ./vector_store:/app/vector_store
    depends_on:
      - mysql
      - redis
    networks:
      - contract-network

  nginx:
    image: nginx:alpine
    container_name: contract-nginx
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./frontend/dist:/usr/share/nginx/html
    depends_on:
      - springboot
      - fastapi
    networks:
      - contract-network

volumes:
  mysql_data:
  redis_data:

networks:
  contract-network:
    driver: bridge
```

## ☁️ Production Deployment

### Recommended Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         User Access                         │
└──────────────────────────────┬──────────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │    CDN / Load Balancer    │
                    │   (Cloudflare/Nginx)     │
                    └──────────┬──────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
┌───────▼──────┐    ┌──────────▼──────────┐   ┌──────▼─────┐
│   Frontend   │    │    SpringBoot       │   │  FastAPI   │
│   (CDN)      │    │    (Java Backend)   │   │  (AI Service)  │
└──────────────┘    └──────────┬──────────┘   └──────┬─────┘
                               │                      │
                    ┌──────────▼──────────┐   ┌──────▼─────┐
                    │      MySQL          │   │   Redis    │
                    │    (Master-Slave)   │   │  (Cluster) │
                    └─────────────────────┘   └────────────┘
```

### Deployment Checklist

- [ ] Change default passwords and keys in all configuration files
- [ ] Configure SSL/TLS certificates
- [ ] Set up firewall rules, only open necessary ports
- [ ] Configure log collection and monitoring alerts
- [ ] Set up regular database backups
- [ ] Configure persistent file storage
- [ ] Enable Redis persistence
- [ ] Configure API rate limiting and anti-spam

Detailed deployment guide in [Cloudflare部署指南.md](Cloudflare部署指南.md)

## 🛠️ Development Guide

### API Interface Specification

- **Unified Response Format**:
```json
{
  "code": 200,
  "message": "success",
  "data": {},
  "timestamp": 1672531200000
}
```

- **Error Code Specification**:
  - `200`: Success
  - `400`: Bad request parameters
  - `401`: Unauthorized
  - `403`: Insufficient permissions
  - `404`: Resource not found
  - `500`: Internal server error

### Code Standards

- **Java**: Follow Alibaba Java Coding Guidelines
- **Python**: Follow PEP 8 standards
- **Vue**: Use Composition API, ESLint validation

### Commit Convention

```
feat: New feature
fix: Bug fix
docs: Documentation updates
style: Code formatting changes
refactor: Code refactoring
test: Test cases
chore: Build process or auxiliary tool changes
perf: Performance optimization
ci: CI/CD related changes
```

## 🔌 API Documentation

### Main API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | User login |
| POST | `/api/auth/register` | User registration |
| POST | `/api/auth/logout` | User logout |
| GET | `/api/auth/captcha` | Get captcha |
| POST | `/api/contract/upload` | Contract upload |
| GET | `/api/contract/list` | Contract list |
| GET | `/api/contract/{id}` | Contract details |
| POST | `/api/contract/{id}/delete` | Delete contract |
| POST | `/api/review/start` | Start review |
| GET | `/api/review/{id}/progress` | Get review progress (SSE) |
| GET | `/api/review/{id}/result` | Get review results |
| GET | `/api/review/{id}/risks` | Get risk list |
| POST | `/api/review/{id}/cancel` | Cancel review |
| GET | `/api/knowledge/laws` | Query laws and regulations |
| GET | `/api/knowledge/laws/{id}` | Law details |
| POST | `/api/chat/send` | Send chat message |
| GET | `/api/chat/history` | Get chat history |

Detailed API documentation in [后端API开发文档.md](后端API开发文档.md)

## 🤖 AI Features

### Contract Review Process

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ Upload  │ -> │ Parse   │ -> │ Chunk   │ -> │ Retrieve│ -> │ Analyze │
│ Contract│    │ Document│    │ Process │    │ Laws    │    │ Risk    │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
                                                                │
                                                                ▼
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│ Generate│ <- │ Save    │ <- │ Associate│ <- │ Evaluate│ <- │ Output  │
│ Report  │    │ Result  │    │ Laws    │    │ Level   │    │ Risk    │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
```

1. **Document Parsing**: Extract text content from PDF/DOCX contracts
2. **Chunking**: Split contract content into appropriately sized chunks
3. **Vector Retrieval**: Retrieve relevant legal articles from knowledge base
4. **Risk Analysis**: AI model analyzes contract clause risks
5. **Report Generation**: Generate structured review report

### Supported AI Models

| Provider | Model | Description |
|----------|-------|-------------|
| **Tongyi Qianwen** | `qwen3.6-flash` | Default model, fast |
| **Tongyi Qianwen** | `qwen-max` | High capability, suitable for complex analysis |
| **Tongyi Qianwen** | `qwen-plus` | Balance performance and cost |
| **DeepSeek** | `deepseek-v3` | Deep reasoning |
| **DeepSeek** | `deepseek-r1` | Enhanced reasoning |
| **OpenAI** | `gpt-4` | International version |
| **OpenAI** | `gpt-3.5-turbo` | Cost-effective |
| **Local Model** | `Qwen/WebWorld-8B` | Private deployment |

### RAG Knowledge Base

- **Embedding Model**: `BAAI/bge-small-zh-v1.5`
- **Vector Database**: Chroma / FAISS
- **Knowledge Sources**: 
  - Chinese laws and regulations
  - Judicial interpretations
  - Contract templates
  - Enterprise internal policies

## 📈 Performance Optimization

### Caching Strategy

- **Redis Cache**: High-frequency query result caching (user sessions, dictionary data)
- **Local Cache**: Caffeine local caching (configuration information)
- **CDN Acceleration**: Static resource CDN distribution

### Database Optimization

- **Index Optimization**: Create indexes on key query fields
- **Connection Pool**: HikariCP connection pool optimization
- **Sharding**: Horizontal sharding for large data volumes (future)
- **Read-Write Separation**: Master-slave replication architecture (future)

### Asynchronous Processing

- **Review Tasks**: Asynchronous queue processing to avoid blocking
- **File Uploads**: Asynchronous chunked uploads, support large files
- **Email Sending**: Asynchronous message queue
- **Report Generation**: Background asynchronous generation

## 🔒 Security Features

### Authentication & Authorization

- **JWT Token**: Stateless authentication with token refresh support
- **RBAC Permissions**: Role-based access control (Admin, Legal, Regular User)
- **Session Management**: Redis distributed sessions, support multi-device login

### Data Security

- **Password Encryption**: BCrypt strong hashing with automatic salting
- **SQL Protection**: MyBatis parameterized queries to prevent SQL injection
- **XSS Protection**: Input/output filtering, rich text escaping
- **File Security**: Type checking, size limits, virus scanning interface

### Audit Logging

- **Operation Auditing**: Log critical operations (login, review, delete)
- **Login Auditing**: Monitor failed logins, abnormal login alerts
- **Exception Monitoring**: Global exception capture, error log recording

## 📝 Related Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Detailed system architecture |
| [后端开发文档.md](后端开发文档.md) | Backend detailed design |
| [后端API开发文档.md](后端API开发文档.md) | API interface specifications |
| [FastAPI优化建议.md](FastAPI优化建议.md) | Python service optimization |
| [项目优化建议.md](项目优化建议.md) | Overall optimization suggestions |
| [Cloudflare部署指南.md](Cloudflare部署指南.md) | Cloud deployment guide |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Pre-commit Checks

```bash
# Frontend code check
cd frontend
npm run lint
npm run build

# Java code check
cd ContractReview
mvn clean verify

# Python code check
cd 合同审查
flake8 app/
black app/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## 👥 Contact

- **Project Maintainer**: xjl
- **Issue Tracker**: [GitHub Issues](https://github.com/your-repo/issues)
- **Email**: xjl20041115@126.com

## 🙏 Acknowledgments

Thanks to the following open-source projects and technologies:

- [Spring Boot](https://spring.io/projects/spring-boot)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Vue.js](https://vuejs.org/)
- [LangChain](https://www.langchain.com/)
- [Tongyi Qianwen](https://tongyi.aliyun.com/)
- [Element Plus](https://element-plus.org/)

---

**Contract Review AI Assistant** - Making contract review smarter and more efficient!
