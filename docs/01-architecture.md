# HealthAI 项目结构与架构总览

> 更新日期：2025-03

---

## 一、项目简介

HealthAI 是一个面向个人用户的智能健康管理系统，核心目标是将 AI 大语言模型（LLM）、多模态视觉模型（VL）与传统医学评估算法深度融合，提供：

- 多科室 AI 智能问诊（ReAct Agent）
- 个人健康指标监测与趋势分析
- 四大医学风险模型评估
- PDF/图片体检报告 OCR 自动解析
- 药品说明书智能识别与用药管理
- 基于《默克家庭诊疗手册》的 RAG 知识检索

---

## 二、整体技术栈

| 层次 | 技术 | 版本/说明 |
|------|------|-----------|
| 前端框架 | Vue 3 + Vite | Composition API，SPA |
| UI 组件 | Lucide Vue Next | 图标库 |
| Markdown 渲染 | marked.js | 消息渲染 |
| 后端框架 | Flask | 3.0.0，Python |
| ORM | SQLAlchemy | 2.0.23 |
| 数据库 | SQLite | 单文件，`backend/database/healthai.db` |
| 认证 | JWT（PyJWT） | Bearer Token |
| LLM 主模型 | GLM-4.7（硅基流动） | `Pro/zai-org/GLM-4.7`，OpenAI 兼容格式 |
| VL 视觉模型 | Qwen2.5-VL-72B | 皮肤图像分析、说明书 OCR |
| OCR 模型 | DeepSeek-OCR | 体检报告图片文字提取 |
| RAG 向量库 | ChromaDB | 持久化本地存储 |
| Embedding | BAAI/bge-m3 | 硅基流动 API |
| Reranker | BAAI/bge-reranker-v2-m3 | 硅基流动 API |
| LLM SDK | openai >= 1.0.0 | 兼容硅基流动 |

---

## 三、目录结构

```
Graduation Develop_副本/
├── backend/                    # Flask 后端
│   ├── app.py                  # 应用入口，蓝图注册
│   ├── config.py               # 配置管理（环境变量）
│   ├── .env                    # 敏感配置（不入版本库）
│   ├── .env.example            # 配置模板
│   ├── requirements.txt        # Python 依赖
│   ├── database/
│   │   ├── models.py           # SQLAlchemy ORM 模型（12 张表）
│   │   ├── healthai.db         # SQLite 数据库文件
│   │   ├── seed.py             # 初始数据填充脚本
│   │   └── device_simulator.py # 穿戴设备数据模拟器
│   ├── routes/                 # Flask 蓝图路由层
│   │   ├── auth.py             # /api/auth/*  认证
│   │   ├── user.py             # /api/user/*  用户档案
│   │   ├── health.py           # /api/metrics/* /api/records/*  健康数据
│   │   ├── consultation.py     # /api/consultation/*  智能问诊
│   │   ├── risk.py             # /api/risk/*  风险评估
│   │   ├── trend.py            # /api/trend/*  趋势分析
│   │   ├── exam.py             # /api/exam/*  体检报告
│   │   ├── medication.py       # /api/medications/*  用药管理
│   │   ├── medical.py          # /api/medical/*  医疗资料（用户只读）
│   │   └── admin.py            # /api/admin/*  管理后台
│   ├── services/               # 业务逻辑层
│   │   ├── agent_service.py    # ReAct Agent 核心（多科室，流式输出）
│   │   ├── agent_tools.py      # Agent 工具链（7 个工具 + Function Calling Schema）
│   │   ├── risk_service.py     # 风险评估调度（调用 ML 模型）
│   │   ├── trend_service.py    # 趋势分析（含穿戴设备数据）
│   │   ├── health_service.py   # 健康指标 CRUD
│   │   ├── user_service.py     # 用户信息管理
│   │   ├── exam_service.py     # 体检报告 OCR + LLM 解析
│   │   ├── vl_service.py       # 视觉语言模型（皮肤分析 + 说明书 OCR）
│   │   ├── rag_service.py      # RAG 检索（ChromaDB + bge-m3 + reranker）
│   │   ├── auth_service.py     # 认证逻辑（注册/登录/JWT）
│   │   ├── admin_service.py    # 管理员操作
│   │   └── auto_tag_service.py # 自动健康标签评估
│   │   └── ml_models/          # ML 风险评估模型
│   │       ├── cardiovascular.py  # Framingham 心血管风险
│   │       ├── diabetes.py        # FINDRISC 糖尿病风险
│   │       ├── metabolic.py       # 代谢综合征评估
│   │       ├── osteoporosis.py    # FRAX® 骨质疏松风险
│   │       └── trend_analysis.py  # 趋势分析 + 异常检测算法
│   ├── utils/
│   │   ├── jwt_utils.py        # JWT 签发与校验工具
│   │   └── llm_client.py       # OpenAI SDK 封装（指向硅基流动）
│   └── rag_data/
│       ├── 默克家庭诊疗手册.txt  # RAG 知识源（3.5MB）
│       ├── build_index.py       # 构建 ChromaDB 向量索引脚本
│       └── chroma_db/           # 持久化向量数据库
├── frontend/                    # Vue 3 前端
│   ├── src/
│   │   ├── main.js              # 应用入口
│   │   ├── App.vue              # 根组件（路由出口）
│   │   ├── api/index.js         # 全量 API 请求封装
│   │   ├── router/index.js      # Vue Router 路由配置
│   │   ├── views/               # 页面组件（14 个）
│   │   └── components/layout/   # 布局组件
│   ├── package.json
│   └── vite.config.js
├── docs/                        # 项目文档（本目录）
└── thesis-latex/                # 毕业论文 LaTeX 源文件
```

