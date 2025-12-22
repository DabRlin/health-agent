/**
 * HealthAI API Service
 */

// 直接请求后端
const API_BASE = 'http://127.0.0.1:5000/api'

/**
 * 获取存储的 Token
 */
function getToken() {
  return localStorage.getItem('token')
}

/**
 * 设置 Token
 */
export function setToken(token) {
  if (token) {
    localStorage.setItem('token', token)
  } else {
    localStorage.removeItem('token')
  }
}

/**
 * 清除 Token
 */
export function clearToken() {
  localStorage.removeItem('token')
}

/**
 * 通用请求方法
 */
async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`
  
  const token = getToken()
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    },
    ...options,
  }
  
  try {
    const response = await fetch(url, config)
    const data = await response.json()
    
    if (!response.ok) {
      // 如果是 401 错误，清除 token 并跳转到登录页
      if (response.status === 401) {
        clearToken()
        window.location.href = '/login'
      }
      throw new Error(data.error || '请求失败')
    }
    
    return data
  } catch (error) {
    console.error(`API Error [${endpoint}]:`, error)
    throw error
  }
}

/**
 * API 方法集合
 */
export const api = {
  // 健康检查
  healthCheck: () => request('/health'),
  
  // ========== 认证相关 ==========
  login: (username, password) => request('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  }),
  register: (username, password, name) => request('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ username, password, name }),
  }),
  logout: () => request('/auth/logout', {
    method: 'POST',
  }),
  
  // ========== 用户相关 ==========
  getUser: () => request('/user'),
  updateUser: (data) => request('/user', {
    method: 'PUT',
    body: JSON.stringify(data),
  }),
  getUserStats: () => request('/user/stats'),
  getUserTags: () => request('/user/tags'),
  getUserReports: () => request('/user/reports'),
  
  // ========== 健康数据 ==========
  getMetrics: () => request('/metrics'),
  getMetricsTrend: (days = 30, metric = 'all') => 
    request(`/metrics/trend?days=${days}&metric=${metric}`),
  getRecords: () => request('/records'),
  addRecord: (data) => request('/records', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  addMetric: (data) => request('/metrics/add', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  
  // ========== 风险评估 ==========
  getRiskAssessments: () => request('/risk/assessments'),
  createRiskAssessment: (type) => request('/risk/assess', {
    method: 'POST',
    body: JSON.stringify({ type }),
  }),
  
  // ========== 智能问诊 ==========
  startConsultation: () => request('/consultation/start', {
    method: 'POST',
  }),
  sendMessage: (conversationId, message) => request('/consultation/message', {
    method: 'POST',
    body: JSON.stringify({ conversation_id: conversationId, message }),
  }),
  // 流式发送消息
  sendMessageStream: async (conversationId, message, onChunk, onDone, onError) => {
    try {
      const token = getToken()
      const response = await fetch(`${API_BASE}/consultation/message/stream`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ conversation_id: conversationId, message }),
      })
      
      if (!response.ok) {
        throw new Error('请求失败')
      }
      
      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        
        const text = decoder.decode(value)
        const lines = text.split('\n')
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              if (data.type === 'chunk') {
                onChunk?.(data.content)
              } else if (data.type === 'done') {
                onDone?.()
              } else if (data.type === 'user_message') {
                // 用户消息确认，可忽略
              } else if (data.type === 'error') {
                onError?.(data.content)
              }
            } catch (e) {
              // 忽略解析错误
            }
          }
        }
      }
    } catch (error) {
      onError?.(error.message)
    }
  },
  getConsultationHistory: () => request('/consultation/history'),
  
  // ========== 首页仪表盘 ==========
  getDashboard: () => request('/dashboard'),
}

export default api
