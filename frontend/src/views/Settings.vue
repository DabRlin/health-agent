<script setup>
import { ref, reactive, onMounted } from 'vue'
import { User, Lock, Bell, Save, CheckCircle, Eye, EyeOff } from 'lucide-vue-next'
import api from '@/api'

// ==================== 个人信息 ====================
const saving = ref(false)
const saveSuccess = ref(false)

const userForm = reactive({
  name: '',
  gender: '',
  age: '',
  phone: '',
  email: '',
  location: '',
})

async function loadUser() {
  try {
    const res = await api.getUser()
    const d = res.data || {}
    userForm.name = d.name || ''
    userForm.gender = d.gender || ''
    userForm.age = d.age || ''
    userForm.phone = d.phone || ''
    userForm.email = d.email || ''
    userForm.location = d.location || ''
  } catch {}
}

async function saveUser() {
  saving.value = true
  saveSuccess.value = false
  try {
    await api.updateUser({ ...userForm, age: userForm.age ? Number(userForm.age) : undefined })
    saveSuccess.value = true
    setTimeout(() => (saveSuccess.value = false), 2500)
  } catch {}
  saving.value = false
}

// ==================== 修改密码 ====================
const pwdForm = reactive({ old_password: '', new_password: '', confirm: '' })
const pwdError = ref('')
const pwdSuccess = ref(false)
const showOld = ref(false)
const showNew = ref(false)
const pwdSaving = ref(false)

async function changePassword() {
  pwdError.value = ''
  pwdSuccess.value = false
  if (!pwdForm.old_password || !pwdForm.new_password) {
    pwdError.value = '请填写完整密码信息'
    return
  }
  if (pwdForm.new_password !== pwdForm.confirm) {
    pwdError.value = '两次新密码输入不一致'
    return
  }
  if (pwdForm.new_password.length < 6) {
    pwdError.value = '新密码至少 6 位'
    return
  }
  pwdSaving.value = true
  try {
    await api.changePassword(pwdForm.old_password, pwdForm.new_password)
    pwdSuccess.value = true
    pwdForm.old_password = ''
    pwdForm.new_password = ''
    pwdForm.confirm = ''
    setTimeout(() => (pwdSuccess.value = false), 2500)
  } catch (e) {
    pwdError.value = e?.message || '修改失败，请检查原密码是否正确'
  }
  pwdSaving.value = false
}

// ==================== 通知偏好 ====================
const NOTIF_KEY = 'healthai_notif_prefs'
function loadPrefs() {
  try { return JSON.parse(localStorage.getItem(NOTIF_KEY) || '{}') } catch { return {} }
}
const notifPrefs = reactive({
  metric_abnormal: true,
  risk_assessment: true,
  exam_done: true,
  med_reminder: true,
  system_notification: false,
  ...loadPrefs(),
})
function savePrefs() {
  localStorage.setItem(NOTIF_KEY, JSON.stringify({ ...notifPrefs }))
}

const sysNotifStatus = ref(Notification?.permission || 'default')
async function toggleSystemNotif() {
  if (notifPrefs.system_notification) {
    if (Notification?.permission !== 'granted') {
      const perm = await Notification.requestPermission()
      sysNotifStatus.value = perm
      if (perm !== 'granted') {
        notifPrefs.system_notification = false
      }
    }
  }
  savePrefs()
}

onMounted(loadUser)
</script>

