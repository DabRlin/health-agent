# HealthAI - 基于 AI Agent 的个人健康风险预测与智能健康咨询系统

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/Vue-3.0+-green.svg)](https://vuejs.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-lightgrey.svg)](https://flask.palletsprojects.com/)

> 毕业设计项目 — 基于大语言模型 Agent 与机器学习的个人健康管理平台

## 📖 项目简介

HealthAI 是一个全栈智能健康管理系统，深度融合自建 LLM Agent、视觉语言模型（VL）、RAG 知识检索增强、机器学习风险评估模型等 AI 技术，为用户提供一站式的健康数据管理、智能问诊、疾病风险预测和健康知识服务。

- 🤖 **自建 LLM Agent** — ReAct 循环架构，7 个工具链，流式输出 + 思考状态可视化
- 🏥 **多科室智能问诊** — 全科、心内科、内分泌科、皮肤科，各科独立提示与工具链
- 👁️ **VL 视觉语言模型** — Qwen2.5-VL-72B 驱动皮肤图像分析与药品说明书 OCR
- 📊 **4 大风险评估模型** — Framingham、FINDRISC、代谢综合征、FRAX® 权威医学模型
- 📚 **RAG 知识库** — 基于《默克家庭诊疗手册》，向量检索 + Reranker 精排
- � **健康趋势分析** — 时序异常检测、趋势预测、ECharts 可视化
- 💊 **用药管理** — VL 模型 OCR 药品说明书 + 服药提醒
- 📋 **体检报告解析** — PDF/图片上传，OCR + LLM 结构化解析

## ✨ 功能模块

### 1. 智能问诊（LLM Agent + 多科室）
- 自建 ReAct 循环 Agent，自主决策调用工具获取真实用户数据
- **4 大门诊科室**：全科、心内科、内分泌科、皮肤科，各科独立系统提示与工具链
- 流式输出 + 工具调用期间实时显示"思考状态"
- 滑动窗口对话历史（默认保留最近 10 条）
- 会话管理：新建 / 切换 / 删除 / 双击重命名，按最新消息时间排序
- **皮肤科图像分析**：上传皮肤图片，VL 模型（Qwen2.5-VL-72B）分析后注入对话上下文

### 2. 用药管理（VL OCR + 提醒）
- 上传药品说明书图片，VL 模型自动 OCR 提取药品名称、用法用量、禁忌症、副作用等
- 提取结果供用户确认编辑后保存
- 用药 CRUD（创建 / 查看 / 编辑 / 删除）
- **服药提醒**：基于设定时间自动检测，支持浏览器系统通知

### 3. RAG 健康知识库
- 基于《默克家庭诊疗手册》构建，约 360 个文本块
- **向量检索**：SiliconFlow `BAAI/bge-m3` 嵌入 + ChromaDB 本地持久化
- **精排**：`BAAI/bge-reranker-v2-m3` Reranker，Top-3 结果
- **分科索引**：全科、心内科、内分泌科、皮肤科各有独立 collection
- 索引未就绪时自动降级到结构化知识库（14 条预置条目）
- 前端"医疗资料"页面可直接浏览和搜索

### 4. 体检报告解析
- 上传 PDF / 图片格式体检报告
- 后端 OCR 提取文本（PyMuPDF 处理 PDF，VL 模型处理图片）
- LLM 结构化解析：指标名称、数值、单位、参考范围、状态
- 历史报告列表，状态追踪（待处理/解析中/已完成），支持删除

### 5. 风险评估（4 大医学模型）
- **心血管疾病风险** — Framingham Risk Score (2008)，Cox 回归模型
- **糖尿病风险** — FINDRISC 评分系统，循证评分量表
- **代谢综合征** — IDF/NCEP ATP III 诊断标准，规则引擎
- **骨质疏松风险** — FRAX® 骨折风险评估，Logistic 回归模型
- 输出：风险等级、评分、风险因素分析、个性化健康建议

### 6. 健康数据管理
- 6 类指标：心率、收缩压、舒张压、空腹血糖、BMI、睡眠时长
- 每日唯一制（同日同类型自动更新）
- 4 个 Tab 图表：概览 / 血压（双轨）/ 血糖 / 心率
- 历史曲线 + 异常标注 + 预测曲线 + 正常范围标线
- 统计摘要：平均值、最高、最低、异常次数

### 7. 健康档案与智能标签
- 完整档案编辑：身体数据、血压基线、血液指标、生活习惯、家族病史
- 档案完整度进度条，BMI 自动计算
- **智能标签**：AI 自动评估生成系统标签 + 用户自定义标签

### 8. 首页仪表盘
- 健康评分 + 核心指标卡片（最新值 + 趋势箭头 + 状态颜色）
- 最近健康记录时间线 + 快捷入口

### 9. 顶栏功能
- **全局搜索**：页面导航 + 健康报告 + 体检报告，分组下拉
- **通知中心**：指标异常 / 风险提醒 / 报告解析完成，已读状态管理

### 10. 管理员后台
- 用户列表管理、账户激活/禁用、密码重置
- admin 角色路由守卫

### 11. 认证系统
- JWT Token 认证，登录/注册/登出
- 路由守卫区分公开/登录/管理员页面，401 自动跳转
- Canvas 验证码校验

## 🛠️ 技术栈

### 前端

| 技术 | 说明 |
|------|------|
| Vue 3 + Vite | 前端框架与构建工具 |
| Vue Router 4 | 路由管理 + 权限守卫 |
| ECharts + vue-echarts | 健康数据可视化图表 |
| Lucide Vue Next | 图标库 |
| 原生 CSS | Meta 风格设计系统，CSS 变量主题 |

### 后端

| 技术 | 说明 |
|------|------|
| Flask 3.0 | Web 框架 |
| SQLite + SQLAlchemy 2.0 | 数据库与 ORM |
| PyJWT | JWT Token 认证 |
| OpenAI SDK | LLM Agent 调用（兼容硅基流动 API） |
| ChromaDB | RAG 向量数据库 |
| httpx | HTTP 客户端（嵌入/精排 API） |
| PyMuPDF (fitz) | PDF 文本提取 |
| Werkzeug | 密码哈希（scrypt） |

### AI 模型

| 模型 | 用途 |
|------|------|
| GLM-4.7 (SiliconFlow) | LLM Agent 推理、体检报告解析 |
| Qwen2.5-VL-72B-Instruct | 皮肤图像分析、药品说明书 OCR |
| BAAI/bge-m3 | RAG 文本嵌入 |
| BAAI/bge-reranker-v2-m3 | RAG 检索精排 |

### ML 风险评估 & 趋势分析

| 模型 | 类型 | 文献依据 |
|------|------|----------|
| Framingham Risk Score | Cox 回归 | D'Agostino et al., *Circulation* 2008 |
| FINDRISC | 循证评分量表 | Lindström & Tuomilehto, *Diabetes Care* 2003 |
| 代谢综合征 | 规则引擎 | IDF/NCEP ATP III, *Circulation* 2009 |
| FRAX® | Logistic 回归 | Kanis et al., *Osteoporosis Int.* 2008 |
| 趋势分析 | 移动平均 + 线性回归 | — |
| 异常检测 | Z-Score + IQR + 医学阈值 | — |

## 📁 项目结构

```
health-agent/
├── backend/                          # 后端服务
│   ├── app.py                        # Flask 应用入口 + 统一错误处理
│   ├── config.py                     # 配置管理（LLM/VL/指标/风险类型）
│   ├── requirements.txt              # Python 依赖
│   ├── database/                     # 数据库模块
│   │   ├── models.py                 # SQLAlchemy 模型（13 张表）
│   │   ├── seed.py                   # 种子数据生成
│   │   ├── device_simulator.py       # 穿戴设备数据模拟器
│   │   └── __init__.py               # 模型导出
│   ├── services/                     # 业务逻辑层
│   │   ├── agent_service.py          # LLM Agent ReAct 循环 + 多科室
│   │   ├── agent_tools.py            # Agent 工具链（7 个工具 + Schema）
│   │   ├── rag_service.py            # RAG 向量检索 + Reranker 精排
│   │   ├── vl_service.py             # VL 视觉语言模型（皮肤分析 + OCR）
│   │   ├── exam_service.py           # 体检报告 OCR + LLM 解析
│   │   ├── health_service.py         # 健康指标 CRUD
│   │   ├── trend_service.py          # 趋势分析 + 异常检测 + 预测
│   │   ├── risk_service.py           # 风险评估调度
│   │   ├── auth_service.py           # 认证（登录/注册/改密）
│   │   ├── user_service.py           # 用户信息 + 标签 + 报告
│   │   ├── admin_service.py          # 管理员服务
│   │   ├── auto_tag_service.py       # 智能标签自动评估
│   │   └── ml_models/                # ML 模型实现
│   │       ├── cardiovascular.py     # Framingham 心血管风险
│   │       ├── diabetes.py           # FINDRISC 糖尿病风险
│   │       ├── metabolic.py          # 代谢综合征评估
│   │       ├── osteoporosis.py       # FRAX® 骨质疏松风险
│   │       └── trend_analysis.py     # 趋势分析 + 异常检测算法
│   ├── routes/                       # API 路由层
│   │   ├── auth.py                   # 认证路由
│   │   ├── health.py                 # 健康数据 + 仪表盘
│   │   ├── consultation.py           # 智能问诊（流式 SSE）
│   │   ├── exam.py                   # 体检报告上传/查询
│   │   ├── risk.py                   # 风险评估
│   │   ├── trend.py                  # 趋势分析
│   │   ├── user.py                   # 用户信息 + 标签
│   │   ├── medication.py             # 用药管理 CRUD
│   │   ├── medical.py                # 医疗资料（RAG 搜索）
│   │   └── admin.py                  # 管理员路由
│   ├── rag_data/                     # RAG 知识库
│   │   ├── build_index.py            # 索引构建脚本
│   │   ├── 默克家庭诊疗手册.txt       # 源文档
│   │   └── chroma_db/                # 向量索引（.gitignore）
│   └── utils/                        # 工具模块
│       ├── llm_client.py             # OpenAI SDK 封装 → 硅基流动
│       └── jwt_utils.py              # JWT 生成/验证/装饰器
├── frontend/                          # 前端应用
│   ├── src/
│   │   ├── views/                    # 页面视图（14 个）
│   │   │   ├── Landing.vue           # 着陆页
│   │   │   ├── Login.vue             # 登录（含验证码）
│   │   │   ├── Register.vue          # 注册
│   │   │   ├── Home.vue              # 首页仪表盘
│   │   │   ├── DepartmentSelect.vue  # 科室选择
│   │   │   ├── Consultation.vue      # 智能问诊（流式对话）
│   │   │   ├── HealthData.vue        # 健康数据（图表 + 录入）
│   │   │   ├── RiskAssessment.vue    # 风险评估
│   │   │   ├── Profile.vue           # 健康档案 + 标签
│   │   │   ├── ExamReport.vue        # 体检报告
│   │   │   ├── MedicalData.vue       # 医疗资料（RAG 浏览）
│   │   │   ├── Medication.vue        # 用药管理
│   │   │   ├── Settings.vue          # 设置
│   │   │   └── Admin.vue             # 管理员后台
│   │   ├── components/layout/        # 布局组件
│   │   │   ├── Header.vue            # 顶栏（搜索 + 通知 + 头像）
│   │   │   └── Sidebar.vue           # 侧边栏导航
│   │   ├── router/index.js           # 路由配置 + 权限守卫
│   │   └── api/index.js              # API 服务层（具名方法）
│   └── package.json
└── docs/                              # 项目文档
    ├── architecture.md               # 系统架构设计
    ├── database.md                   # 数据库设计
    ├── data-layer.md                 # 数据层设计
    ├── api.md                        # API 接口文档
    ├── ml-models.md                  # ML 模型说明
    └── changelog.md                  # 更新日志
```

## 🚀 快速开始

### 环境要求
- Python >= 3.9
- Node.js >= 18
- 硅基流动 API Key（[https://cloud.siliconflow.cn](https://cloud.siliconflow.cn)）

### 1. 克隆项目

```bash
git clone https://github.com/DabRlin/health-agent.git
cd health-agent
```

### 2. 后端设置

```bash
# 创建并激活虚拟环境（项目根目录）
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r backend/requirements.txt

# 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入硅基流动 API Key

# 初始化数据库（生成种子数据）
cd backend/database && python seed.py && cd ../..

# （可选）构建 RAG 向量索引
cd backend/rag_data && python build_index.py && cd ../..

# 启动后端服务
cd backend && python app.py
```

后端服务运行在 `http://127.0.0.1:5000`

### 3. 前端设置

```bash
cd frontend
npm install
npm run dev
```

前端应用运行在 `http://localhost:5173`

### 4. 默认账号

| 账号 | 密码 | 角色 |
|------|------|------|
| `admin` | `123456` | 管理员 |
| `user` | `123456` | 普通用户 |
| `demo` | `demo` | 普通用户 |

### 5. 环境变量说明

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `LLM_API_KEY` | 硅基流动 API Key | **必填** |
| `LLM_BASE_URL` | LLM API 地址 | `https://api.siliconflow.cn/v1` |
| `LLM_MODEL` | Agent 推理模型 | `Pro/zai-org/GLM-4.7` |
| `LLM_MAX_HISTORY` | 对话历史滑动窗口 | `10` |
| `VL_MODEL` | VL 视觉模型（皮肤分析） | `Qwen/Qwen2.5-VL-72B-Instruct` |
| `VL_OCR_MODEL` | VL OCR 模型（药品/报告） | `Qwen/Qwen2.5-VL-72B-Instruct` |

## 🤖 Agent 架构说明

智能问诊模块采用自建 ReAct（Reasoning + Acting）Agent：

1. **用户发送消息** → Agent 接收，构建上下文（科室系统提示 + 滑动窗口历史）
2. **VL 前置处理**（皮肤科）→ 若有图片，先调用 VL 模型分析，结果注入上下文
3. **LLM 推理** → 判断是否需要调用工具（`stream=False`，Function Calling）
4. **工具执行** → 调用对应服务获取真实数据，结果追加到上下文
5. **循环推理** → 重复步骤 3-4，直到无需更多工具调用
6. **流式输出** → 最终回复以 `stream=True` + SSE 实时推送到前端

**可用工具（7 个）：**

| 工具 | 功能 | 适用科室 |
|------|------|----------|
| `get_health_metrics` | 查询用户最新健康指标 | 全科/心内/内分泌 |
| `get_health_trend` | 分析指标历史趋势 + 异常检测 | 全科/心内/内分泌 |
| `run_risk_assessment` | 运行 4 种风险评估模型 | 全科/心内/内分泌 |
| `get_user_profile` | 获取用户健康档案 | 全科/心内/内分泌 |
| `add_health_metric` | 录入新的健康数据 | 全科/心内/内分泌 |
| `get_health_knowledge` | RAG 知识库检索（优先向量，降级结构化） | 全部科室 |
| `analyze_exam_report` | 解读最近一份体检报告 | 全科/心内/内分泌 |

**科室工具链配置**：各科室仅暴露相关工具子集，皮肤科仅使用知识库（图像分析由 VL 模型前置处理）。

## 📊 ML 模型详细说明

### 心血管风险评估 (Framingham Risk Score)
- **类型**: 多元 Cox 统计回归模型
- 基于 Framingham Heart Study，D'Agostino et al., *Circulation* 2008
- 预测 10 年内心肌梗死、冠心病死亡、中风等心血管事件风险
- 输入：年龄、性别、总胆固醇、HDL、收缩压、吸烟史、糖尿病史、降压药使用

### 糖尿病风险评估 (FINDRISC)
- **类型**: 循证医学评分量表（Finnish Diabetes Risk Score）
- 基于 Lindström & Tuomilehto，*Diabetes Care* 2003
- 预测未来 10 年内发生 2 型糖尿病的风险，评分范围 0–26 分
- 无需实验室检查，适合人群筛查

### 代谢综合征评估
- **类型**: 规则引擎（基于国际诊断标准）
- 基于 IDF/NCEP ATP III 联合声明，*Circulation* 2009
- 采用亚洲人群腰围标准（男 ≥90cm，女 ≥80cm）
- 腹围、甘油三酯、HDL、血压、血糖 5 项中满足 ≥3 项即确诊

### 骨质疏松风险评估 (FRAX®)
- **类型**: Logistic 回归统计模型
- 基于 WHO 骨折风险评估工具，Kanis et al., *Osteoporosis International* 2008
- 预测 10 年内主要骨质疏松性骨折及髋部骨折概率
- 无需骨密度检测（BMD-free 版本），适合初筛

## 🎯 开发路线图

- [x] 项目架构设计 + 前后端框架搭建
- [x] 数据库设计（13 张表）+ 种子数据
- [x] JWT 认证系统 + 路由守卫
- [x] 首页仪表盘（指标卡片 + 记录时间线）
- [x] 健康数据管理（6 类指标 + 每日唯一制）
- [x] 健康数据图表（4 Tab + 异常标注 + 预测曲线）
- [x] 血压双轨显示（收缩压 + 舒张压独立趋势线与预测）
- [x] ML 风险评估模型集成（4 个模型）
- [x] 健康档案编辑 + 完整度进度条
- [x] 智能标签系统（AI 自动评估 + 手动管理）
- [x] 自建 LLM Agent（ReAct + Function Calling）
- [x] Agent 工具链（7 个工具）
- [x] 多科室问诊（全科/心内/内分泌/皮肤科）
- [x] 流式输出 + 思考状态可视化
- [x] VL 视觉语言模型集成（皮肤图像分析）
- [x] 用药管理（VL OCR 药品说明书 + 服药提醒）
- [x] 体检报告 OCR + LLM 结构化解析
- [x] RAG 健康知识库（ChromaDB + bge-m3 + Reranker + 分科索引）
- [x] 医疗资料浏览页面
- [x] 顶栏搜索 / 通知中心
- [x] 设置页面（信息编辑 + 密码修改 + 通知偏好）
- [x] 管理员后台（用户管理 + 权限控制）
- [x] 着陆页
- [x] 智能问诊会话管理（排序 + 重命名 + 删除）
- [x] 穿戴设备数据模拟
- [ ] 移动端响应式适配

## 🔒 免责声明

> ⚠️ **重要提示**：本系统仅供健康参考和学术研究，所提供的风险评估与健康建议不能替代专业医疗诊断。如有健康问题，请及时前往正规医疗机构就医。

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 👨‍💻 作者

毕业设计项目 - HealthAI

## 🙏 致谢

- [Framingham Heart Study](https://framinghamheartstudy.org/) — 心血管风险评估模型
- [FINDRISC](https://www.diabetes.fi/english) — 糖尿病风险评分
- [FRAX®](https://www.sheffield.ac.uk/FRAX/) — 骨折风险评估工具
- [SiliconFlow 硅基流动](https://siliconflow.cn/) — LLM/VL/Embedding/Reranker API
- [Vue.js](https://vuejs.org/) — 前端框架
- [Flask](https://flask.palletsprojects.com/) — 后端框架
- [ChromaDB](https://www.trychroma.com/) — 向量数据库
- [ECharts](https://echarts.apache.org/) — 数据可视化
- 《默克家庭诊疗手册》 — RAG 知识库源文档
