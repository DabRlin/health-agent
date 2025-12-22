# HealthAI MVP 更新日志

所有重要的项目变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)。

---

## [0.1.0] - 2024-12-03

### 新增

#### 前端
- **项目初始化**: 使用 Vite + Vue 3 搭建前端项目
- **路由系统**: 配置 Vue Router，支持 5 个主要页面
- **设计系统**: 实现 Meta 风格的扁平化极简 UI
  - CSS 变量定义（颜色、间距、圆角、阴影）
  - 响应式布局支持
  - 通用组件样式（按钮、卡片、徽章等）
- **布局组件**: 
  - `AppLayout.vue` - 应用主布局
  - `Sidebar.vue` - 侧边导航栏
  - `Header.vue` - 顶部标题栏
- **页面视图**:
  - `Home.vue` - 首页仪表盘
  - `Consultation.vue` - 智能问诊
  - `HealthData.vue` - 健康数据管理
  - `RiskAssessment.vue` - 风险评估
  - `Profile.vue` - 个人中心
- **API 服务层**: 封装所有后端 API 请求
- **ECharts 图表**: 健康数据趋势图表
- **数据录入弹窗**: 支持添加健康指标

#### 后端
- **Flask 应用**: 创建 RESTful API 服务
- **CORS 处理**: 支持跨域请求
- **API 接口**:
  - 用户信息相关 API
  - 健康数据相关 API
  - 风险评估相关 API
  - 智能问诊相关 API
  - 首页仪表盘 API
- **模拟数据**: 生成各类健康数据用于演示

#### 数据库
- **SQLite 数据库**: 本地数据持久化
- **SQLAlchemy ORM**: 数据模型定义
- **数据表**:
  - users - 用户表
  - health_records - 健康记录表
  - health_metrics - 健康指标表
  - risk_assessments - 风险评估表
  - consultations - 问诊会话表
  - consultation_messages - 问诊消息表
  - health_reports - 健康报告表
  - health_tags - 健康标签表
- **种子数据脚本**: 自动生成 30 天模拟数据

#### 文档
- `README.md` - 项目说明文档
- `API.md` - API 接口文档
- `DATABASE.md` - 数据库设计文档
- `CHANGELOG.md` - 更新日志

### 修复
- 解决 CORS 跨域问题（localhost vs 127.0.0.1）
- 修复前端数据加载状态管理

### 技术栈
- **前端**: Vue 3, Vite, Vue Router, ECharts, Lucide Icons
- **后端**: Flask, SQLAlchemy
- **数据库**: SQLite

---

## [0.2.0] - 2024-12-06

### 新增

#### 用户认证系统
- JWT Token 认证机制
- 用户登录/注册功能
- 登录状态持久化
- 路由守卫保护

#### 个人信息管理
- 用户资料编辑功能
- 个人信息更新 API

#### 架构文档
- 新增 `ARCHITECTURE.md` 系统架构设计文档
- 明确三大核心模块：智能问诊、体检报告分析、健康数据分析
- 定义 ML 模型接入方案
- 规划智能穿戴设备数据方案

#### 数据层建设
- 新增 `device_readings` 穿戴设备原始数据表
- 新增 `daily_health_summaries` 每日健康汇总表
- 新增 `user_health_profiles` 用户健康档案表
- 实现穿戴设备数据模拟器 `device_simulator.py`
- 生成30天模拟数据（心率、步数、睡眠、血氧等）

#### ML 模型集成
- **Framingham Risk Score**: 心血管疾病10年风险评估
- **FINDRISC**: 糖尿病10年风险评估
- **代谢综合征评估**: 基于 IDF/NCEP ATP III 标准
- 重构 `RiskService` 使用真实 ML 模型
- 风险因素详细分析和个性化健康建议

#### 趋势分析模块
- **TrendAnalyzer**: 移动平均、线性回归、趋势预测
- **AnomalyDetector**: Z-Score、IQR、医学阈值异常检测
- **HealthScoreCalculator**: 多维度综合健康评分
- 新增 `TrendService` 整合趋势分析功能
- 新增 `/api/trend/*` API 路由

---

## 待开发功能

### Phase 1: 数据基础建设 ✅
- [x] 穿戴设备数据表设计
- [x] 模拟数据生成脚本
- [x] 数据聚合服务

### Phase 2: ML 模型集成 ✅
- [x] Framingham 心血管风险评估
- [x] FINDRISC 糖尿病风险评分
- [x] 代谢综合征风险评估

### Phase 3: 趋势分析 ✅
- [x] 血压趋势预测
- [x] 异常检测模型
- [x] 预测结果展示
- [x] 综合健康评分

### Phase 4: 体检报告分析
- [ ] PDF/图片上传
- [ ] OCR 文字提取
- [ ] LLM 报告解读

### Phase 5: 健康画像
- [ ] 多模块数据整合
- [ ] 综合健康评分
- [ ] 个性化建议

### 其他计划
- [ ] 问诊历史查看功能
- [ ] 健康报告详情页
- [ ] 数据导出功能
- [ ] 深色模式支持

---

## 版本说明

- **主版本号**: 重大架构变更
- **次版本号**: 新功能添加
- **修订号**: Bug 修复和小改进

当前版本: **0.2.0**
