<template>
  <div class="ai-chat">
    <div class="chat-card">
      <!-- 头部 -->
      <header class="chat-header">
        <div class="brand">
          <div class="brand-icon">
            <el-icon :size="22"><MagicStick /></el-icon>
          </div>
          <div class="brand-text">
            <div class="brand-title">AI 智能助手</div>
            <div class="brand-sub">
              <span class="pulse" :class="{ 'is-active': chatLoading }"></span>
              {{ chatLoading ? '正在生成回答…' : '在线 · 查实验室、问规则、帮你预约' }}
            </div>
          </div>
        </div>
        <!-- 流式输出途中不让点，避免旧回答还在往 messages 里写就换了新会话 -->
        <el-button round :disabled="chatLoading" @click="handleNewChat">
          <el-icon style="margin-right: 4px"><Refresh /></el-icon>
          新对话
        </el-button>
      </header>

      <!-- 消息区 -->
      <div class="body-wrap">
        <div ref="listRef" class="chat-body" @scroll="onScroll">
          <div v-for="(item, index) in chatMessages" :key="index" class="msg" :class="item.role">
            <div class="msg-avatar">
              <img v-if="item.role === 'user' && userInfo?.avatar" :src="userInfo.avatar" alt="" />
              <el-icon v-else :size="18">
                <User v-if="item.role === 'user'" />
                <MagicStick v-else />
              </el-icon>
            </div>

            <div class="msg-bubble">
              <!-- 工具调用过程 -->
              <div v-if="item.role === 'assistant' && item.steps?.length" class="msg-steps">
                <div v-for="(step, i) in item.steps" :key="i" class="msg-step">
                  <span class="step-dot"></span>{{ step }}
                </div>
              </div>

              <!-- 状态文案（还没出字的时候配个跳动的省略号） -->
              <div v-if="item.role === 'assistant' && item.status" class="msg-status">
                <span>{{ item.status }}</span>
                <span v-if="!item.content" class="typing"><i></i><i></i><i></i></span>
              </div>

              <div
                v-if="item.content"
                class="msg-content"
                v-html="parseMarkdown(item.content)"
              ></div>

              <!-- 打字光标 -->
              <span v-if="isStreaming(index)" class="cursor"></span>
            </div>
          </div>
        </div>

        <!-- 回到底部 -->
        <transition name="fade">
          <div v-show="!stickToBottom" class="to-bottom" @click="scrollToBottom('smooth')">
            <el-icon><ArrowDown /></el-icon>
          </div>
        </transition>
      </div>

      <!-- 输入区 -->
      <footer class="chat-footer">
        <div v-if="showChips" class="chips">
          <button v-for="text in suggestions" :key="text" class="chip" @click="useSuggestion(text)">
            {{ text }}
          </button>
        </div>

        <div class="composer">
          <el-input
            v-model="input"
            type="textarea"
            :rows="2"
            resize="none"
            placeholder="问问实验室怎么预约、开放时间..."
            @keydown.enter.exact.prevent="handleSend"
            @keydown.enter.shift.stop
          ></el-input>
          <el-button
            class="send-btn"
            type="primary"
            circle
            :loading="chatLoading"
            @click="handleSend"
          >
            <el-icon v-if="!chatLoading" :size="18"><Promotion /></el-icon>
          </el-button>
        </div>
        <div class="composer-tip">Enter 发送 · Shift + Enter 换行</div>
      </footer>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, nextTick, onMounted } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify' // 过滤危险的 HTML，防止 XSS 攻击
import { ArrowDown, MagicStick, Promotion, Refresh, User } from '@element-plus/icons-vue'
import { chatStreamApi } from '@/api/ai'
import { ElMessage } from 'element-plus'
import { useUser } from '@/utils/user'
// 对话历史放在 store 里（模块单例 + localStorage），
// 路由切走时组件销毁了数据也不丢，切回来还能接着聊
import { chatMessages, chatLoading, resetChat } from '@/stores/chat'

const { userInfo } = useUser()

const input = ref('')
const listRef = ref()

/** 贴底开关：用户手动往上翻时关掉，免得每个 token 都把他拽回底部 */
const stickToBottom = ref(true)

const suggestions = [
  '帮我预约明天下午 3 点的云计算实验室',
  '实验室的开放时间是几点？',
  '有哪些可以做深度学习的设备？',
  '取消了预约还能再约吗？'
]

