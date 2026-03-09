<script setup>
import { useRouter } from 'vue-router'
import { onMounted } from 'vue'
import {
  Heart,
  MessageCircle,
  Activity,
  ShieldCheck,
  ClipboardList,
  BookOpen,
  Brain,
  ArrowRight,
  Sparkles,
  ChevronRight
} from 'lucide-vue-next'

const router = useRouter()

const features = [
  {
    icon: MessageCircle,
    title: '智能健康问诊',
    desc: '基于 AI Agent 的智能对话，自主调用工具链分析您的健康数据，提供个性化建议',
    color: '#0866FF'
  },
  {
    icon: ShieldCheck,
    title: '疾病风险预测',
    desc: '集成 Framingham、FINDRISC、FRAX® 等国际权威医学模型，科学评估健康风险',
    color: '#31A24C'
  },
  {
    icon: Activity,
    title: '健康趋势分析',
    desc: '智能追踪血压、血糖、心率等关键指标，异常检测与趋势预测一目了然',
    color: '#F7B928'
  },
  {
    icon: ClipboardList,
    title: '体检报告解读',
    desc: '上传体检报告，AI 自动 OCR 识别并结构化解析，快速理解检查结果',
    color: '#FA383E'
  },
  {
    icon: BookOpen,
    title: 'RAG 健康知识库',
    desc: '基于《默克家庭诊疗手册》构建的专业知识库，检索增强问答更准确',
    color: '#8B5CF6'
  },
  {
    icon: Brain,
    title: '智能健康档案',
    desc: '完整的个人健康档案管理，AI 自动评估生成健康标签，全方位了解自身状况',
    color: '#00C6FF'
  }
]

const highlights = [
  { number: '4', label: '权威医学模型', suffix: '个' },
  { number: '7', label: 'Agent 工具', suffix: '个' },
  { number: '360', label: '知识库文本块', suffix: '+' },
  { number: '10', label: '年风险预测', suffix: '年' }
]

function scrollTo(id) {
  const el = document.getElementById(id)
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

onMounted(() => {
  const reveals = document.querySelectorAll('.reveal')
  const io = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('visible')
        io.unobserve(e.target)
      }
    })
  }, { threshold: 0.12 })
  reveals.forEach(el => io.observe(el))
})
</script>

