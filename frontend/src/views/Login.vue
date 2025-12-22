<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Heart, User, Lock, RefreshCw, Loader2 } from 'lucide-vue-next'
import { api, setToken } from '@/api'

const router = useRouter()

// 表单数据
const form = ref({
  username: '',
  password: '',
  captcha: ''
})

// 状态
const loading = ref(false)
const error = ref('')
const captchaCode = ref('')
const captchaCanvas = ref(null)

// 生成随机验证码
const generateCaptcha = () => {
  const chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
  let code = ''
  for (let i = 0; i < 4; i++) {
    code += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  captchaCode.value = code
  drawCaptcha(code)
}

// 绘制验证码
const drawCaptcha = (code) => {
  const canvas = captchaCanvas.value
  if (!canvas) return
  
  const ctx = canvas.getContext('2d')
  const width = canvas.width
  const height = canvas.height
  
  // 清空画布
  ctx.fillStyle = '#f5f5f5'
  ctx.fillRect(0, 0, width, height)
  
  // 绘制干扰线
  for (let i = 0; i < 4; i++) {
    ctx.strokeStyle = `rgba(${Math.random() * 150}, ${Math.random() * 150}, ${Math.random() * 150}, 0.5)`
    ctx.beginPath()
    ctx.moveTo(Math.random() * width, Math.random() * height)
    ctx.lineTo(Math.random() * width, Math.random() * height)
    ctx.stroke()
  }
  
  // 绘制干扰点
  for (let i = 0; i < 30; i++) {
    ctx.fillStyle = `rgba(${Math.random() * 150}, ${Math.random() * 150}, ${Math.random() * 150}, 0.5)`
    ctx.beginPath()
    ctx.arc(Math.random() * width, Math.random() * height, 1, 0, 2 * Math.PI)
    ctx.fill()
  }
  
  // 绘制验证码文字
  const colors = ['#0866FF', '#FA383E', '#31A24C', '#F7B928']
  ctx.font = 'bold 28px Arial'
  ctx.textBaseline = 'middle'
  
  for (let i = 0; i < code.length; i++) {
    ctx.fillStyle = colors[i % colors.length]
    ctx.save()
    ctx.translate(20 + i * 28, height / 2)
    ctx.rotate((Math.random() - 0.5) * 0.4)
    ctx.fillText(code[i], 0, 0)
    ctx.restore()
  }
}

// 登录
const handleLogin = async () => {
  error.value = ''
  
  // 验证表单
  if (!form.value.username) {
    error.value = '请输入用户名'
    return
  }
  if (!form.value.password) {
    error.value = '请输入密码'
    return
  }
  if (!form.value.captcha) {
    error.value = '请输入验证码'
    return
  }
  if (form.value.captcha.toUpperCase() !== captchaCode.value) {
    error.value = '验证码错误'
    generateCaptcha()
    form.value.captcha = ''
    return
  }
  
  loading.value = true
  
  try {
    // 调用登录 API
    const data = await api.login(form.value.username, form.value.password)
    
    if (data.success) {
      // 保存 JWT Token
      setToken(data.data.token)
      // 保存用户信息
      localStorage.setItem('user', JSON.stringify(data.data.user))
      // 跳转首页
      router.push('/')
    } else {
      error.value = data.error || '登录失败'
      generateCaptcha()
      form.value.captcha = ''
    }
  } catch (err) {
    error.value = err.message || '网络错误，请稍后重试'
    generateCaptcha()
    form.value.captcha = ''
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  generateCaptcha()
})
</script>

<template>
  <div class="login-page">
    <div class="login-container">
      <!-- Logo 区域 -->
      <div class="login-header">
        <div class="logo">
          <Heart :size="32" />
        </div>
        <h1>HealthAI</h1>
        <p class="subtitle">智能健康管理系统</p>
      </div>
      
      <!-- 登录表单 -->
      <form class="login-form" @submit.prevent="handleLogin">
        <!-- 错误提示 -->
        <div v-if="error" class="error-message">
          {{ error }}
        </div>
        
        <!-- 用户名 -->
        <div class="form-group">
          <div class="input-wrapper">
            <User :size="18" class="input-icon" />
            <input 
              v-model="form.username"
              type="text"
              placeholder="用户名"
              autocomplete="username"
            />
          </div>
        </div>
        
        <!-- 密码 -->
        <div class="form-group">
          <div class="input-wrapper">
            <Lock :size="18" class="input-icon" />
            <input 
              v-model="form.password"
              type="password"
              placeholder="密码"
              autocomplete="current-password"
            />
          </div>
        </div>
        
        <!-- 验证码 -->
        <div class="form-group">
          <div class="captcha-row">
            <div class="input-wrapper captcha-input">
              <input 
                v-model="form.captcha"
                type="text"
                placeholder="验证码"
                maxlength="4"
              />
            </div>
            <div class="captcha-box" @click="generateCaptcha">
              <canvas ref="captchaCanvas" width="120" height="40"></canvas>
              <RefreshCw :size="14" class="refresh-icon" />
            </div>
          </div>
        </div>
        
        <!-- 登录按钮 -->
        <button type="submit" class="login-btn" :disabled="loading">
          <Loader2 v-if="loading" :size="18" class="spin" />
          <span v-else>登 录</span>
        </button>
        
        <!-- 注册链接 -->
        <div class="register-link">
          <span>还没有账号？</span>
          <router-link to="/register">立即注册</router-link>
        </div>
        
        <!-- 提示信息 -->
        <div class="login-tips">
          <p>演示账号: admin / 123456</p>
        </div>
      </form>
    </div>
    
    <!-- 底部版权 -->
    <div class="login-footer">
      <p>© 2024 HealthAI. All rights reserved.</p>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: var(--color-bg);
  padding: var(--spacing-lg);
}

