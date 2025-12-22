# Dify 接入指南

本文档介绍如何接入 Dify 平台实现真实的智能问诊功能。

## 一、启动 Dify 平台

### 1. 准备工作

确保已安装 Docker 和 Docker Compose（推荐使用 OrbStack）。

### 2. 启动 Dify

```bash
cd MVP/dify/docker
cp .env.example .env
docker compose up -d
```

首次启动需要拉取镜像，可能需要几分钟。

### 3. 访问 Dify

启动完成后，访问 http://localhost 进行初始化设置：
- 创建管理员账号
- 完成初始配置

## 二、创建健康咨询应用

### 1. 创建应用

1. 登录 Dify 控制台
2. 点击「创建应用」→「从空白创建」
3. 选择「聊天助手」类型
4. 命名为 `HealthAI 智能问诊`

### 2. 配置模型

1. 进入「设置」→「模型供应商」
2. 添加你的 LLM 提供商（如 OpenAI、智谱、通义千问等）
3. 配置 API Key

### 3. 设置系统提示词

在应用的「提示词编排」中设置：

```
你是 HealthAI 智能健康助手，一个专业的医疗健康咨询 AI。

## 你的职责
1. 分析用户描述的症状，提供可能的原因分析
2. 给出专业的健康建议和生活方式指导
3. 在必要时建议用户就医，并推荐相应科室

## 回复格式要求
- 使用 Markdown 格式组织内容
- 包含清晰的标题和分点列表
- 语气专业但亲切易懂

## 重要原则
- 始终提醒用户：AI 建议仅供参考，不能替代专业医疗诊断
- 如遇紧急症状（如胸痛、呼吸困难、大量出血等），立即建议拨打 120 或就近就医
- 不做具体疾病诊断，只提供健康建议和就医指引
- 保护用户隐私，不询问不必要的个人信息
```

### 4. 发布应用

1. 点击「发布」按钮
2. 进入「访问 API」页面
3. 复制 API Key（格式如 `app-xxxxxxxxxxxxxxxx`）

## 三、配置后端

### 1. 修改环境变量

编辑 `MVP/backend/.env` 文件：

```bash
# 启用 Dify
DIFY_ENABLED=true

# 填入你的 API Key
DIFY_API_KEY=app-xxxxxxxxxxxxxxxxxxxxxxxx

# Dify API 地址（本地部署默认为）
DIFY_BASE_URL=http://localhost/v1
```

### 2. 安装依赖

```bash
cd MVP/backend
pip install -r requirements.txt
```

### 3. 重启后端

```bash
python app_db.py
```

看到 `✅ Dify API 已启用` 表示配置成功。

## 四、测试

1. 启动前端：`cd MVP/frontend && npm run dev`
2. 访问 http://localhost:5173
3. 进入「智能问诊」页面
4. 输入症状描述，验证 AI 回复是否来自 Dify

## 五、高级配置（可选）

### 使用工作流模式

如果需要更复杂的逻辑（如 RAG 知识库检索），可以创建 Dify 工作流：

1. 创建「工作流」类型应用
2. 设计工作流节点：
   - 开始节点 → LLM 节点 → 结束节点
   - 可添加知识库检索节点实现 RAG
3. 修改后端代码使用 `client.run_workflow()` 方法

### 接入知识库

1. 在 Dify 中创建知识库
2. 上传医疗健康相关文档
3. 在工作流中添加「知识检索」节点
4. 将检索结果作为 LLM 的上下文

## 六、故障排除

### Dify 启动失败

```bash
# 查看日志
docker compose logs -f

# 重启服务
docker compose restart
```

### API 调用失败

1. 检查 API Key 是否正确
2. 确认 Dify 服务正在运行
3. 检查网络连接（本地部署确保端口 80 可访问）

### 降级到本地模式

如果 Dify 不可用，系统会自动降级到本地关键字匹配模式，确保基本功能可用。

---

## 相关文件

- `MVP/backend/dify_client.py` - Dify API 客户端
- `MVP/backend/.env` - 环境变量配置
- `MVP/backend/app_db.py` - 后端主程序（已集成 Dify）