<template>
  <div class="landing">
    <!-- Navigation -->
    <header class="landing-nav">
      <div class="nav-inner">
        <div class="nav-left">
          <div class="nav-brand" @click="router.push('/landing')">
            <div class="brand-icon">
              <Heart :size="20" />
            </div>
            <span class="brand-text">HealthAI</span>
          </div>
        </div>
        <nav class="nav-links">
          <a @click.prevent="scrollTo('features')" href="#features">功能</a>
          <a @click.prevent="scrollTo('tech')" href="#tech">技术</a>
          <a @click.prevent="scrollTo('about')" href="#about">关于</a>
        </nav>
        <div class="nav-actions">
          <a class="nav-btn-github" href="https://github.com/DabRlin/health-agent" target="_blank" rel="noopener noreferrer" title="GitHub">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0C5.374 0 0 5.373 0 12c0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0 1 12 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z"/>
            </svg>
          </a>
          <button class="nav-btn-primary" @click="router.push('/register')">
            开始使用
            <ArrowRight :size="16" />
          </button>
        </div>
      </div>
    </header>

    <!-- Hero Section -->
    <section class="hero">
      <div class="hero-bg">
        <div class="blob blob-1"></div>
        <div class="blob blob-2"></div>
        <div class="blob blob-3"></div>
      </div>

      <div class="hero-inner">
        <div class="hero-badge anim-up anim-d1">
          <Sparkles :size="14" />
          <span>AI 驱动的个人健康管理</span>
        </div>
        <h1 class="hero-title anim-up anim-d2">
          您的健康，<span class="hero-highlight">智能守护</span><br />
          每一天
        </h1>
        <p class="hero-desc anim-up anim-d3">
          融合大语言模型 Agent、权威医学评估模型与 RAG 知识库，<br class="hide-mobile" />
          为您提供科学、专业、个性化的健康管理体验
        </p>
        <div class="hero-actions anim-up anim-d4">
          <button class="hero-btn-primary" @click="router.push('/register')">
            免费开始
            <ArrowRight :size="18" />
          </button>
          <button class="hero-btn-secondary" @click="router.push('/login')">
            已有账号，立即登录 →
          </button>
        </div>

        <!-- Hero Chat Visual -->
        <div class="hero-visual anim-up anim-d5">
          <div class="chat-card">
            <div class="chat-header">
              <div class="chat-avatar">
                <Heart :size="18" />
              </div>
              <div>
                <div class="chat-name">HealthAI</div>
                <div class="chat-status">在线</div>
              </div>
            </div>
            <div class="msg msg-user">
              <div class="msg-bubble user-bubble">我最近血压有点高，需要注意什么？</div>
            </div>
            <div class="msg msg-ai">
              <div class="msg-bubble ai-bubble">
                根据您近 30 天的血压数据，收缩压均值 138mmHg，略高于正常范围。建议您：<br />
                ① 减少盐分摄入，每日不超过 5g<br />
                ② 保持每天 30 分钟有氧运动<br />
                ③ 若持续偏高，建议就医检查
              </div>
            </div>
            <div class="msg msg-ai">
              <div class="typing-indicator">
                <span></span><span></span><span></span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Highlights -->
    <section class="highlights reveal">
      <div class="highlights-inner">
        <div class="highlight-item" v-for="h in highlights" :key="h.label">
          <div class="highlight-number">{{ h.number }}<span class="highlight-suffix">{{ h.suffix }}</span></div>
          <div class="highlight-label">{{ h.label }}</div>
        </div>
      </div>
    </section>

    <!-- Features -->
    <section class="features" id="features">
      <div class="features-inner">
        <div class="section-header reveal">
          <div class="section-label">核心功能</div>
          <h2 class="section-title">让 AI 成为您的<span class="text-gradient">健康伙伴</span></h2>
        </div>
        <div class="features-grid">
          <div class="feature-card reveal" v-for="f in features" :key="f.title">
            <div class="feature-icon" :style="{ background: f.color + '12', color: f.color }">
              <component :is="f.icon" :size="24" />
            </div>
            <h3 class="feature-title">{{ f.title }}</h3>
            <p class="feature-desc">{{ f.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Tech Stack -->
    <section class="tech-section" id="tech">
      <div class="tech-inner">
        <div class="section-header reveal">
          <div class="section-label">技术架构</div>
          <h2 class="section-title">基于前沿 AI 技术，<span class="text-gradient">科学可信</span></h2>
        </div>
        <div class="tech-grid">
          <div class="tech-card reveal">
            <div class="tech-tag">AI Agent</div>
            <h3>ReAct 自主推理</h3>
            <p>自建 LLM Agent，基于 ReAct 循环自主决策调用工具链，支持流式输出与思考状态实时展示</p>
          </div>
          <div class="tech-card reveal">
            <div class="tech-tag">医学模型</div>
            <h3>权威评估体系</h3>
            <p>集成 Framingham、FINDRISC、FRAX® 等国际权威医学模型，基于循证医学的科学评估</p>
          </div>
          <div class="tech-card reveal">
            <div class="tech-tag">RAG</div>
            <h3>知识增强问答</h3>
            <p>基于《默克家庭诊疗手册》构建 RAG 系统，bge-m3 嵌入 + Reranker 精排，回答有据可查</p>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="cta" id="about">
      <div class="cta-inner reveal">
        <div class="section-label">立即体验</div>
        <h2 class="cta-title">健康管理，<span class="text-gradient">从今天开始</span></h2>
        <p class="cta-desc">注册即可免费体验全部功能，让 AI 成为您的私人健康顾问</p>
        <button class="cta-btn" @click="router.push('/register')">
          免费注册
          <ChevronRight :size="18" />
        </button>
      </div>
    </section>

    <!-- Footer -->
    <footer class="landing-footer">
      <div class="footer-inner">
        <div class="footer-brand">
          <Heart :size="16" />
          <span>HealthAI</span>
        </div>
        <p class="footer-disclaimer">本系统仅供健康参考和学术研究，不能替代专业医疗诊断</p>
        <p class="footer-copy">© 2025 HealthAI. All rights reserved.</p>
      </div>
    </footer>
  </div>
</template>

<style scoped>
/* ========== Global ========== */
.landing {
  min-height: 100vh;
  background: #ffffff;
}

.text-gradient {
  background: linear-gradient(135deg, #0866FF, #00C6FF);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

/* ========== Animations ========== */
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(24px); }
  to   { opacity: 1; transform: none; }
}
@keyframes fadeDown {
  from { opacity: 0; transform: translateY(-12px); }
  to   { opacity: 1; transform: none; }
}
@keyframes float {
  0%, 100% { transform: translateY(0) rotate(0deg); }
  50%      { transform: translateY(-24px) rotate(3deg); }
}
@keyframes blink {
  0%, 80%, 100% { transform: scale(1); opacity: 0.4; }
  40%           { transform: scale(1.3); opacity: 1; }
}

.anim-up { opacity: 0; animation: fadeUp 0.7s ease both; }
.anim-d1 { animation-delay: 0.1s; }
.anim-d2 { animation-delay: 0.2s; }
.anim-d3 { animation-delay: 0.3s; }
.anim-d4 { animation-delay: 0.4s; }
.anim-d5 { animation-delay: 0.5s; }

.reveal {
  opacity: 0;
  transform: translateY(28px);
  transition: opacity 0.65s ease, transform 0.65s ease;
}
.reveal.visible {
  opacity: 1;
  transform: none;
}

/* ========== Navigation ========== */
.landing-nav {
  position: fixed;
  top: 0; left: 0; right: 0;
  z-index: 100;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--color-border);
  animation: fadeDown 0.6s ease both;
}

.nav-inner {
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 80px;
  height: 60px;
  display: flex;
  align-items: center;
}

.nav-left {
  flex: 1;
  display: flex;
  align-items: center;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  cursor: pointer;
}

.brand-icon {
  width: 32px;
  height: 32px;
  background: linear-gradient(135deg, #0866FF, #00C6FF);
  border-radius: var(--radius-md);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.brand-text {
  font-size: var(--font-size-lg);
  font-weight: 700;
  color: var(--color-text-primary);
}

.nav-links {
  display: flex;
  gap: 36px;
  flex-shrink: 0;
}

.nav-links a {
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--color-text-secondary);
  text-decoration: none;
  transition: color 0.2s;
}

.nav-links a:hover {
  color: var(--color-text-primary);
}

.nav-actions {
  flex: 1;
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  justify-content: flex-end;
}

.nav-btn-github {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  background: none;
  border: 1px solid var(--color-border);
  color: var(--color-text-secondary);
  text-decoration: none;
  border-radius: var(--radius-full);
  transition: all 0.2s;
  flex-shrink: 0;
}

.nav-btn-github:hover {
  color: var(--color-text-primary);
  border-color: #BBB;
  background: var(--color-bg);
}

.nav-btn-ghost {
  padding: 8px 16px;
  background: none;
  border: none;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
  font-weight: 500;
  cursor: pointer;
  border-radius: var(--radius-md);
  transition: all 0.2s;
}

.nav-btn-ghost:hover {
  color: var(--color-text-primary);
  background: var(--color-bg);
}

.nav-btn-primary {
  padding: 8px 20px;
  background: var(--color-text-primary);
  color: white;
  border: none;
  font-size: var(--font-size-sm);
  font-weight: 500;
  cursor: pointer;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s;
}

.nav-btn-primary:hover {
  background: #333;
  transform: translateY(-1px);
}

/* ========== Hero ========== */
.hero {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 120px 40px 80px;
  text-align: center;
  position: relative;
  overflow: visible;
}

.hero::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 80% 60% at 50% -10%, rgba(8, 102, 255, 0.08) 0%, transparent 70%),
    radial-gradient(ellipse 40% 40% at 10% 80%, rgba(0, 198, 255, 0.1) 0%, transparent 60%),
    radial-gradient(ellipse 30% 30% at 90% 70%, rgba(8, 102, 255, 0.06) 0%, transparent 60%);
  pointer-events: none;
}