/** 只有开场白时显示推荐问题 */
const showChips = computed(() => chatMessages.value.length <= 1)

const scrollToBottom = (behavior = 'auto') => {
  nextTick(() => {
    const elem = listRef.value
    if (!elem) return
    stickToBottom.value = true
    if (behavior === 'smooth') {
      elem.scrollTo({ top: elem.scrollHeight, behavior: 'smooth' })
    } else {
      elem.scrollTop = elem.scrollHeight
    }
  })
}

/** 距底部 120px 以内算「贴底」 */
const onScroll = () => {
  const elem = listRef.value
  if (!elem) return
  const distance = elem.scrollHeight - elem.scrollTop - elem.clientHeight
  stickToBottom.value = distance < 120
}

/** 最后一条助手消息还在流式输出时，给个打字光标 */
const isStreaming = (index) =>
  chatLoading.value &&
  index === chatMessages.value.length - 1 &&
  chatMessages.value[index]?.role === 'assistant'

const useSuggestion = (text) => {
  input.value = text
}

const handleSend = async () => {
  const text = input.value.trim()
  if (!text || chatLoading.value) return

  chatMessages.value.push({ role: 'user', content: text })
  input.value = ''
  chatLoading.value = true
  scrollToBottom()

  // 必须用 reactive：普通对象 push 后再改字段，视图可能不更新
  const assistant = reactive({
    role: 'assistant',
    content: '', // 正文：靠 token 一点点拼
    status: '正在思考…', // 当前状态文案
    steps: [] // 过程流水，不进下次 history
  })
  chatMessages.value.push(assistant)

  const history = chatMessages.value
    .filter((item) => item.role === 'user' || item.role === 'assistant')
    .slice(0, -1) // 去掉刚插入的空助手，避免把空 content 送回去
    // 只保留 role/content；status、steps 丢掉
    .map(({ role, content }) => ({ role, content }))

  try {
    // 第二个参数是回调：每解析出一条 SSE 事件就进一次
    await chatStreamApi({ messages: history }, (evt) => {
      if (evt.type === 'status') {
        assistant.status = evt.message || '正在思考…'
      } else if (evt.type === 'tool_start') {
        const label = evt.label || evt.name || '工具'
        assistant.status = `正在${label}…`
        assistant.steps.push(`开始：${label}`)
      } else if (evt.type === 'tool_end') {
        const label = evt.label || evt.name || '工具'
        assistant.status = `${label}完成`
        assistant.steps.push(`完成：${label}`)
      } else if (evt.type === 'token') {
        assistant.content += evt.content || '' // 打字机：追加，不是覆盖
        assistant.status = '' // 开始出字后清掉「正在…」，避免叠在一起
      } else if (evt.type === 'done') {
        assistant.status = ''
        // 注意：不要在这里再 append 一整段正文，否则会双份
      } else if (evt.type === 'error') {
        assistant.status = ''
        if (!assistant.content) {
          assistant.content = evt.message || '请求失败'
        }
        ElMessage.error(evt.message || '请求失败')
      }
      if (stickToBottom.value) scrollToBottom()
    })
  } catch (err) {
    assistant.status = ''
    if (!assistant.content) {
      assistant.content = err.message || '网络异常'
    }
    ElMessage.error(err.message || '网络异常')
  } finally {
    chatLoading.value = false
    assistant.status = ''
    scrollToBottom()
  }
}

// 开一段新对话：历史和输入框草稿都清掉
const handleNewChat = () => {
  resetChat()
  input.value = ''
  scrollToBottom()
}

// 从别的页面切回来时，先滚到底部，直接看到最后一轮对话
onMounted(scrollToBottom)

// 将 markdown 字符串转换为安全的 HTML 字符串
const parseMarkdown = (text) => {
  if (!text) return ''
  marked.setOptions({ breaks: true }) // 把 \n 转换成 <br>
  // 使用 marked 解析，然后用 DOMPurify 清理
  const rawHtml = marked.parse(text)
  return DOMPurify.sanitize(rawHtml)
}
</script>

<style scoped>
.ai-chat {
  /* 撑满 el-main：100vh 减掉头部 60 和 el-main 上下内边距 40 */
  height: calc(100vh - 100px);
  min-height: 460px;
}

