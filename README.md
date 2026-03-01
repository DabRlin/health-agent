# HealthAI - 基于 AI Agent 的个人健康风险预测与智能健康咨询系统

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/Vue-3.0+-green.svg)](https://vuejs.org/)

> 毕业设计项目

## 📖 项目简介

HealthAI 是一个智能健康管理系统，融合了机器学习模型、RAG 知识库和自建 LLM Agent 技术，为用户提供：

- 🏥 **疾病风险预测** - 基于 Framingham、FINDRISC 等医学评估模型
- 📊 **健康趋势分析** - 时序数据分析、异常检测、健康评分
- 🤖 **智能健康咨询** - 自建 LLM Agent，支持工具调用与流式对话
- � **体检报告解析** - 上传 PDF/图片，AI 自动 OCR + LLM 结构化解析
- 📚 **RAG 健康知识库** - 基于《默克家庭诊疗手册》的检索增强问答
- � **数据可视化** - ECharts 健康趋势图表

## ✨ 核心功能

### 1. 智能问诊（LLM Agent）
- 基于 ReAct 循环的自建 Agent，自主决策调用工具
- 支持流式输出，工具调用期间显示思考状态
- 滑动窗口对话历史管理
- 工具链：查询健康指标、趋势分析、风险评估、健康档案、录入数据、知识库查询、体检报告解读

### 2. RAG 健康知识库
- 基于《默克家庭诊疗手册》构建，约 360 个文本块
- 向量检索：SiliconFlow `BAAI/bge-m3` 嵌入 + ChromaDB 本地存储
- 精排：`BAAI/bge-reranker-v2-m3` Reranker，Top-3 结果
- 索引未就绪时自动降级到结构化知识库

### 3. 体检报告
- 上传 PDF / 图片，后端 OCR 提取文本
- LLM 结构化解析：生成指标摘要和健康建议
- 支持历史报告列表查看，支持按 ID 跳转定位

### 4. 风险评估
- **心血管疾病风险** - Framingham Risk Score (2008)
- **糖尿病风险** - FINDRISC 评分系统
- **代谢综合征** - IDF/NCEP ATP III 标准
- 风险因素分析 + 个性化健康建议

### 5. 健康数据管理
- 健康指标录入（血压、血糖、心率、BMI 等）
- 概览/血压/血糖/心率 Tab 切换联动图表
- 异常检测和预警通知

### 6. 健康档案与标签
- 完整健康档案（身体数据、生化指标、生活习惯、家族病史）
- 档案完整度进度条
- 智能健康标签：AI 基于档案数据自动评估生成，支持手动添加/编辑

### 7. 健康报告
- 汇总体检报告（exam）与系统生成报告（风险评估、健康分析）
- 按来源分组展示，支持跳转详情

### 8. 顶栏功能
- **搜索框**：实时搜索页面导航 + 健康报告 + 体检报告，分组下拉展示
- **通知**：指标异常 / 高中风险评估 / 体检报告解析完成，支持已读状态
- **设置**：个人信息编辑、修改密码、通知偏好配置

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
- **LLM Agent**: 自建 ReAct Agent，基于 OpenAI SDK 调用硅基流动 API
- **RAG**: ChromaDB 向量库 + SiliconFlow bge-m3 嵌入 + bge-reranker-v2-m3 精排
- **OCR**: pdfplumber（PDF）+ pytesseract（图片）

### ML 模型
- **风险评估**: Framingham、FINDRISC、代谢综合征
- **趋势分析**: 移动平均、线性回归
- **异常检测**: Z-Score、IQR、医学阈值

## 📁 项目结构

```
health-agent/
├── backend/                 # 后端服务
│   ├── app.py              # Flask 应用入口
│   ├── config.py           # 配置管理
│   ├── database/           # 数据库模块
│   │   ├── models.py       # SQLAlchemy 模型
│   │   ├── seed.py         # 种子数据生成
│   │   └── __init__.py
│   ├── services/           # 业务逻辑层
│   │   ├── ml_models/      # ML 模型实现
│   │   ├── agent_service.py    # LLM Agent ReAct 循环
│   │   ├── agent_tools.py      # Agent 工具链（7 个工具）
│   │   ├── rag_service.py      # RAG 检索 + 精排服务
│   │   ├── exam_service.py     # 体检报告 OCR + LLM 解析
│   │   ├── health_service.py
│   │   ├── risk_service.py
│   │   ├── trend_service.py
│   │   ├── auth_service.py
│   │   └── user_service.py
│   ├── routes/             # API 路由层
│   ├── rag_data/           # RAG 知识库
│   │   ├── build_index.py  # 索引构建脚本
│   │   ├── 默克家庭诊疗手册.txt
│   │   └── chroma_db/      # 向量索引（已 .gitignore）
│   └── utils/              # 工具模块
│       ├── llm_client.py   # LLM 客户端封装
│       └── jwt_utils.py    # JWT 工具
└── frontend/                # 前端应用
    ├── src/
    │   ├── views/          # 页面视图
    │   │   ├── Home.vue
    │   │   ├── Consultation.vue  # 智能问诊
    │   │   ├── HealthData.vue    # 健康数据
    │   │   ├── RiskAssessment.vue
    │   │   ├── ExamReport.vue    # 体检报告
    │   │   ├── Profile.vue       # 健康档案
    │   │   ├── Reports.vue       # 健康报告列表
    │   │   └── Settings.vue      # 设置
    │   ├── components/
    │   │   └── layout/
    │   │       ├── Header.vue    # 顶栏（搜索+通知+设置）
    │   │       └── Sidebar.vue
    │   ├── router/         # 路由配置
    │   └── api/            # API 服务层
    └── package.json
```

## 🚀 快速开始

### 环境要求
- Node.js >= 18
- Python >= 3.9

### 1. 克隆项目

```bash
git clone https://github.com/DabRlin/health-agent.git
cd health-agent
```

### 2. 后端设置

```bash
cd backend

# 创建并激活虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 初始化数据库
python database/seed.py

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入硅基流动 API Key（https://cloud.siliconflow.cn）

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

### 4. 环境变量说明

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `LLM_API_KEY` | 硅基流动 API Key | 必填 |
| `LLM_BASE_URL` | LLM API 地址 | `https://api.siliconflow.cn/v1` |
| `LLM_MODEL` | 使用的模型 | `Pro/zai-org/GLM-4.7` |
| `LLM_MAX_HISTORY` | 对话历史滑动窗口大小 | `10` |

## 🤖 Agent 架构说明

智能问诊模块采用自建 ReAct（Reasoning + Acting）Agent：

1. **用户发送消息** → Agent 接收并构建上下文（系统提示 + 滑动窗口历史）
2. **LLM 推理** → 判断是否需要调用工具（`stream=False`）
3. **工具执行** → 调用对应服务获取真实数据，结果追加到上下文
4. **循环推理** → 重复步骤 2-3，直到无需更多工具调用
5. **流式输出** → 最终回复以 `stream=True` 实时推送到前端

**可用工具（7 个）：**
- `get_health_metrics` - 查询用户最新健康指标
- `get_health_trend` - 分析指定指标的历史趋势
- `run_risk_assessment` - 运行心血管/糖尿病/代谢综合征风险评估
- `get_user_profile` - 获取用户健康档案
- `add_health_metric` - 录入新的健康数据
- `get_health_knowledge` - RAG 知识库检索（优先向量检索，降级到结构化库）
- `analyze_exam_report` - 解读最近一份体检报告

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

## 🎯 开发路线图

- [x] 项目架构设计
- [x] 前端 UI 框架搭建
- [x] 后端 API 开发
- [x] 数据库设计与实现
- [x] JWT 用户认证
- [x] ML 风险评估模型集成
- [x] 健康趋势分析模块
- [x] 自建 LLM Agent（ReAct + Function Calling）
- [x] Agent 工具链（7 个工具）
- [x] 流式输出 + 思考状态显示
- [x] 体检报告 OCR + LLM 解析
- [x] RAG 健康知识库（ChromaDB + bge-m3 + Reranker）
- [x] 健康数据图表 Tab 切换
- [x] 健康档案完整度 + 智能标签
- [x] 健康报告列表页
- [x] 顶栏搜索 / 通知 / 设置
- [ ] 移动端适配

## 🔒 免责声明

⚠️ **重要提示**：本系统仅供健康参考和学术研究，所提供的风险评估与健康建议不能替代专业医疗诊断。如有健康问题，请及时前往正规医疗机构就医。

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 👨‍💻 作者

毕业设计项目 - HealthAI

## 🙏 致谢

- [Framingham Heart Study](https://framinghamheartstudy.org/)
- [FINDRISC](https://www.diabetes.fi/english)
- [SiliconFlow](https://siliconflow.cn/)
- [Vue.js](https://vuejs.org/)
- [Flask](https://flask.palletsprojects.com/)
