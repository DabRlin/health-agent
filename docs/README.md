# HealthAI MVP

基于 AI 的个人健康风险预测与智能健康咨询系统 - 最小可行产品

## 项目概述

HealthAI MVP 是一个健康管理系统的原型，旨在验证核心功能和用户体验。系统提供健康数据管理、智能问诊、风险评估等功能。

## 技术栈

### 前端
- **框架**: Vue 3 + Vite
- **路由**: Vue Router 4
- **图表**: ECharts + vue-echarts
- **图标**: Lucide Vue Next
- **样式**: 原生 CSS（Meta 风格设计系统）

### 后端
- **框架**: Flask
- **数据库**: SQLite + SQLAlchemy ORM
- **跨域**: 手动 CORS 处理

## 文档索引

| 文档 | 说明 |
|------|------|
| [README.md](./README.md) | 项目说明（本文档） |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | 系统架构设计 |
| [DATABASE.md](./DATABASE.md) | 数据库表结构 |
| [DATA_LAYER.md](./DATA_LAYER.md) | 数据层设计（穿戴设备数据） |
| [ML_MODELS.md](./ML_MODELS.md) | ML 模型文档（风险评估算法） |
| [API.md](./API.md) | API 接口文档 |
| [CHANGELOG.md](./CHANGELOG.md) | 更新日志 |

## 目录结构

```
MVP/
├── Docs/                    # 项目文档
│   ├── README.md           # 项目说明
│   ├── ARCHITECTURE.md     # 系统架构设计
│   ├── DATABASE.md         # 数据库设计文档
│   ├── DATA_LAYER.md       # 数据层设计文档
│   ├── ML_MODELS.md        # ML 模型文档
│   ├── API.md              # API 接口文档
│   └── CHANGELOG.md        # 更新日志
├── backend/                 # 后端服务
│   ├── app.py              # Flask 应用主文件
│   ├── app_db.py           # 数据库版 API（备用）
│   ├── requirements.txt    # Python 依赖
│   └── database/           # 数据库模块
│       ├── __init__.py     # 模块导出
│       ├── models.py       # 数据模型定义
│       ├── seed.py         # 种子数据脚本
│       └── healthai.db     # SQLite 数据库文件
└── frontend/                # 前端应用
    ├── index.html          # 入口 HTML
    ├── package.json        # 依赖配置
    ├── vite.config.js      # Vite 配置
    └── src/
        ├── main.js         # 应用入口
        ├── App.vue         # 根组件
        ├── api/            # API 服务层
        │   └── index.js    # API 请求封装
        ├── router/         # 路由配置
        │   └── index.js    # 路由定义
        ├── components/     # 公共组件
        │   └── layout/     # 布局组件
        ├── views/          # 页面视图
        │   ├── Home.vue           # 首页
        │   ├── Consultation.vue   # 智能问诊
        │   ├── HealthData.vue     # 健康数据
        │   ├── RiskAssessment.vue # 风险评估
        │   └── Profile.vue        # 个人中心
        └── assets/         # 静态资源
            └── styles/     # 全局样式
```

## 快速开始

### 环境要求
- Node.js >= 18
- Python >= 3.9

### 安装依赖

```bash
# 后端依赖
cd MVP/backend
pip install -r requirements.txt

# 前端依赖
cd MVP/frontend
npm install
```

### 初始化数据库

```bash
cd MVP/backend
python3 database/seed.py
```

### 启动服务

```bash
# 启动后端 (端口 5000)
cd MVP/backend
python3 app.py

# 启动前端 (端口 5173)
cd MVP/frontend
npm run dev
```

### 访问应用

- 前端: http://localhost:5173
- 后端 API: http://127.0.0.1:5000/api

## 功能模块

### 1. 首页仪表盘
- 健康评分展示
- 今日健康指标概览
- 快捷操作入口
- 最近健康记录

### 2. 智能问诊
- 实时对话交互
- 症状分析与建议
- 问诊历史记录

### 3. 健康数据
- 健康指标卡片展示
- ECharts 趋势图表
- 数据录入功能
- 历史记录查看

### 4. 风险评估
- 多种评估类型（心血管、糖尿病、代谢综合征等）
- 风险等级评估
- 风险因素分析
- 健康建议

### 5. 个人中心
- 用户信息展示
- 健康统计数据
- 健康标签
- 健康报告列表

## 设计规范

采用 Meta 风格的扁平化极简设计：
- 主色调: #0866FF (Meta Blue)
- 圆角: 8px / 12px
- 阴影: 轻量级投影
- 字体: 系统字体栈

## 开发团队

HealthAI 毕业设计项目

## 许可证

MIT License