.hero-bg {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}

.blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.2;
  pointer-events: none;
  animation: float 8s ease-in-out infinite;
}
.blob-1 { width: 420px; height: 420px; background: #a8d4ff; top: -100px; left: -120px; animation-delay: 0s; }
.blob-2 { width: 280px; height: 280px; background: #c0e8ff; top: 40%; right: -60px; animation-delay: -3s; }
.blob-3 { width: 200px; height: 200px; background: #80c4ff; bottom: 60px; left: 20%; animation-delay: -5s; }

.hero-inner {
  width: 100%;
  margin: 0 auto;
  position: relative;
  z-index: 1;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  background: rgba(8, 102, 255, 0.06);
  border: 1px solid rgba(8, 102, 255, 0.12);
  border-radius: var(--radius-full);
  font-size: var(--font-size-sm);
  font-weight: 500;
  color: var(--color-primary);
  margin-bottom: 32px;
}

.hero-title {
  font-size: clamp(2.8rem, 8vw, 6.5rem);
  font-weight: 800;
  line-height: 1.15;
  color: var(--color-text-primary);
  letter-spacing: -2px;
  margin-bottom: var(--spacing-lg);
}

.hero-highlight {
  background: linear-gradient(135deg, #0866FF, #00C6FF);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-desc {
  font-size: 1.1rem;
  font-weight: 300;
  line-height: 1.75;
  color: var(--color-text-secondary);
  max-width: 600px;
  margin: 0 auto 44px;
}

.hero-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-md);
  margin-bottom: 72px;
}

.hero-btn-primary {
  padding: 14px 32px;
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: var(--radius-full);
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: all 0.2s;
  box-shadow: 0 4px 20px rgba(8, 102, 255, 0.2);
}

.hero-btn-primary:hover {
  background: var(--color-primary-hover);
  transform: translateY(-2px);
  box-shadow: 0 8px 28px rgba(8, 102, 255, 0.35);
}

.hero-btn-secondary {
  padding: 14px 28px;
  background: none;
  border: none;
  color: var(--color-text-primary);
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.hero-btn-secondary:hover {
  color: var(--color-primary);
}

/* ========== Chat Card ========== */
.hero-visual {
  max-width: 780px;
  margin: 0 auto;
}

.chat-card {
  background: white;
  border: 1px solid var(--color-border);
  border-radius: 20px;
  padding: 28px 32px;
  box-shadow: 0 20px 60px rgba(8, 102, 255, 0.06), 0 4px 16px rgba(0, 0, 0, 0.04);
  text-align: left;
}

.chat-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--color-border);
  margin-bottom: 20px;
}

.chat-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #0866FF, #00C6FF);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.chat-name {
  font-weight: 600;
  font-size: var(--font-size-sm);
  color: var(--color-text-primary);
}