.chat-card {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 14px;
  box-shadow: 0 6px 24px -18px rgba(0, 0, 0, 0.35);
}

/* ---------- 头部 ---------- */
.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 18px;
  border-bottom: 1px solid #f0f2f5;
  background: linear-gradient(120deg, #f7f9ff 0%, #fbf8ff 100%);
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.brand-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  flex-shrink: 0;
  border-radius: 12px;
  color: #fff;
  background: linear-gradient(135deg, #4f7dfb 0%, #7c5bf5 100%);
  box-shadow: 0 6px 14px -8px rgba(90, 100, 240, 0.9);
}

.brand-title {
  font-size: 16px;
  font-weight: 700;
  color: #303133;
}

.brand-sub {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 3px;
  font-size: 12px;
  color: #909399;
}

.pulse {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #67c23a;
  flex-shrink: 0;
}

.pulse.is-active {
  background: #409eff;
  animation: pulse 1.2s ease-in-out infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
    transform: scale(1);
  }
  50% {
    opacity: 0.35;
    transform: scale(0.75);
  }
}

/* ---------- 消息区 ---------- */
/* 包一层：给「回到底部」按钮做定位参照，按钮不会跟着消息一起滚走 */
.body-wrap {
  position: relative;
  display: flex;
  flex: 1;
  min-height: 0;
}

.chat-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 20px 20px 8px;
  background:
    radial-gradient(circle at 12% 0%, rgba(79, 125, 251, 0.05), transparent 42%),
    radial-gradient(circle at 88% 8%, rgba(155, 107, 242, 0.06), transparent 40%), #fafbfd;
}

.msg {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 18px;
}

.msg.user {
  flex-direction: row-reverse;
}

.msg-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  flex-shrink: 0;
  border-radius: 50%;
  color: #fff;
  overflow: hidden;
  background: linear-gradient(135deg, #4f7dfb 0%, #7c5bf5 100%);
}

.msg.user .msg-avatar {
  background: #e8eaf6;
  color: #5b6bd6;
}

.msg-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.msg-bubble {
  max-width: min(78%, 720px);
  padding: 12px 14px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.75;
  word-break: break-word;
  background: #fff;
  color: #303133;
  border: 1px solid #ebeef5;
  box-shadow: 0 2px 10px -8px rgba(0, 0, 0, 0.5);
}

.msg.user .msg-bubble {
  background: linear-gradient(135deg, #4f7dfb 0%, #6b5cf6 100%);
  border-color: transparent;
  color: #fff;
  box-shadow: 0 6px 16px -10px rgba(90, 100, 240, 0.9);
}

/* 助手的过程流水 */
.msg-steps {
  margin-bottom: 10px;
  padding: 8px 10px;
  border-radius: 8px;
  background: #f5f7fc;
  font-size: 12px;
  line-height: 1.9;
  color: #7a8290;
}

.msg-step {
  display: flex;
  align-items: center;
  gap: 6px;
}

.step-dot {
  width: 5px;
  height: 5px;
  flex-shrink: 0;
  border-radius: 50%;
  background: #a8b0c2;
}

.msg-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #909399;
}

.msg-status + .msg-content {
  margin-top: 6px;
}

/* 跳动的省略号 */
.typing {
  display: inline-flex;
  gap: 3px;
  align-items: center;
}

.typing i {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: #b7bcc9;
  animation: blink 1.2s infinite ease-in-out;
}

.typing i:nth-child(2) {
  animation-delay: 0.2s;
}

.typing i:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes blink {
  0%,
  80%,
  100% {
    opacity: 0.3;
  }
  40% {
    opacity: 1;
  }
}

/* 打字光标 */
.cursor {
  display: inline-block;
  width: 2px;
  height: 14px;
  margin-left: 2px;
  vertical-align: -2px;
  background: #4f7dfb;
  animation: blink-cursor 0.9s step-end infinite;
}

@keyframes blink-cursor {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0;
  }
}

/* ---------- markdown 正文 ---------- */
.msg-content :deep(p) {
  margin: 0 0 8px;
}

.msg-content :deep(p:last-child) {
  margin-bottom: 0;
}

