# HealthAI 全面审查报告

## 🔴 严重 Bug（会导致功能崩溃）

### B1. medication.py `image_path` 未定义变量
- **文件**: `backend/routes/medication.py:104`
- **问题**: `create_medication()` 中引用 `image_path` 变量，但该变量在移除图片存储后已不存在
- **影响**: 创建用药记录时 500 错误，整个保存功能不可用
- **修复**: 改为 `image_path=None`

### B2. Settings.vue 使用不存在的 api 方法
- **文件**: `frontend/src/views/Settings.vue:21,36,68`
- **问题**: `api.get('/user')`, `api.put('/user')`, `api.post('/auth/change-password')` 在 api/index.js 中不存在
- **影响**: 设置页面无法加载用户信息、无法保存修改、无法修改密码
- **修复**: 替换为 `api.getUser()`, `api.updateUser()`, `api.changePassword()`（需新增 changePassword 方法）

### B3. Header.vue 搜索区域使用不存在的 api 方法
- **文件**: `frontend/src/components/layout/Header.vue:33-34`
- **问题**: `api.get('/user/reports')`, `api.get('/exam/reports?limit=20')` 不存在
- **影响**: 全局搜索中无法加载报告和体检数据
- **修复**: 替换为 `api.getUserReports()`, `api.getExamReports(20)`

### B4. Header.vue 搜索结果字段名不匹配
- **文件**: `frontend/src/components/layout/Header.vue:36,43`
- **问题**: `rRes.data.reports` 实际应为 `rRes.data`（api request 已解包）；`eRes.data.reports` 同理
- **影响**: 搜索结果中报告和体检数据永远为空
- **修复**: 修正字段路径

### B5. database/__init__.py 缺少 Medication 模型导出
- **文件**: `backend/database/__init__.py`
- **问题**: `Medication` 模型未在 `__init__.py` 中导出
- **影响**: 其他模块无法通过 `from database import Medication` 导入（目前 medication.py 直接从 models 导入绕过了此问题，但不一致）
- **修复**: 添加 Medication 到导出列表

## 🟡 安全问题

### S1. JWT Secret 硬编码
- **文件**: `backend/utils/jwt_utils.py:13`
- **问题**: `JWT_SECRET = 'healthai-mvp-secret-key-2024'` 硬编码，未强制要求环境变量
- **影响**: 生产部署若忘记设置环境变量，所有 token 可被伪造
- **修复**: 添加启动时检查，开发环境警告

### S2. 备用明文账户
- **文件**: `backend/services/auth_service.py:18-22`
- **问题**: `FALLBACK_USERS` 含明文密码 admin/123456
- **影响**: 当前代码实际未使用这些备用账户（login 方法只查 DB），但留着有误导风险
- **修复**: 删除 FALLBACK_USERS

### S3. 明文密码兼容逻辑
- **文件**: `backend/services/auth_service.py:220-224`
- **问题**: `_verify_password` 在非哈希格式时直接明文比较
- **影响**: 旧迁移期数据安全隐患
- **修复**: 添加日志警告，长期应迁移所有密码为哈希格式

### S4. CORS 允许所有来源
- **文件**: `backend/app.py:33`
- **问题**: `Access-Control-Allow-Origin: *` 允许任何域名跨域请求
- **影响**: 开发环境可接受，生产环境需要限制为前端域名
- **修复**: 开发环境保持，生产环境改为具体域名（当前为毕业设计项目，暂可保留）

## 🟢 逻辑/一致性问题

### L1. logout 不实际失效
- **文件**: `backend/routes/auth.py:76-79`
- **问题**: logout 只返回成功，JWT 无服务端黑名单
- **影响**: token 在过期前仍有效（JWT 特性，需权衡）
- **备注**: 对于毕设项目可接受，前端 clearToken() 已删除本地 token

### L2. getMetrics 返回结构与 Header 字段不一致
- **文件**: `backend/routes/health.py:24` vs `Header.vue:154`
- **问题**: 路由返回 `{success, data: metrics}`，api 解包后为 `{success, data}`，Header 读 `metricsRes.metrics` — 实际应为 `metricsRes.data`
- **修复**: Header.vue 中将 `metricsRes.metrics` 改为 `metricsRes.data`

### L3. api/index.js 缺少 changePassword 方法
- **文件**: `frontend/src/api/index.js`
- **问题**: Settings.vue 需要调用修改密码 API，但 api 对象中没有该方法
- **修复**: 添加 `changePassword` 方法