---

## 四、系统架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                         浏览器 / 前端                                │
│   Vue 3 + Vite  (localhost:5173)                                     │
│   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│   │ 智能问诊  │ │ 健康数据 │ │ 风险评估 │ │ 体检报告 │ │ 用药管理 │ │
│   └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ │
└────────┼─────────────┼────────────┼─────────────┼────────────┼──────┘
         │  HTTP REST / SSE 流式    │             │            │
┌────────▼─────────────▼────────────▼─────────────▼────────────▼──────┐
│                    Flask 后端 (127.0.0.1:5000)                        │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │                         Routes（蓝图层）                      │    │
│  │  auth  user  health  consultation  risk  trend  exam  ...    │    │
│  └───────────────────────────┬──────────────────────────────────┘    │
│  ┌────────────────────────────▼─────────────────────────────────┐    │
│  │                        Services（业务层）                     │    │
│  │  ┌────────────────┐  ┌──────────────┐  ┌──────────────────┐  │    │
│  │  │  AgentService  │  │ RiskService  │  │  ExamService     │  │    │
│  │  │  (ReAct Loop)  │  │  (ML模型)    │  │  (OCR+LLM解析)   │  │    │
│  │  └───────┬────────┘  └──────┬───────┘  └─────────┬────────┘  │    │
│  │  ┌───────▼────────┐  ┌──────▼───────┐  ┌─────────▼────────┐  │    │
│  │  │  AgentTools    │  │  ml_models/  │  │   VLService      │  │    │
│  │  │  (7 工具函数)   │  │  Framingham  │  │  (Qwen2.5-VL)    │  │    │
│  │  │               │  │  FINDRISC    │  └─────────┬────────┘  │    │
│  │  │               │  │  FRAX®       │            │           │    │
│  │  └───────┬────────┘  └──────────────┘           │           │    │
│  │  ┌───────▼────────┐  ┌──────────────────────────▼─────────┐ │    │
│  │  │  RAGService    │  │           llm_client.py             │ │    │
│  │  │  ChromaDB      │  │      (OpenAI SDK → 硅基流动)         │ │    │
│  │  └────────────────┘  └─────────────────────────────────────┘ │    │
│  └──────────────────────────────────────────────────────────────┘    │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │                     Database（SQLite）                        │    │
│  │  accounts / users / health_metrics / consultations /         │    │
│  │  risk_assessments / exam_reports / medications / ...         │    │
│  └──────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
         │                                         │
         ▼                                         ▼
