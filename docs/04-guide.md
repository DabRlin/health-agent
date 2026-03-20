# HealthAI 项目常见问题与使用指南

> 更新日期：2025-03

---

## 一、快速启动

### 前置条件

- Python 3.10+
- Node.js 18+
- 硅基流动（SiliconFlow）API Key（[申请地址](https://siliconflow.cn)）

### 步骤一：配置环境变量

复制 `.env.example` 为 `.env`，填写必要配置：

```bash
cp backend/.env.example backend/.env
```

编辑 `backend/.env`：

```env
# 必填：硅基流动 API Key
LLM_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx

# 以下为默认值，通常无需修改
LLM_BASE_URL=https://api.siliconflow.cn/v1
LLM_MODEL=Pro/zai-org/GLM-4.7
LLM_MAX_HISTORY=10

# 视觉模型（用于皮肤图像分析、说明书 OCR）
VL_MODEL=Qwen/Qwen2.5-VL-72B-Instruct
VL_OCR_MODEL=Qwen/Qwen2.5-VL-72B-Instruct

# Flask 配置
DEBUG=true
HOST=127.0.0.1
PORT=5000
```

### 步骤二：安装后端依赖

```bash
# 在项目根目录下（确认 .venv 已创建）
source .venv/bin/activate

# 安装依赖
pip install -r backend/requirements.txt
```

### 步骤三：初始化数据库（首次）

数据库会在后端首次启动时自动创建所有表。如需填充测试数据：

```bash
source .venv/bin/activate
python backend/database/seed.py
```

### 步骤四：启动后端

```bash
source .venv/bin/activate
python backend/app.py
```

看到如下输出表示启动成功：

```
🚀 HealthAI MVP Backend starting...
📍 API running at http://127.0.0.1:5000
INFO: LLM Agent 已启用: https://api.siliconflow.cn/v1 (Pro/zai-org/GLM-4.7)
```

### 步骤五：启动前端

```bash
cd frontend
npm install    # 首次安装依赖
npm run dev    # 启动开发服务器
```

浏览器访问 `http://localhost:5173`

### 步骤六：构建 RAG 索引（可选，推荐）

若需要知识库检索功能（Agent 的 `get_health_knowledge` 工具完整能力），需构建 ChromaDB 向量索引：

```bash
source .venv/bin/activate
python backend/rag_data/build_index.py
```

构建时间约 5–15 分钟（需要调用硅基流动 Embedding API，消耗 API 用量）。构建完成后重启后端服务生效。

---

## 二、账户与权限

### 注册与登录

访问 `http://localhost:5173/register` 注册新用户，或访问 `/login` 登录。

默认测试账户（通过 `seed.py` 初始化）：

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 管理员 |
| testuser | test123 | 普通用户 |

> 实际密码以 `seed.py` 中定义为准。

### 管理员功能

管理员登录后访问 `/admin` 或在首页导航中点击"管理后台"，可进行：
- 用户管理（查看、禁用、重置密码）
- 健康知识库管理（增删改查结构化知识条目）
- RAG 向量索引管理与搜索测试

---

## 三、智能问诊使用指南

### 选择科室

首先访问 `/consultation`（科室选择页），根据问题类型选择对应科室：

- **全科门诊**：综合健康问题、健康数据查询与分析
- **心血管科**：血压、心率、心脏相关问题
- **内分泌科**：血糖、糖尿病、甲状腺、代谢问题
- **皮肤科**：皮肤问题，支持上传图片

### 对话技巧

Agent 会根据对话内容**自动决定是否调用工具**，无需特殊指令。以下是常见场景示例：

**查询健康数据**
> "帮我看看我最近的血压情况"  
> → Agent 自动调用 `get_health_metrics` 和 `get_health_trend`

**录入数据**
> "我今天测了血压，收缩压 125，帮我记录一下"  
> → Agent 会先确认数值，再调用 `add_health_metric`

**风险评估**
> "帮我评估一下我的心血管风险"  
> → Agent 调用 `run_risk_assessment`，基于健康档案运行 Framingham 模型

**知识问答**
> "高血压平时应该注意什么饮食？"  
> → Agent 调用 `get_health_knowledge` 检索《默克家庭诊疗手册》

**体检报告解读**
> "帮我解读一下我最近的体检报告"  
> → Agent 调用 `analyze_exam_report` 获取已解析的体检数据

**皮肤科图片分析**
> 点击图片上传按钮，发送皮肤图片  
> → 后端自动调用 Qwen2.5-VL 分析后注入对话上下文

### 会话管理

- 左侧边栏显示历史会话列表，点击可切换
- 点击会话标题旁的编辑图标可重命名
- 点击垃圾桶图标可删除会话（不可恢复）
- 新建会话点击左上角"+"按钮

---

## 四、健康档案填写指南

完善的健康档案是风险评估准确性的基础。访问 `/profile` 填写：

### 基本信息
- 姓名、性别、年龄、身高、体重（BMI 自动计算）

### 关键医学指标（用于风险评估）

| 指标 | 用于模型 | 单位 |
|------|---------|------|
| 总胆固醇 | Framingham 心血管 | mg/dL |
| HDL 胆固醇 | Framingham 心血管 | mg/dL |
| LDL 胆固醇 | 通用参考 | mg/dL |
| 甘油三酯 | 代谢综合征 | mg/dL |
| 空腹血糖 | FINDRISC + 代谢综合征 | mmol/L |
| 糖化血红蛋白（HbA1c） | 糖尿病管理参考 | % |
| 收缩压 / 舒张压 | Framingham + 代谢综合征 | mmHg |
| 腰围 | FINDRISC + 代谢综合征 | cm |

### 生活习惯与病史
- 吸烟情况、运动频率、饮食习惯
- 既往病史（糖尿病/高血压/心脏病）
- 家族史（糖尿病/心脏病/高血压）

> 提示：未填写的字段会使用默认值参与评估，但准确性会降低，评估结果中会明确标注。

---

## 五、体检报告上传指南

1. 访问 `/exam-report`，点击"上传报告"
2. 选择 **PDF 或图片格式**（JPG/PNG）的体检报告
3. 系统自动进行 OCR 提取（DeepSeek-OCR）+ 结构化解析（GLM-4.7）
4. 解析完成后（状态变为"已完成"），可查看提取的各项指标
5. 进入智能问诊，对 Agent 说"帮我解读体检报告"，AI 将调用 `analyze_exam_report` 工具进行专业解读

---

## 六、用药管理使用指南

1. 访问 `/medication`，点击"添加用药"
2. **方式一（推荐）**：拍摄/上传药品说明书图片，系统自动识别用药信息
3. **方式二**：手动填写药品名称、用法用量、提醒时间
4. 确认信息后保存，即可在用药列表中查看管理

---

## 七、常见问题（FAQ）

### Q1：后端启动时提示"未配置 LLM_API_KEY，智能问诊功能不可用"

**原因**：`backend/.env` 文件中 `LLM_API_KEY` 为空。  
**解决**：填写有效的硅基流动 API Key，重启后端。

---

### Q2：智能问诊报错"服务暂时不可用，请稍后重试"

**可能原因**：
- API Key 额度不足或已过期
- 硅基流动 API 服务临时故障
- 网络连接问题

**排查**：查看后端终端日志，通常会有具体的 API 报错信息。

---

### Q3：体检报告上传后状态一直是"处理中"

**可能原因**：OCR/解析过程中 API 调用失败。  
**解决**：查看后端日志中 `exam_service` 相关错误。常见原因是 API Key 无效或图片格式不支持。

---

### Q4：风险评估结果提示"部分数据使用默认值"

**原因**：健康档案中某些关键字段未填写，评估使用了默认值。  
**解决**：前往 `/profile` → "健康档案"页面，补充对应指标数据后重新评估。

---

### Q5：RAG 知识库未构建，get_health_knowledge 工具没有返回《默克手册》内容

**原因**：`backend/rag_data/chroma_db/` 目录不存在或为空，RAG 索引未构建。  
**解决**：
```bash
source .venv/bin/activate
python backend/rag_data/build_index.py
```
构建完成后重启后端。构建时会消耗 Embedding API 用量。

---

### Q6：前端显示 CORS 错误

**原因**：前端请求地址与后端实际地址不匹配。  
**检查**：`frontend/src/api/index.js` 中 `API_BASE = 'http://127.0.0.1:5000/api'`，确认后端运行在 `127.0.0.1:5000`（不是 `localhost:5000`，两者在某些浏览器下视为不同 Origin）。

---

### Q7：皮肤科图片分析功能无响应

**原因**：VL 模型调用失败（API 错误或超时）。  
**注意**：Qwen2.5-VL-72B 为大型模型，调用耗时通常在 10–30 秒，属正常现象。查看后端日志中 `vl_service` 相关错误。

---

### Q8：如何重置数据库

```bash
# 删除现有数据库（所有数据会丢失）
rm backend/database/healthai.db

# 重启后端，数据库会自动重建
python backend/app.py

# 可选：重新填充测试数据
python backend/database/seed.py
```

---

### Q9：如何新增健康知识条目

**通过管理后台**（推荐）：
1. 用管理员账户登录
2. 访问 `/admin` → "知识库管理"
3. 点击"新增知识"，填写分类、标题、关键词、内容

**通过 API**（开发用）：
```bash
curl -X POST http://127.0.0.1:5000/api/admin/knowledge \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin_token>" \
  -d '{
    "category": "disease",
    "subcategory": "cardiovascular",
    "title": "高血压",
    "keywords": "高血压,血压,降压",
    "content": "..."
  }'
```

---

### Q10：如何查看 Agent 的详细调用日志

后端在 INFO 级别记录每次工具调用：

```
INFO: 🔧 Agent 调用工具: get_health_metrics({})
DEBUG:    工具结果: {"metrics": [...]}
```

如需 DEBUG 级别详情，在 `backend/app.py` 中将 `logging.INFO` 改为 `logging.DEBUG`。

---

## 八、API 接口速查

### 基础信息

- **Base URL**：`http://127.0.0.1:5000/api`
- **认证方式**：`Authorization: Bearer <JWT Token>`
- **响应格式**：`{ "success": true/false, "data": {...} / "error": "..." }`

### 认证接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/auth/login` | 登录，返回 token |
| POST | `/auth/register` | 注册新用户 |
| POST | `/auth/logout` | 登出 |
| POST | `/auth/change-password` | 修改密码 |

### 用户接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/user` | 获取当前用户信息 |
| PUT | `/user` | 更新用户基本信息 |
| GET | `/user/stats` | 获取用户统计数据 |
| GET | `/user/tags` | 获取健康标签列表 |
| GET/PUT | `/user/health-profile` | 健康档案读写 |

### 健康数据接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/metrics` | 获取最新健康指标 |
| POST | `/metrics/add` | 录入新健康指标 |
| GET | `/metrics/trend` | 获取趋势数据 |
| GET | `/records` | 获取健康记录列表 |
| GET | `/dashboard` | 获取首页仪表盘数据 |

### 智能问诊接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/consultation/departments` | 获取科室列表 |
| POST | `/consultation/start` | 创建新会话 |
| POST | `/consultation/message/stream` | 流式发送消息（SSE） |
| GET | `/consultation/history` | 获取历史会话列表 |
| GET | `/consultation/<session_id>` | 获取会话详情 |
| PATCH | `/consultation/<session_id>` | 重命名会话 |
| DELETE | `/consultation/<session_id>` | 删除会话 |

### 风险评估接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/risk/assessments` | 获取评估历史 |
| POST | `/risk/assess` | 运行新评估（cardiovascular/diabetes/metabolic/osteoporosis） |

### 体检报告接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/exam/reports` | 获取报告列表 |
| POST | `/exam/reports/upload` | 上传并解析报告（multipart/form-data） |
| GET | `/exam/reports/<id>` | 获取单份报告详情 |
| DELETE | `/exam/reports/<id>` | 删除报告 |

### 用药管理接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/medications/extract` | VL 识别说明书图片（不入库） |
| GET | `/medications` | 获取用药列表 |
| POST | `/medications` | 保存用药记录 |
| PUT | `/medications/<id>` | 更新用药记录 |
| DELETE | `/medications/<id>` | 删除用药记录 |

### 管理员接口

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/admin/stats` | 系统统计数据 |
| GET | `/admin/users` | 用户列表 |
| POST | `/admin/users/<id>/toggle` | 启用/禁用账户 |
| POST | `/admin/users/<id>/reset-password` | 重置密码 |
| GET/POST | `/admin/knowledge` | 知识库列表/新增 |
| GET/PUT/DELETE | `/admin/knowledge/<id>` | 知识条目操作 |
| GET | `/admin/rag/stats` | RAG 索引统计 |
| GET | `/admin/rag/chunks` | 分页查看向量块 |
| POST | `/admin/rag/search` | RAG 语义搜索测试 |

---

## 九、项目依赖版本

### 后端（`backend/requirements.txt`）

```
flask==3.0.0
flask-cors==4.0.0
sqlalchemy==2.0.23
requests==2.31.0
python-dotenv==1.0.0
PyJWT==2.10.1
openai>=1.0.0
httpx>=0.27.0
chromadb>=1.0.0
pymupdf>=1.24.0
```

### 前端（`frontend/package.json`）

```json
{
  "dependencies": {
    "vue": "^3.x",
    "vue-router": "^4.x",
    "lucide-vue-next": "...",
    "marked": "..."
  },
  "devDependencies": {
    "vite": "^5.x",
    "@vitejs/plugin-vue": "..."
  }
}
```