.chat-status {
  font-size: var(--font-size-xs);
  color: var(--color-primary);
}
.chat-status::before {
  content: '● ';
}

.msg {
  margin-bottom: 14px;
  display: flex;
  gap: 10px;
}

.msg-user {
  flex-direction: row-reverse;
}

.msg-bubble {
  max-width: 75%;
  padding: 12px 16px;
  border-radius: 18px;
  font-size: var(--font-size-sm);
  line-height: 1.65;
}

.user-bubble {
  background: var(--color-primary);
  color: white;
  border-bottom-right-radius: 4px;
}

.ai-bubble {
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  color: var(--color-text-primary);
  border-bottom-left-radius: 4px;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  align-items: center;
  padding: 12px 16px;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 18px;
  border-bottom-left-radius: 4px;
  width: fit-content;
}

.typing-indicator span {
  width: 6px;
  height: 6px;
  background: var(--color-text-tertiary);
  border-radius: 50%;
  animation: blink 1.4s ease-in-out infinite;
}
.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

/* ========== Highlights ========== */
.highlights {
  padding: 56px 80px;
  border-top: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg);
}

.highlights-inner {
  max-width: 1440px;
  margin: 0 auto;
  display: flex;
  justify-content: center;
  gap: 100px;
}

.highlight-item {
  text-align: center;
}

.highlight-number {
  font-size: 3rem;
  font-weight: 800;
  color: var(--color-text-primary);
  line-height: 1;
  letter-spacing: -1px;
}

.highlight-suffix {
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--color-primary);
  margin-left: 2px;
}

.highlight-label {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
  margin-top: 8px;
  font-weight: 500;
}

/* ========== Section Common ========== */
.section-header {
  text-align: center;
  margin-bottom: 56px;
}

.section-label {
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  color: var(--color-primary);
  text-transform: uppercase;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.section-label::before,
.section-label::after {
  content: '';
  display: inline-block;
  width: 24px;
  height: 1px;
  background: var(--color-primary);
  opacity: 0.4;
}

.section-title {
  font-size: clamp(2rem, 3.8vw, 3rem);
  font-weight: 700;
  color: var(--color-text-primary);
  line-height: 1.2;
  letter-spacing: -0.5px;
}

/* ========== Features ========== */
.features {
  padding: 100px 80px;
}

.features-inner {
  max-width: 1440px;
  margin: 0 auto;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-lg);
}

.feature-card {
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 16px;
  padding: var(--spacing-xl) var(--spacing-lg);
  transition: transform 0.2s, box-shadow 0.2s;
  position: relative;
  overflow: hidden;
}

.feature-card::after {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  background: linear-gradient(90deg, #0866FF, #00C6FF);
  opacity: 0;
  transition: opacity 0.2s;
}

.feature-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 36px rgba(8, 102, 255, 0.08);
}

.feature-card:hover::after {
  opacity: 1;
}

.feature-icon {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: var(--spacing-md);
}