.msg-content :deep(h1),
.msg-content :deep(h2),
.msg-content :deep(h3),
.msg-content :deep(h4) {
  margin: 12px 0 6px;
  font-size: 15px;
  font-weight: 600;
}

.msg-content :deep(ul),
.msg-content :deep(ol) {
  margin: 6px 0;
  padding-left: 20px;
  list-style: revert;
}

.msg-content :deep(li) {
  margin: 2px 0;
}

.msg-content :deep(code) {
  padding: 1px 5px;
  border-radius: 4px;
  background: #f2f3f7;
  font-family: Consolas, Monaco, monospace;
  font-size: 13px;
  color: #c7254e;
}

.msg-content :deep(pre) {
  margin: 8px 0;
  padding: 12px;
  overflow-x: auto;
  border-radius: 8px;
  background: #f7f8fa;
}

.msg-content :deep(pre code) {
  padding: 0;
  background: transparent;
  color: inherit;
}

.msg-content :deep(blockquote) {
  margin: 8px 0;
  padding: 4px 12px;
  border-left: 3px solid #c6d4ff;
  background: #f7f9ff;
  color: #606266;
}

.msg-content :deep(table) {
  width: 100%;
  margin: 8px 0;
  border-collapse: collapse;
  font-size: 13px;
}

.msg-content :deep(th),
.msg-content :deep(td) {
  padding: 6px 10px;
  border: 1px solid #ebeef5;
  text-align: left;
}

.msg-content :deep(th) {
  background: #f7f8fa;
}

.msg-content :deep(a) {
  color: #4f7dfb;
}

/* 用户气泡里的 markdown 反过来配色 */
.msg.user .msg-content :deep(code) {
  background: rgba(255, 255, 255, 0.22);
  color: #fff;
}

.msg.user .msg-content :deep(a) {
  color: #fff;
  text-decoration: underline;
}

/* ---------- 回到底部 ---------- */
.to-bottom {
  position: absolute;
  right: 26px;
  bottom: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  color: #5b6bd6;
  background: #fff;
  border: 1px solid #e4e7ed;
  box-shadow: 0 4px 14px -6px rgba(0, 0, 0, 0.35);
  cursor: pointer;
  transition: transform 0.2s ease;
}

.to-bottom:hover {
  transform: translateY(-2px);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* ---------- 输入区 ---------- */
.chat-footer {
  padding: 12px 18px 14px;
  border-top: 1px solid #f0f2f5;
  background: #fff;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}

.chip {
  padding: 6px 12px;
  border: 1px solid #e4e9f7;
  border-radius: 999px;
  background: #f7f9ff;
  color: #4f5bd6;
  font-size: 12px;
  font-family: inherit;
  cursor: pointer;
  transition:
    background 0.2s ease,
    border-color 0.2s ease,
    transform 0.2s ease;
}

.chip:hover {
  transform: translateY(-1px);
  border-color: #c6d4ff;
  background: #eef2ff;
}

.composer {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  padding: 8px 8px 8px 12px;
  border: 1px solid #e4e7ed;
  border-radius: 12px;
  background: #fcfdff;
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.composer:focus-within {
  border-color: #a9bcff;
  background: #fff;
  box-shadow: 0 0 0 3px rgba(79, 125, 251, 0.12);
}

.composer :deep(.el-textarea__inner) {
  padding: 4px 0;
  border: none;
  background: transparent;
  box-shadow: none;
  font-family: inherit;
  font-size: 14px;
  line-height: 1.7;
  color: #303133;
}

.composer :deep(.el-textarea__inner:focus) {
  box-shadow: none;
}

.send-btn {
  width: 38px;
  height: 38px;
  flex-shrink: 0;
  border: none;
  background: linear-gradient(135deg, #4f7dfb 0%, #7c5bf5 100%);
  box-shadow: 0 6px 14px -8px rgba(90, 100, 240, 0.95);
}

.send-btn:hover {
  background: linear-gradient(135deg, #3f6ef5 0%, #6b48f0 100%);
}

.composer-tip {
  margin-top: 6px;
  font-size: 11px;
  color: #b6bbc8;
  text-align: right;
}

@media (max-width: 768px) {
  .ai-chat {
    height: calc(100vh - 88px);
  }

  .msg-bubble {
    max-width: 86%;
  }

  .chat-body {
    padding: 16px 12px 8px;
  }
}
</style>
