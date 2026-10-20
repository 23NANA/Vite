<template>
  <div class="auth-page">
    <div class="auth-card">
      <!-- 左侧品牌区 -->
      <aside class="auth-brand">
        <div class="brand-top">
          <div class="brand-logo">
            <img :src="logo" alt="logo" />
          </div>
          <span class="brand-name">智能实验室预约系统</span>
        </div>

        <div class="brand-body">
          <h1 class="brand-title">{{ title }}</h1>
          <p class="brand-sub">{{ subtitle }}</p>
          <ul class="brand-points">
            <li v-for="point in points" :key="point.text">
              <span class="point-icon">
                <el-icon :size="15"><component :is="point.icon" /></el-icon>
              </span>
              {{ point.text }}
            </li>
          </ul>
        </div>

        <div class="brand-foot">Agent 驱动 · 让每一次预约更省心</div>
      </aside>

      <!-- 右侧表单区 -->
      <main class="auth-main">
        <div class="compact-brand">
          <img :src="logo" alt="logo" />
          <span>智能实验室预约系统</span>
        </div>

        <h2 class="form-title">{{ heading }}</h2>
        <p class="form-sub">{{ description }}</p>

        <slot />
      </main>
    </div>
  </div>
</template>

<script setup>
import logo from '@/assets/imgs/logo.png'
import { ChatDotRound, DocumentChecked, OfficeBuilding } from '@element-plus/icons-vue'

defineProps({
  // 品牌区大标题，用 \n 换行
  title: { type: String, default: '让每一次预约\n都更省心' },
  subtitle: { type: String, default: '基于 Agent 的智能实验室预约系统' },
  heading: { type: String, default: '欢迎回来' },
  description: { type: String, default: '登录后即可浏览实验室、预约设备' },
  points: {
    type: Array,
    default: () => [
      { icon: OfficeBuilding, text: '实验室 / 设备在线浏览与预约' },
      { icon: ChatDotRound, text: 'AI 助手对话式完成预约' },
      { icon: DocumentChecked, text: '审核进度实时可见' }
    ]
  }
})
</script>

<style scoped>
.auth-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 24px;
  background:
    radial-gradient(circle at 12% 18%, rgba(79, 125, 251, 0.14), transparent 45%),
    radial-gradient(circle at 88% 82%, rgba(155, 107, 242, 0.14), transparent 45%), #f4f6fb;
}

.auth-card {
  display: grid;
  grid-template-columns: 1.05fr 1fr;
  width: 100%;
  max-width: 940px;
  min-height: 540px;
  overflow: hidden;
  background: #fff;
  border-radius: 20px;
  box-shadow:
    0 26px 60px -30px rgba(40, 50, 120, 0.45),
    0 0 0 1px rgba(255, 255, 255, 0.6) inset;
}

/* ---------- 左侧品牌区 ---------- */
.auth-brand {
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 36px 38px;
  color: #fff;
  background: linear-gradient(150deg, #4f7dfb 0%, #6b5cf6 52%, #9b6bf2 100%);
}

/* 装饰光斑 */
.auth-brand::before,
.auth-brand::after {
  content: '';
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
}

.auth-brand::before {
  width: 320px;
  height: 320px;
  top: -140px;
  right: -110px;
  background: rgba(255, 255, 255, 0.14);
}

.auth-brand::after {
  width: 220px;
  height: 220px;
  bottom: -120px;
  left: -70px;
  background: rgba(255, 255, 255, 0.1);
}

.brand-top {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
}

.brand-logo {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 11px;
  background: rgba(255, 255, 255, 0.92);
}

.brand-logo img {
  width: 30px;
  height: 30px;
  object-fit: contain;
}

.brand-name {
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.brand-body {
  position: relative;
  margin: 34px 0;
}

.brand-title {
  margin: 0;
  font-size: 30px;
  font-weight: 700;
  line-height: 1.45;
  letter-spacing: 1px;
  white-space: pre-line;
}

.brand-sub {
  margin-top: 14px;
  font-size: 14px;
  line-height: 1.7;
  color: rgba(255, 255, 255, 0.85);
}

.brand-points {
  margin-top: 30px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.brand-points li {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13.5px;
  color: rgba(255, 255, 255, 0.92);
}

.point-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  flex-shrink: 0;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.2);
}

.brand-foot {
  position: relative;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.65);
}

/* ---------- 右侧表单区 ---------- */
.auth-main {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 48px 52px;
}

.compact-brand {
  display: none;
  align-items: center;
  gap: 8px;
  margin-bottom: 22px;
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.compact-brand img {
  width: 34px;
  height: 34px;
  object-fit: contain;
}

.form-title {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: #202534;
}

.form-sub {
  margin-top: 8px;
  margin-bottom: 30px;
  font-size: 13px;
  color: #909399;
}

@media (max-width: 860px) {
  .auth-card {
    grid-template-columns: 1fr;
    max-width: 440px;
    min-height: auto;
  }

  .auth-brand {
    display: none;
  }

  .compact-brand {
    display: flex;
  }

  .auth-main {
    padding: 34px 26px;
  }
}
</style>

<!--
  表单控件的样式放在这里统一维护：slot 内容由父页面编译，
  scoped 样式够不到 Element 的内部结构，所以用 .auth-main 前缀做作用域隔离。
-->
<style>
.auth-main .el-form-item {
  margin-bottom: 18px;
}

.auth-main .el-form-item__label {
  padding-bottom: 6px;
  font-size: 13px;
  font-weight: 500;
  line-height: 1.4;
  color: #5a6072;
}

.auth-main .el-input__wrapper {
  min-height: 46px;
  padding: 4px 14px;
  border-radius: 10px;
  background: #fbfcfe;
  box-shadow: 0 0 0 1px #e4e7ed inset;
  transition:
    box-shadow 0.2s ease,
    background 0.2s ease;
}

.auth-main .el-input__wrapper:hover {
  box-shadow: 0 0 0 1px #c6d4ff inset;
}

.auth-main .el-input__wrapper.is-focus {
  background: #fff;
  box-shadow:
    0 0 0 1px #7b98ff inset,
    0 0 0 3px rgba(79, 125, 251, 0.12);
}

.auth-main .el-input__prefix {
  color: #a8adb9;
}

.auth-main .el-input__inner {
  font-size: 14px;
  color: #303133;
}

/* 主按钮：和首页横幅、AI 助手同一套渐变 */
.auth-main button.submit-btn {
  width: 100%;
  height: 46px;
  margin-top: 6px;
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
  letter-spacing: 2px;
  background: linear-gradient(135deg, #4f7dfb 0%, #7c5bf5 100%);
  box-shadow: 0 12px 22px -14px rgba(90, 100, 240, 0.95);
}

.auth-main button.submit-btn:hover {
  background: linear-gradient(135deg, #3f6ef5 0%, #6b48f0 100%);
}

.auth-main button.submit-btn.is-loading {
  letter-spacing: 0;
}

.auth-main .auth-switch {
  margin-top: 22px;
  text-align: center;
  font-size: 13px;
  color: #909399;
}

.auth-main .auth-switch a {
  margin-left: 2px;
  color: #4f7dfb;
  font-weight: 600;
  text-decoration: none;
}

.auth-main .auth-switch a:hover {
  text-decoration: underline;
}
</style>