┌─────────────────┐                    ┌─────────────────────────┐
│  硅基流动 API    │                    │   ChromaDB 本地向量库    │
│  GLM-4.7        │                    │   默克家庭诊疗手册        │
│  Qwen2.5-VL-72B │                    │   bge-m3 Embedding      │
│  DeepSeek-OCR   │                    │   bge-reranker-v2-m3    │
│  bge-m3         │                    └─────────────────────────┘
│  bge-reranker   │
└─────────────────┘
```

---

## 五、数据库模型概览

系统共 12 张数据库表，分为三个层次：

### 用户体系
| 表名 | 说明 |
|------|------|
| `accounts` | 账户表（登录认证，存储 scrypt hash 密码） |
| `users` | 用户信息表（姓名、性别、年龄、健康评分） |
| `user_health_profiles` | 健康档案（身体指标、血液指标、生活习惯、病史） |

### 健康数据
| 表名 | 说明 |
|------|------|
| `health_metrics` | 健康指标记录（心率、血压、血糖、BMI、睡眠，含时间序列索引） |
| `health_records` | 健康记录流水（体检报告、日常监测、风险评估等） |
| `health_tags` | 健康标签（用户手动 + 系统自动评估，分 positive/warning/neutral） |
| `device_readings` | 穿戴设备原始数据（高频采集，含 steps、spo2 等） |
| `daily_health_summaries` | 每日健康汇总（心率/活动/睡眠/血氧统计） |
| `risk_assessments` | 风险评估历史记录 |

### AI / 内容
| 表名 | 说明 |
|------|------|
| `consultations` | 问诊会话（科室、状态、会话 ID） |
| `consultation_messages` | 问诊消息（role: user/assistant） |
| `exam_reports` | 体检报告（原始文件、OCR 文字、LLM 结构化解析结果） |
| `medications` | 用药记录（结构化提醒 + 非结构化说明书内容） |
| `health_knowledge` | 结构化健康知识库（疾病/指标/饮食/药物/症状/生活方式） |

---

## 六、请求认证机制

所有需要登录的接口均使用 **JWT Bearer Token** 认证：

1. 登录成功后，服务端签发 JWT，存储于前端 `localStorage`
2. 每次请求在 `Authorization: Bearer <token>` 头中携带
3. 服务端通过 `@login_required` 装饰器校验（`backend/utils/jwt_utils.py`）
4. Token 过期或无效时返回 401，前端自动清除 token 并跳转到 `/landing`

---

## 七、前端路由结构

| 路径 | 页面 | 权限 |
|------|------|------|
| `/landing` | 产品主页 | 公开 |
| `/login` | 登录 | 公开 |
| `/register` | 注册 | 公开 |
| `/` | 首页仪表盘 | 登录 |
| `/consultation` | 科室选择 | 登录 |
| `/consultation/chat` | 智能问诊对话 | 登录 |
| `/health-data` | 健康数据管理 | 登录 |
| `/risk-assessment` | 风险评估 | 登录 |
| `/profile` | 健康档案 | 登录 |
| `/exam-report` | 体检报告 | 登录 |
| `/medical-data` | 医疗资料 | 登录 |
| `/medication` | 用药管理 | 登录 |
| `/settings` | 账户设置 | 登录 |
| `/admin` | 管理后台 | 管理员 |

---

## 八、环境启动方式

### 后端
```bash
# 进入项目根目录
cd "Graduation Develop_副本"

# 激活虚拟环境
source .venv/bin/activate

# 启动 Flask
python backend/app.py
# 默认运行在 http://127.0.0.1:5000
```

### 前端
```bash
cd "Graduation Develop_副本/frontend"
npm install       # 首次安装依赖
npm run dev       # 运行在 http://localhost:5173
```

### RAG 索引构建（首次 / 知识库更新时）
```bash
source .venv/bin/activate
python backend/rag_data/build_index.py
```
