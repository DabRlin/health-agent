# HealthAI 全面审查报告

> 审查范围：全部后端路由/服务层/数据库模型 + 全部前端视图/组件/API 调用/路由守卫
> 审查时间：2026-03-13

## 🔴 严重 Bug（会导致功能崩溃） — 全部已修复 ✅

### B1. medication.py `image_path` 未定义变量 ✅
- **文件**: `backend/routes/medication.py:104`
- **问题**: `create_medication()` 中引用 `image_path` 变量，但该变量在移除图片存储后已不存在
- **影响**: 创建用药记录时 500 错误
- **修复**: 改为 `image_path=None`

### B2. Settings.vue 使用不存在的 api 方法 ✅
- **文件**: `frontend/src/views/Settings.vue:21,36,68`
- **问题**: `api.get('/user')`, `api.put('/user')`, `api.post('/auth/change-password')` 不存在
- **修复**: 替换为 `api.getUser()`, `api.updateUser()`, `api.changePassword()`

### B3. Header.vue 搜索区域使用不存在的 api 方法 ✅
- **文件**: `frontend/src/components/layout/Header.vue:33-34`
- **修复**: 替换为 `api.getUserReports()`, `api.getExamReports(20)`

### B4. Header.vue 搜索结果字段名不匹配 ✅
- **文件**: `frontend/src/components/layout/Header.vue:36,43`
- **问题**: `rRes.data.reports` → 应为 `rRes.data`
- **修复**: 修正字段路径

### B5. database/__init__.py 缺少 Medication 模型导出 ✅
- **修复**: 添加 Medication 到导出列表

### B6. Header.vue 通知区域 metrics 数据结构错误 ✅
- **问题**: `getMetrics()` 返回数组 `[{metric_type, name, value, ...}]`，但通知代码按字典 `metrics['heart_rate']` 访问
- **修复**: 重写为遍历数组，按 `metric_type` 匹配正常范围；后端 `health_service.py` 补充返回 `metric_type` 字段

### B7. Settings.vue 错误信息获取方式错误 ✅
- **文件**: `frontend/src/views/Settings.vue:75`
- **问题**: `e?.response?.data?.error` 是 axios 风格，但 `request()` 抛 `Error` 对象
- **修复**: 改为 `e?.message`

### B8. medication.py 写操作缺少 rollback ✅
- **文件**: `backend/routes/medication.py` create/update/delete
- **问题**: 只有 `try/finally`，异常时不 rollback
- **修复**: 三个写操作均添加 `except: db.rollback()` + 错误返回

### B9. 401 跳转地址与路由守卫不一致 ✅
- **文件**: `frontend/src/api/index.js:56`
- **问题**: `request()` 中 401 跳转 `/login`，但路由守卫未登录跳转 `/landing`
- **修复**: 统一为 `/landing`

### B10. Medication.vue 定时器内存泄漏 ✅
- **问题**: `reminderTimer` 缺少 `onUnmounted` 清理
- **修复**: 添加 `onUnmounted` 清理 `clearInterval`

### B11. Medication.vue 不必要发送 image_base64 ✅
- **问题**: `saveMedication` 将整个 base64 图片发给后端，但后端直接 pop 丢弃
- **修复**: payload 只发 `extractedData.value`，不含图片

## 🟡 安全问题

### S1. JWT Secret 硬编码（保留，毕设可接受）
- **文件**: `backend/utils/jwt_utils.py:13`
- **说明**: 默认值 `'healthai-mvp-secret-key-2024'`，生产需设 `JWT_SECRET` 环境变量

### S2. 备用明文账户 ✅ 已删除
- **修复**: 删除 `FALLBACK_USERS`

### S3. 明文密码兼容逻辑 ✅ 已添加警告
- **修复**: 添加 `logger.warning` 警告，提醒迁移

### S4. CORS 允许所有来源（保留，毕设可接受）
- **文件**: `backend/app.py:33`

## 🟢 逻辑/一致性问题（低优先级，已知可接受）

### L1. logout 不实际失效 token
- JWT 无状态特性，前端 `clearToken()` 已删除本地 token

### L2. Register.vue 多余的 localStorage 写入
- `localStorage.setItem('isLoggedIn', 'true')` 无人读取，路由守卫只检查 `token`
- 不影响功能，可后续清理

## ✅ 审查通过（无问题）的模块

- **后端路由**: auth.py, health.py, user.py, consultation.py, risk.py, exam.py, trend.py, admin.py, medical.py
- **后端服务**: auth_service.py, health_service.py, user_service.py, risk_service.py, exam_service.py, agent_service.py, vl_service.py, rag_service.py, trend_service.py, agent_tools.py, admin_service.py
- **后端 DB 会话管理**: 全部服务均使用 `try/finally: db.close()` 模式，无泄漏
- **前端视图**: Home.vue, HealthData.vue, RiskAssessment.vue, Consultation.vue, Profile.vue, ExamReport.vue, MedicalData.vue, Admin.vue, DepartmentSelect.vue, Login.vue, Register.vue, Landing.vue
- **前端路由守卫**: 正确区分 public/private/admin 路由
- **前端 API 调用**: 所有视图使用正确的具名 API 方法（修复后）
- **JWT 认证链**: login_required / admin_required / optional_login 装饰器实现正确