<template>
  <div class="settings-page">
    <div class="settings-grid">

      <!-- 个人信息 -->
      <div class="card settings-card">
        <div class="card-header">
          <User :size="18" class="card-icon" />
          <h2 class="card-title">个人信息</h2>
        </div>
        <div class="form-grid">
          <div class="form-group">
            <label class="form-label">姓名</label>
            <input v-model="userForm.name" class="form-input" placeholder="请输入姓名" />
          </div>
          <div class="form-group">
            <label class="form-label">性别</label>
            <select v-model="userForm.gender" class="form-input">
              <option value="">请选择</option>
              <option value="male">男</option>
              <option value="female">女</option>
            </select>
          </div>
          <div class="form-group">
            <label class="form-label">年龄</label>
            <input v-model="userForm.age" type="number" class="form-input" placeholder="请输入年龄" min="1" max="120" />
          </div>
          <div class="form-group">
            <label class="form-label">手机号</label>
            <input v-model="userForm.phone" class="form-input" placeholder="请输入手机号" />
          </div>
          <div class="form-group">
            <label class="form-label">邮箱</label>
            <input v-model="userForm.email" type="email" class="form-input" placeholder="请输入邮箱" />
          </div>
          <div class="form-group">
            <label class="form-label">所在地</label>
            <input v-model="userForm.location" class="form-input" placeholder="城市/地区" />
          </div>
        </div>
        <div class="card-footer">
          <button class="btn btn-primary save-btn" @click="saveUser" :disabled="saving">
            <CheckCircle v-if="saveSuccess" :size="16" />
            <Save v-else :size="16" />
            {{ saveSuccess ? '已保存' : (saving ? '保存中...' : '保存修改') }}
          </button>
        </div>
      </div>

      <!-- 修改密码 -->
      <div class="card settings-card pwd-card">
        <div class="card-header">
          <Lock :size="18" class="card-icon" />
          <h2 class="card-title">修改密码</h2>
        </div>
        <div class="form-stack">
          <div class="form-group">
            <label class="form-label">当前密码</label>
            <div class="input-with-eye">
              <input
                v-model="pwdForm.old_password"
                :type="showOld ? 'text' : 'password'"
                class="form-input"
                placeholder="请输入当前密码"
              />
              <button class="eye-btn" @click="showOld = !showOld" type="button">
                <component :is="showOld ? EyeOff : Eye" :size="16" />
              </button>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">新密码</label>
            <div class="input-with-eye">
              <input
                v-model="pwdForm.new_password"
                :type="showNew ? 'text' : 'password'"
                class="form-input"
                placeholder="至少 6 位"
              />
              <button class="eye-btn" @click="showNew = !showNew" type="button">
                <component :is="showNew ? EyeOff : Eye" :size="16" />
              </button>
            </div>
          </div>
          <div class="form-group">
            <label class="form-label">确认新密码</label>
            <input v-model="pwdForm.confirm" type="password" class="form-input" placeholder="再次输入新密码" />
          </div>
          <p v-if="pwdError" class="form-error">{{ pwdError }}</p>
          <p v-if="pwdSuccess" class="form-success">密码修改成功</p>
        </div>
        <div class="card-footer">
          <button class="btn btn-primary save-btn" @click="changePassword" :disabled="pwdSaving">
            <CheckCircle v-if="pwdSuccess" :size="16" />
            <Lock v-else :size="16" />
            {{ pwdSuccess ? '修改成功' : (pwdSaving ? '提交中...' : '确认修改') }}
          </button>
        </div>
      </div>

      <div class="card settings-card notif-card">
        <div class="card-header">
          <Bell :size="18" class="card-icon" />
          <h2 class="card-title">通知偏好</h2>
        </div>
        <div class="toggle-list">
          <div class="toggle-item">
            <div class="toggle-info">
              <div class="toggle-title">健康指标异常提醒</div>
              <div class="toggle-desc">当心率、血压、血糖等指标超出正常范围时通知</div>
            </div>
            <label class="toggle-switch">
              <input type="checkbox" v-model="notifPrefs.metric_abnormal" @change="savePrefs" />
              <span class="toggle-slider"></span>
            </label>
          </div>
          <div class="toggle-item">
            <div class="toggle-info">
              <div class="toggle-title">风险评估结果通知</div>
              <div class="toggle-desc">收到新的心血管、糖尿病等风险评估结果时通知</div>
            </div>
            <label class="toggle-switch">
              <input type="checkbox" v-model="notifPrefs.risk_assessment" @change="savePrefs" />
              <span class="toggle-slider"></span>
            </label>
          </div>
          <div class="toggle-item">
            <div class="toggle-info">
              <div class="toggle-title">体检报告解析完成</div>
              <div class="toggle-desc">上传的体检报告 AI 解析完成时通知</div>
            </div>
            <label class="toggle-switch">
              <input type="checkbox" v-model="notifPrefs.exam_done" @change="savePrefs" />
              <span class="toggle-slider"></span>
            </label>
          </div>
          <div class="toggle-item">
            <div class="toggle-info">
              <div class="toggle-title">用药服药提醒</div>
              <div class="toggle-desc">设定的服药时间到点时，在铃铛面板显示提醒</div>
            </div>
            <label class="toggle-switch">
              <input type="checkbox" v-model="notifPrefs.med_reminder" @change="savePrefs" />
              <span class="toggle-slider"></span>
            </label>
          </div>
          <div class="toggle-item">
            <div class="toggle-info">
              <div class="toggle-title">系统通知（浏览器弹窗）</div>
              <div class="toggle-desc">
                开启后，所有提醒额外发送系统弹窗通知
                <span v-if="sysNotifStatus === 'denied'" class="notif-denied-tip">（浏览器已拒绝，请在浏览器设置中手动允许）</span>
              </div>
            </div>
            <label class="toggle-switch">
              <input type="checkbox" v-model="notifPrefs.system_notification" @change="toggleSystemNotif" :disabled="sysNotifStatus === 'denied'" />
              <span class="toggle-slider"></span>
            </label>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
