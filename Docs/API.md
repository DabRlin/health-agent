# HealthAI MVP API 文档

## 基础信息

- **Base URL**: `http://127.0.0.1:5000/api`
- **数据格式**: JSON
- **字符编码**: UTF-8

## 通用响应格式

### 成功响应
```json
{
  "success": true,
  "data": { ... }
}
```

### 错误响应
```json
{
  "success": false,
  "error": "错误信息"
}
```

---

## 接口列表

### 1. 健康检查

#### GET /health
检查 API 服务状态

**响应示例**:
```json
{
  "status": "ok",
  "message": "HealthAI API is running"
}
```

---

### 2. 用户相关

#### GET /user
获取当前用户信息

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "张三",
    "gender": "男",
    "age": 35,
    "birthday": "1989-05-15",
    "phone": "138****8888",
    "email": "zhang***@example.com",
    "location": "北京市朝阳区",
    "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=health",
    "health_score": 85,
    "health_days": 30,
    "created_at": "2024-01-01"
  }
}
```

#### GET /user/stats
获取用户健康统计

**响应示例**:
```json
{
  "success": true,
  "data": [
    {"label": "健康评分", "value": "85", "unit": "分", "icon": "Heart", "color": "#FA383E"},
    {"label": "体检次数", "value": "8", "unit": "次", "icon": "FileText", "color": "#0866FF"},
    {"label": "问诊记录", "value": "3", "unit": "次", "icon": "Activity", "color": "#31A24C"},
    {"label": "风险评估", "value": "3", "unit": "次", "icon": "Shield", "color": "#F7B928"}
  ]
}
```

#### GET /user/tags
获取用户健康标签

**响应示例**:
```json
{
  "success": true,
  "data": [
    {"name": "血压正常", "type": "positive"},
    {"name": "血糖偏高", "type": "warning"},
    {"name": "BMI正常", "type": "positive"}
  ]
}
```

#### GET /user/reports
获取用户健康报告列表

**响应示例**:
```json
{
  "success": true,
  "data": [
    {"id": 1, "name": "2024年度体检报告", "type": "体检报告", "date": "2024-01-15"},
    {"id": 2, "name": "心血管风险评估报告", "type": "风险评估", "date": "2024-01-10"}
  ]
}
```

---

### 3. 健康数据

#### GET /metrics
获取最新健康指标

**响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "心率",
      "value": 72,
      "unit": "bpm",
      "icon": "Heart",
      "color": "#FA383E",
      "status": "normal",
      "normal_range": "60-100",
      "trend": "stable"
    }
  ]
}
```

#### GET /metrics/trend
获取健康指标趋势数据

**查询参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| days | int | 30 | 查询天数 |
| metric | string | all | 指标类型 |

**响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "date": "2024-01-01",
      "heart_rate": 72,
      "systolic": 120,
      "diastolic": 80,
      "blood_sugar": 5.2
    }
  ]
}
```

#### POST /metrics/add
添加健康指标记录

**请求体**:
```json
{
  "type": "heart_rate",
  "value": 75
}
```

**指标类型**:
| type | 说明 | 单位 | 正常范围 |
|------|------|------|----------|
| heart_rate | 心率 | bpm | 60-100 |
| blood_pressure_sys | 收缩压 | mmHg | 90-140 |
| blood_pressure_dia | 舒张压 | mmHg | 60-90 |
| blood_sugar | 空腹血糖 | mmol/L | 3.9-6.1 |
| bmi | BMI | kg/m² | 18.5-24.9 |
| sleep | 睡眠时长 | 小时 | 7-9 |

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": 1234,
    "name": "心率",
    "value": 75,
    "unit": "bpm",
    "status": "normal",
    "recorded_at": "2024-01-15T10:30:00"
  }
}
```

#### GET /records
获取健康记录列表

**响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "date": "2024-01-15",
      "type": "体检报告",
      "source": "医院导入",
      "status": "已分析",
      "risk": "low"
    }
  ]
}
```

#### POST /records
添加健康记录

**请求体**:
```json
{
  "type": "日常监测",
  "source": "手动录入"
}
```

---

### 4. 风险评估

#### GET /risk/assessments
获取风险评估历史

**响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "type": "cardiovascular",
      "name": "心血管疾病风险",
      "date": "2024-01-10",
      "risk_level": "low",
      "score": 18,
      "factors": [
        {"name": "血压正常", "positive": true},
        {"name": "胆固醇偏高", "positive": false}
      ],
      "recommendations": [
        "继续保持健康的生活方式",
        "建议定期监测胆固醇水平"
      ]
    }
  ]
}
```

#### POST /risk/assess
创建新的风险评估

**请求体**:
```json
{
  "type": "cardiovascular"
}
```

**评估类型**:
| type | 说明 |
|------|------|
| cardiovascular | 心血管疾病风险 |
| diabetes | 糖尿病风险 |
| metabolic | 代谢综合征风险 |
| osteoporosis | 骨质疏松风险 |

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": 4,
    "type": "cardiovascular",
    "name": "心血管疾病风险",
    "date": "2024-01-15",
    "risk_level": "low",
    "score": 22,
    "factors": [...],
    "recommendations": [...]
  }
}
```

---

### 5. 智能问诊

#### POST /consultation/start
开始新的问诊会话

**响应示例**:
```json
{
  "success": true,
  "data": {
    "conversation_id": "conv_20240115103000_1234",
    "messages": [
      {
        "id": 1,
        "role": "assistant",
        "content": "您好！我是 HealthAI 智能健康助手...",
        "time": "10:30"
      }
    ]
  }
}
```

#### POST /consultation/message
发送问诊消息

**请求体**:
```json
{
  "conversation_id": "conv_20240115103000_1234",
  "message": "最近经常头痛"
}
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "user_message": {
      "id": 2,
      "role": "user",
      "content": "最近经常头痛",
      "time": "10:31"
    },
    "ai_message": {
      "id": 3,
      "role": "assistant",
      "content": "根据您描述的头痛症状...",
      "time": "10:31"
    }
  }
}
```

#### GET /consultation/history
获取问诊历史列表

**响应示例**:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "session_id": "conv_20240115_001",
      "date": "2024-01-15",
      "summary": "头痛症状咨询",
      "status": "已完成"
    }
  ]
}
```

#### GET /consultation/:session_id
获取问诊会话详情

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "session_id": "conv_20240115_001",
    "status": "已完成",
    "messages": [
      {"id": 1, "role": "assistant", "content": "...", "time": "10:30"},
      {"id": 2, "role": "user", "content": "...", "time": "10:31"}
    ]
  }
}
```

---

### 6. 首页数据

#### GET /dashboard
获取首页仪表盘数据

**响应示例**:
```json
{
  "success": true,
  "data": {
    "user": {
      "name": "张三",
      "health_score": 85,
      "health_days": 30
    },
    "metrics": [...],
    "recent_records": [...],
    "quick_actions": [
      {"title": "智能问诊", "desc": "描述症状，获取健康建议", "icon": "MessageCircle", "path": "/consultation", "color": "#0866FF"}
    ]
  }
}
```

---

## 错误码

| HTTP 状态码 | 说明 |
|-------------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

## 注意事项

1. 所有 POST 请求需要设置 `Content-Type: application/json`
2. 开发环境下 CORS 已开启，允许所有来源
3. 当前版本为 MVP，无需身份验证
