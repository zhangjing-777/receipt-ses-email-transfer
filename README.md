# SES Email Transfer & OCR API

本项目用于**自动接收 AWS SES 邮件通知**，通过解析邮件内容，将附件存储到 Supabase Storage，并对附件进行 OCR，提取发票信息并存入 Supabase 表。后端基于 FastAPI，支持 Docker 一键部署。

---

## 功能简介

- **自动接收 AWS SES 邮件通知**，解析邮件内容
- **附件上传至 Supabase Storage**
- **对附件进行 OCR 识别，提取发票信息**
- **将结构化发票信息存入 Supabase 数据表**
- **详细日志记录**，支持本地和文件存储
- **健康检查接口**，便于监控

---

## 目录结构

```
.
├── app.py                  # FastAPI 主入口
├── requirements.txt        # Python 依赖
├── dockerfile              # Docker 构建文件
├── docker-compose.yml      # Docker Compose 配置
├── ses_eml_save/           # 邮件解析、上传、OCR、数据处理等核心代码
│   ├── main.py
│   ├── eml_parser.py
│   ├── insert_data.py
│   ├── ocr.py
│   ├── upload_storage.py
│   └── util.py
└── logs/                   # 日志文件目录（自动生成）
```

---

## 环境变量（.env）

请在根目录下创建 `.env` 文件，内容示例：

```env
SUPABASE_URL=你的supabase项目url
SUPABASE_SERVICE_ROLE_KEY=你的supabase服务密钥
OPENROUTER_API_KEY=你的OpenRouter大模型API Key
OPENROUTER_URL=你的OpenRouter API地址
MODEL=你的大模型名称
DEEPSEEK_URL=你的Deepseek API地址
DEEPSEEK_API_KEY=你的Deepseek API Key
AWS_REGION=你的AWS区域
AWS_ACCESS_KEY_ID=你的AWS访问ID
AWS_SECRET_ACCESS_KEY=你的AWS密钥
```

---

## 快速启动

### 1. 本地运行

```bash
pip install -r requirements.txt
uvicorn app:app --reload
```

### 2. Docker 一键部署

#### 构建镜像

```bash
docker build -t ses-email-transfer .
```

#### 启动服务

```bash
docker-compose up --build
```

#### 访问健康检查

浏览器访问 [http://localhost:8000/health](http://localhost:8000/health)

---

## 主要 API

### 1. Webhook 接口

- **POST** `/webhook/ses-email-transfer`
- 用于接收 AWS SNS/SES 通知，自动处理邮件和附件

### 2. 健康检查

- **GET** `/health`
- 返回服务状态和时间戳

---

## 日志

- 日志文件自动保存在 `logs/` 目录下，按模块和日期区分
- 同时输出到控制台和文件，便于调试和生产监控

---
