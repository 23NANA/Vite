import { ref, watch } from 'vue'

/**
 * AI 对话的会话状态。
 *
 * 为什么写在模块作用域，而不是 AIChat.vue 里面？
 * ES module 只会被执行一次，这里导出的 ref 就是个全局单例：
 * 组件被路由切走销毁后，数据还留在这个模块里，切回来直接复用。
 * 再配合 localStorage，连刷新浏览器都能把历史恢复出来。
 */
const STORAGE_KEY = 'ai_chat_messages'

const WELCOME_TEXT =
  '您好，我是实验室助手。你可以向我提问怎么预约、取消。您也可以发送[帮我预约明天下午的XXX实验室]来开始~'

function welcomeMessage() {
  return { role: 'assistant', content: WELCOME_TEXT }
}

/** 从 localStorage 恢复；内容坏了或者是空的就返回 null，交给调用方用默认开场白 */
function restore() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return null
    const list = JSON.parse(raw)
    if (!Array.isArray(list)) return null
    // 只认 role / content：status、steps 是流式过程中的临时 UI 状态，不还原
    const clean = list
      .filter(
        (item) =>
          item &&
          (item.role === 'user' || item.role === 'assistant') &&
          typeof item.content === 'string'
      )
      .map((item) => ({ role: item.role, content: item.content }))
    return clean.length ? clean : null
  } catch {
    // JSON 坏了 / 被手动改过：当作没有历史，别让页面白屏
    return null
  }
}

export const chatMessages = ref(restore() || [welcomeMessage()])

/** loading 也放进来：流式响应跑一半切走页面再回来，不能让人重复发第二条 */
export const chatLoading = ref(false)

// 流式输出时每来一个 token，messages 就变一次；
// 每个 token 都同步写一次 localStorage 会卡主线程，所以做个节流：
// 距上次保存超过 500ms 就立刻写，否则排一次尾随保存。
const SAVE_INTERVAL = 500
let lastSavedAt = 0
let saveTimer = null

function saveNow() {
  saveTimer = null
  lastSavedAt = Date.now()
  try {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify(chatMessages.value.map(({ role, content }) => ({ role, content })))
    )
  } catch {
    // 超出配额或浏览器隐私模式：存不下就算了，不影响当前这轮对话
  }
}

function scheduleSave() {
  if (saveTimer) return
  const wait = SAVE_INTERVAL - (Date.now() - lastSavedAt)
  if (wait <= 0) saveNow()
  else saveTimer = setTimeout(saveNow, wait)
}

// deep：assistant 那条是就地改 content 的（打字机效果），浅层 watch 收不到
watch(chatMessages, scheduleSave, { deep: true })

/** 开一段新对话，把历史和草稿都清掉 */
export function resetChat() {
  chatMessages.value = [welcomeMessage()]
  // 别等节流：重置后如果马上关掉页面，下次打开不该又冒出旧对话
  if (saveTimer) {
    clearTimeout(saveTimer)
    saveTimer = null
  }
  saveNow()
}