.settings-page {
  width: 100%;
}

.settings-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-lg);
  align-items: stretch;
}

.settings-card {
  padding: var(--spacing-lg);
}

.notif-card {
  grid-column: 1 / -1;
}

.pwd-card {
  display: flex;
  flex-direction: column;
}

.pwd-card .form-stack {
  flex: 1;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: var(--spacing-lg);
  padding-bottom: var(--spacing-md);
  border-bottom: 1px solid var(--color-border);
}

.card-icon {
  color: var(--color-primary);
}

.card-title {
  font-size: var(--font-size-base);
  font-weight: 600;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-md);
}

.form-stack {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-md);
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--color-text-secondary);
}

.form-input {
  padding: 9px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  font-size: var(--font-size-sm);
  background: var(--color-bg);
  color: var(--color-text-primary);
  outline: none;
  transition: border-color var(--transition-fast);
  width: 100%;
}

.form-input:focus {
  border-color: var(--color-primary);
}

.input-with-eye {
  position: relative;
}

.input-with-eye .form-input {
  padding-right: 40px;
}

.eye-btn {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-text-tertiary);
  padding: 0;
  display: flex;
  align-items: center;
}

.form-error {
  font-size: var(--font-size-sm);
  color: #ef4444;
}

.form-success {
  font-size: var(--font-size-sm);
  color: #10b981;
}

.card-footer {
  margin-top: var(--spacing-lg);
  padding-top: var(--spacing-md);
  border-top: 1px solid var(--color-border);
}

.save-btn {
  display: flex;
  align-items: center;
  gap: 6px;
}

/* 通知切换 */
.toggle-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.toggle-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--spacing-md) 0;
  border-bottom: 1px solid var(--color-border);
}

.toggle-item:last-child {
  border-bottom: none;
}

.toggle-info {
  flex: 1;
  margin-right: var(--spacing-lg);
}

.toggle-title {
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--color-text-primary);
  margin-bottom: 3px;
}

.notif-denied-tip {
  color: #DC2626;
  font-size: 11px;
}

.toggle-desc {
  font-size: 12px;
  color: var(--color-text-tertiary);
  line-height: 1.4;
}

.toggle-switch {
  position: relative;
  display: inline-block;
  width: 44px;
  height: 24px;
  flex-shrink: 0;
  cursor: pointer;
}

.toggle-switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  inset: 0;
  background: var(--color-border);
  border-radius: 12px;
  transition: background var(--transition-fast);
}

.toggle-slider::before {
  content: '';
  position: absolute;
  width: 18px;
  height: 18px;
  left: 3px;
  top: 3px;
  background: white;
  border-radius: 50%;
  transition: transform var(--transition-fast);
}

.toggle-switch input:checked + .toggle-slider {
  background: var(--color-primary);
}

.toggle-switch input:checked + .toggle-slider::before {
  transform: translateX(20px);
}

@media (max-width: 768px) {
  .settings-grid {
    grid-template-columns: 1fr;
  }
  .notif-card {
    grid-column: 1;
  }
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