.feature-title {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: var(--spacing-sm);
  color: var(--color-text-primary);
  letter-spacing: -0.2px;
}

.feature-desc {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
  line-height: 1.75;
}

/* ========== Tech Section ========== */
.tech-section {
  padding: 100px 80px;
  background: white;
}

.tech-inner {
  max-width: 1440px;
  margin: 0 auto;
}

.tech-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--spacing-lg);
}

.tech-card {
  padding: var(--spacing-xl) var(--spacing-lg);
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: 16px;
  transition: all 0.2s;
  position: relative;
  overflow: hidden;
}

.tech-card::after {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  background: linear-gradient(90deg, #0866FF, #00C6FF);
  opacity: 0;
  transition: opacity 0.2s;
}

.tech-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 36px rgba(8, 102, 255, 0.08);
}

.tech-card:hover::after {
  opacity: 1;
}

.tech-tag {
  display: inline-block;
  padding: 4px 10px;
  background: rgba(8, 102, 255, 0.08);
  color: var(--color-primary);
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: 600;
  margin-bottom: var(--spacing-md);
}

.tech-card h3 {
  font-size: 1.15rem;
  font-weight: 600;
  margin-bottom: var(--spacing-sm);
  color: var(--color-text-primary);
  letter-spacing: -0.2px;
}

.tech-card p {
  font-size: 0.9rem;
  color: var(--color-text-secondary);
  line-height: 1.75;
}

/* ========== CTA ========== */
.cta {
  padding: 100px 80px;
  text-align: center;
  position: relative;
  overflow: hidden;
}

.cta::before {
  content: '';
  position: absolute;
  inset: 0;
  background: radial-gradient(ellipse 60% 80% at 50% 50%, rgba(8, 102, 255, 0.05), transparent 70%);
  pointer-events: none;
}

.cta-inner {
  max-width: 560px;
  margin: 0 auto;
  position: relative;
}

.cta-title {
  font-size: clamp(2rem, 3.8vw, 3rem);
  font-weight: 700;
  margin-bottom: var(--spacing-md);
  letter-spacing: -0.5px;
  line-height: 1.2;
}

.cta-desc {
  font-size: 1.1rem;
  color: var(--color-text-secondary);
  margin-bottom: 40px;
  line-height: 1.75;
}

.cta-btn {
  padding: 14px 32px;
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: var(--radius-full);
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
  box-shadow: 0 4px 20px rgba(8, 102, 255, 0.2);
}

.cta-btn:hover {
  background: var(--color-primary-hover);
  transform: translateY(-2px);
  box-shadow: 0 8px 28px rgba(8, 102, 255, 0.35);
}

/* ========== Footer ========== */
.landing-footer {
  padding: 32px 80px;
  border-top: 1px solid var(--color-border);
}

.footer-inner {
  max-width: 1440px;
  margin: 0 auto;
  text-align: center;
}

.footer-brand {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--color-text-tertiary);
  font-weight: 600;
  font-size: var(--font-size-sm);
  margin-bottom: var(--spacing-sm);
}

.footer-disclaimer {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
  margin-bottom: var(--spacing-xs);
}

.footer-copy {
  font-size: var(--font-size-xs);
  color: var(--color-text-tertiary);
}

/* ========== Responsive ========== */
@media (max-width: 1024px) {
  .nav-inner { padding: 0 40px; }
  .hero { padding: 120px 40px 80px; }
  .highlights { padding: 56px 40px; }
  .highlights-inner { gap: 60px; }
  .features, .tech-section, .cta { padding: 80px 40px; }
  .landing-footer { padding: 32px 40px; }
  .hero-title { font-size: clamp(2rem, 4vw, 3.6rem); }
}

@media (max-width: 768px) {
  .nav-inner { padding: 0 24px; }
  .nav-links { display: none; }
  .nav-left { flex: 0; }
  .hero { padding: 100px 24px 60px; }
  .hero-title { letter-spacing: 0; font-size: clamp(1.8rem, 6vw, 2.8rem); }
  .hero-actions { flex-direction: column; }
  .hide-mobile { display: none; }

  .highlights { padding: 48px 24px; }
  .highlights-inner { flex-direction: column; gap: 32px; }
  .highlight-number { font-size: 2rem; }

  .features, .tech-section, .cta { padding: 64px 24px; }
  .features-grid, .tech-grid { grid-template-columns: 1fr; }

  .chat-card { padding: 20px; }
  .landing-footer { padding: 32px 24px; }
}

@media (max-width: 480px) {
  .hero { padding: 90px 16px 40px; }
  .nav-btn-ghost { display: none; }
}
</style>