.login-container {
  width: 100%;
  max-width: 400px;
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  padding: var(--spacing-xl);
}

/* Header */
.login-header {
  text-align: center;
  margin-bottom: var(--spacing-xl);
}

.logo {
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, #0866FF, #00C6FF);
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto var(--spacing-md);
  color: white;
}

.login-header h1 {
  font-size: var(--font-size-2xl);
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: var(--spacing-xs);
}

.subtitle {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}

/* Form */
.login-form {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.form-group {
  display: flex;
  flex-direction: column;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: var(--spacing-md);
  color: var(--color-text-tertiary);
  pointer-events: none;
}

.input-wrapper input {
  width: 100%;
  padding: var(--spacing-md) var(--spacing-md) var(--spacing-md) 44px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: var(--font-size-base);
  transition: all var(--transition-fast);
  background: var(--color-bg);
}

.input-wrapper input:focus {
  outline: none;
  border-color: var(--color-primary);
  background: white;
  box-shadow: 0 0 0 3px rgba(8, 102, 255, 0.1);
}

.input-wrapper input::placeholder {
  color: var(--color-text-tertiary);
}

/* Captcha */
.captcha-row {
  display: flex;
  gap: var(--spacing-sm);
}

.captcha-input {
  flex: 1;
}

.captcha-input input {
  padding-left: var(--spacing-md);
  text-transform: uppercase;
  letter-spacing: 4px;
  font-weight: 600;
}

.captcha-box {
  position: relative;
  cursor: pointer;
  border-radius: var(--radius-md);
  overflow: hidden;
  flex-shrink: 0;
}

.captcha-box canvas {
  display: block;
  border-radius: var(--radius-md);
}

.refresh-icon {
  position: absolute;
  right: 4px;
  bottom: 4px;
  color: var(--color-text-tertiary);
  background: rgba(255, 255, 255, 0.8);
  padding: 2px;
  border-radius: var(--radius-sm);
}

.captcha-box:hover .refresh-icon {
  color: var(--color-primary);
}

/* Error */
.error-message {
  padding: var(--spacing-sm) var(--spacing-md);
  background: #FEE2E2;
  color: #DC2626;
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  text-align: center;
}

/* Button */
.login-btn {
  width: 100%;
  padding: var(--spacing-md);
  background: linear-gradient(135deg, #0866FF, #00C6FF);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-size: var(--font-size-base);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-sm);
  margin-top: var(--spacing-sm);
}

.login-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(8, 102, 255, 0.4);
}

.login-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Register Link */
.register-link {
  text-align: center;
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-border);
  margin-top: var(--spacing-sm);
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.register-link a {
  color: var(--color-primary);
  margin-left: var(--spacing-xs);
  font-weight: 500;
  text-decoration: none;
}

.register-link a:hover {
  text-decoration: underline;
}

/* Tips */
.login-tips {
  text-align: center;
  padding-top: var(--spacing-sm);
}

.login-tips p {
  color: var(--color-text-tertiary);
  font-size: var(--font-size-sm);
}

/* Footer */
.login-footer {
  margin-top: var(--spacing-xl);
  color: var(--color-text-tertiary);
  font-size: var(--font-size-sm);
}

/* Responsive */
@media (max-width: 480px) {
  .login-container {
    padding: var(--spacing-lg);
  }
  
  .captcha-box canvas {
    width: 100px;
    height: 36px;
  }
}
</style>
