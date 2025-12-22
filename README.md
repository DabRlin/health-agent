# HealthAI - 基于 AI Agent 的个人健康风险预测与智能健康咨询系统

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/Vue-3.0+-green.svg)](https://vuejs.org/)

> 毕业设计项目 - MVP 最小可行产品

## 📖 项目简介

HealthAI 是一个智能健康管理系统，融合了机器学习模型、医疗知识库和 AI Agent 技术，为用户提供：

- 🏥 **疾病风险预测** - 基于 Framingham、FINDRISC 等医学评估模型
- 📊 **健康趋势分析** - 时序数据分析、异常检测、健康评分
- 🤖 **智能健康咨询** - 基于 Dify + LLM 的智能问诊
- 📈 **数据可视化** - ECharts 健康趋势图表

## ✨ 核心功能

### 1. 智能问诊
- 实时对话交互（支持流式输出）
- 基于 Dify 平台集成 LLM
- 问诊历史记录

### 2. 风险评估
- **心血管疾病风险** - Framingham Risk Score (2008)
- **糖尿病风险** - FINDRISC 评分系统
- **代谢综合征** - IDF/NCEP ATP III 标准
- 风险因素分析 + 个性化健康建议

### 3. 健康数据管理
- 健康指标录入（血压、血糖、心率等）
- 穿戴设备数据模拟
- 趋势图表可视化
- 异常检测和预警

### 4. 健康趋势分析
- 移动平均和线性回归预测
- Z-Score、IQR、医学阈值异常检测
- 多维度综合健康评分

## 🛠️ 技术栈

### 前端
- **框架**: Vue 3 + Vite
- **路由**: Vue Router 4
- **图表**: ECharts + vue-echarts
- **图标**: Lucide Vue Next
- **样式**: 原生 CSS (Meta 风格设计系统)

### 后端
- **框架**: Flask
- **数据库**: SQLite + SQLAlchemy ORM
- **认证**: JWT Token
- **AI 集成**: Dify API

### ML 模型
- **风险评估**: Framingham、FINDRISC、代谢综合征
- **趋势分析**: 移动平均、线性回归
- **异常检测**: Z-Score、IQR、医学阈值

## 📁 项目结构

```
MVP/
├── docs/                    # 项目文档
│   ├── readme.md           # 项目说明
│   ├── architecture.md     # 系统架构设计
│   ├── database.md         # 数据库设计
│   ├── ml-models.md        # ML 模型文档
│   ├── api.md              # API 接口文档
│   └── changelog.md        # 更新日志
├── backend/                 # 后端服务
│   ├── app.py              # Flask 应用入口
│   ├── config.py           # 配置管理
│   ├── database/           # 数据库模块
│   ├── services/           # 业务逻辑层
│   │   ├── ml_models/      # ML 模型实现
│   │   ├── auth_service.py
│   │   ├── consultation_service.py
│   │   ├── risk_service.py
│   │   └── trend_service.py
│   ├── routes/             # API 路由层
│   └── utils/              # 工具模块
├── frontend/                # 前端应用
│   ├── src/
│   │   ├── views/          # 页面视图
│   │   ├── components/     # 公共组件
│   │   ├── router/         # 路由配置
│   │   └── api/            # API 服务层
│   └── package.json
└── dify/                    # Dify 平台 (Docker)
```

## 🚀 快速开始

### 环境要求
- Node.js >= 18
- Python >= 3.9
- Docker & Docker Compose (可选，用于 Dify)

### 1. 克隆项目

```bash
git clone https://github.com/DabRlin/health-agent.git
cd health-agent
```

### 2. 后端设置

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python database/seed.py

# 配置环境变量（可选）
cp .env.example .env
# 编辑 .env 文件，配置 Dify API Key

# 启动后端服务
python app.py
```

后端服务将运行在 `http://127.0.0.1:5000`

### 3. 前端设置

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端应用将运行在 `http://localhost:5173`

### 4. Dify 平台设置（可选）

如需使用真实 LLM 进行智能问诊：

```bash
cd dify/docker

# 配置环境变量
cp .env.example .env

# 启动 Dify 服务
docker compose up -d
```

访问 `http://localhost` 配置 LLM 模型，获取 API Key 后填入后端 `.env` 文件。

## 📚 文档

详细文档请查看 `docs/` 目录：

- [系统架构设计](./docs/architecture.md)
- [数据库设计](./docs/database.md)
- [ML 模型文档](./docs/ml-models.md)
- [API 接口文档](./docs/api.md)
- [更新日志](./docs/changelog.md)

## 🎯 开发路线图

- [x] 项目架构设计
- [x] 前端 UI 框架搭建
- [x] 后端 API 开发
- [x] 数据库设计与实现
- [x] JWT 用户认证
- [x] ML 风险评估模型集成
- [x] 健康趋势分析模块
- [x] Dify AI 问诊集成
- [ ] 体检报告 OCR 分析
- [ ] 健康画像综合分析
- [ ] 移动端适配

## 📊 ML 模型说明

### 心血管风险评估 (Framingham Risk Score)
- 基于 Framingham Heart Study (2008)
- 预测 10 年心血管事件风险
- 输入：年龄、性别、胆固醇、血压、吸烟史等

### 糖尿病风险评估 (FINDRISC)
- 芬兰糖尿病风险评分系统
- 评分范围 0-26 分
- 无需实验室检查即可评估

### 代谢综合征评估
- 基于 IDF/NCEP ATP III 标准
- 亚洲人群腰围标准
- 5 项标准中满足 ≥3 项即确诊

详细说明请参考 [ml-models.md](./docs/ml-models.md)

## 🔒 免责声明

⚠️ **重要提示**：本系统仅供健康参考和学术研究，所提供的风险评估与健康建议不能替代专业医疗诊断。如有健康问题，请及时前往正规医疗机构就医。

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 👨‍💻 作者

毕业设计项目 - HealthAI

## 🙏 致谢

- [Framingham Heart Study](https://framinghamheartstudy.org/)
- [FINDRISC](https://www.diabetes.fi/english)
- [Dify](https://dify.ai/)
- [Vue.js](https://vuejs.org/)
- [Flask](https://flask.palletsprojects.com/)
