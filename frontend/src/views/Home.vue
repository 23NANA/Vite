<template>
  <div class="home">
    <!-- 顶部欢迎横幅 -->
    <div class="hero">
      <div class="hero-main">
        <div class="hero-avatar">
          <img :src="userInfo?.avatar || defaultAvatar" alt="" />
        </div>
        <div>
          <div class="hero-title">{{ greeting }}，{{ userInfo?.name || '同学' }}</div>
          <div class="hero-sub">
            <el-tag size="small" effect="dark" round class="hero-tag">{{ roleLabel }}</el-tag>
            <span>{{ today }}</span>
            <span class="dot">·</span>
            <span>智能实验室预约系统</span>
          </div>
        </div>
      </div>
      <el-button class="hero-btn" size="large" round @click="$router.push('/manager/ai-chat')">
        <el-icon style="margin-right: 6px"><MagicStick /></el-icon>
        打开 AI 助手
      </el-button>
    </div>

    <!-- 数据概览 -->
    <el-row :gutter="16" class="col-row">
      <el-col :xs="12" :sm="12" :md="6" v-for="item in statCards" :key="item.label">
        <div class="stat-card" :style="{ '--accent': item.color }">
          <div class="stat-icon">
            <el-icon :size="22"><component :is="item.icon" /></el-icon>
          </div>
          <div class="stat-body">
            <div class="stat-label">{{ item.label }}</div>
            <div class="stat-value">{{ item.value }}</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="16" class="col-row">
      <!-- 快捷入口 -->
      <el-col :xs="24" :md="14">
        <el-card shadow="never" class="panel">
          <template #header>
            <div class="panel-header">
              <span class="panel-title">快捷入口</span>
              <span class="panel-desc">常用功能一键直达</span>
            </div>
          </template>
          <div class="shortcut-grid">
            <div
              class="shortcut"
              v-for="item in shortcuts"
              :key="item.path"
              @click="$router.push(item.path)"
            >
              <div class="shortcut-icon" :style="{ '--accent': item.color }">
                <el-icon :size="20"><component :is="item.icon" /></el-icon>
              </div>
              <div class="shortcut-text">
                <div class="shortcut-label">{{ item.label }}</div>
                <div class="shortcut-desc">{{ item.desc }}</div>
              </div>
              <el-icon class="shortcut-arrow"><ArrowRight /></el-icon>
            </div>
          </div>
        </el-card>
      </el-col>

      <!-- 最近预约 -->
      <el-col :xs="24" :md="10">
        <el-card shadow="never" class="panel">
          <template #header>
            <div class="panel-header">
              <span class="panel-title">最近预约</span>
              <el-link type="primary" :underline="false" @click="$router.push(recentLink)">
                查看全部
              </el-link>
            </div>
          </template>
          <div v-if="recentList.length" class="recent-list">
            <div class="recent-item" v-for="row in recentList" :key="row.id">
              <div class="recent-date">
                <div class="recent-day">{{ dayOf(row.date) }}</div>
                <div class="recent-month">{{ monthOf(row.date) }}</div>
              </div>
              <div class="recent-main">
                <div class="recent-name">{{ row.lab_name || '-' }}</div>
                <div class="recent-meta">
                  <el-tag size="small" type="info" effect="plain" class="recent-type">
                    {{ row.type || '实验室' }}
                  </el-tag>
                  <span>{{ row.start_time }} - {{ row.end_time }}</span>
                </div>
              </div>
              <el-tag :type="statusType(row.status)" effect="light" round size="small">
                {{ statusText(row.status) }}
              </el-tag>
            </div>
          </div>
          <el-empty v-else description="还没有预约记录" :image-size="70" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 系统能做什么 -->
    <el-card shadow="never" class="panel">
      <template #header>
        <div class="panel-header">
          <span class="panel-title">系统能做什么</span>
        </div>
      </template>
      <el-row :gutter="16">
        <el-col :xs="24" :sm="12" :md="8" v-for="item in features" :key="item.title">
          <div class="feature" :style="{ '--accent': item.color }">
            <div class="feature-icon">
              <el-icon :size="22"><component :is="item.icon" /></el-icon>
            </div>
            <div class="feature-title">{{ item.title }}</div>
            <div class="feature-desc">{{ item.desc }}</div>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useUser } from '@/utils/user'
import { getLabPageList } from '@/api/lab'
import { getReservationPageList } from '@/api/reservation'
import {
  ArrowRight,
  Calendar,
  ChatDotRound,
  CircleCheck,
  Clock,
  DocumentChecked,
  House,
  MagicStick,
  OfficeBuilding,
  Reading,
  Setting,
  Tickets,
  User
} from '@element-plus/icons-vue'
import defaultAvatar from '@/assets/imgs/logo.png'

const { userInfo } = useUser()

const labTotal = ref('-')
const reservationTotal = ref('-')
const pendingTotal = ref('-')
const approvedTotal = ref('-')
const recentList = ref([])

const isAdmin = computed(() => userInfo.value?.role === 'admin')

const roleLabel = computed(() => (isAdmin.value ? '管理员' : '学生'))

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜深了'
  if (h < 12) return '早上好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  return '晚上好'
})

const today = computed(() => {
  const now = new Date()
  const week = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][now.getDay()]
  return `${now.getFullYear()}年${now.getMonth() + 1}月${now.getDate()}日 ${week}`
})

const statCards = computed(() => [
  {
    label: '开放实验室',
    value: labTotal.value,
    icon: OfficeBuilding,
    color: '#409eff'
  },
  {
    label: isAdmin.value ? '全部预约' : '我的预约',
    value: reservationTotal.value,
    icon: Tickets,
    color: '#7c5bf5'
  },
  {
    label: '待审核',
    value: pendingTotal.value,
    icon: Clock,
    color: '#e6a23c'
  },
  {
    label: '已通过',
    value: approvedTotal.value,
    icon: CircleCheck,
    color: '#67c23a'
  }
])

const features = [
  {
    title: '业务预约',
    desc: '实验室 / 设备浏览、提交预约、我的预约与管理员审核。',
    icon: Calendar,
    color: '#409eff'
  },
  {
    title: '知识库问答',
    desc: 'RAG 检索规则与开放时间等文档，回答有据可依。',
    icon: Reading,
    color: '#67c23a'
  },
  {
    title: '智能 Agent',
    desc: 'Tool Calling + LangGraph：查库、流式过程可见，对话确认后提交预约。',
    icon: MagicStick,
    color: '#7c5bf5'
  }
]

const shortcuts = computed(() => {
  const list = [
    {
      label: 'AI 智能助手',
      desc: '对话式完成查库与预约',
      path: '/manager/ai-chat',
      icon: ChatDotRound,
      color: '#7c5bf5'
    },
    {
      label: '我的预约',
      desc: '查看与取消预约记录',
      path: '/manager/my-reservation',
      icon: Tickets,
      color: '#409eff'
    },
    {
      label: '实验室列表',
      desc: '浏览可用实验室与设备',
      path: '/manager/lablist',
      icon: OfficeBuilding,
      color: '#67c23a'
    }
  ]
  if (isAdmin.value) {
    list[1] = {
      label: '预约审核',
      desc: '审批待处理的预约申请',
      path: '/manager/audit-reservation',
      icon: DocumentChecked,
      color: '#e6a23c'
    }
    list[2] = {
      label: '实验室管理',
      desc: '维护实验室基础信息',
      path: '/manager/lab',
      icon: House,
      color: '#409eff'
    }
    list.push(
      {
        label: '设备管理',
        desc: '维护实验室下的设备',
        path: '/manager/equipment',
        icon: Setting,
        color: '#67c23a'
      },
      {
        label: '用户管理',
        desc: '管理用户账号与角色',
        path: '/manager/user',
        icon: User,
        color: '#f56c6c'
      }
    )
  }
  return list
})

const recentLink = computed(() =>
  isAdmin.value ? '/manager/audit-reservation' : '/manager/my-reservation'
)

const statusType = (status) =>
  ({ 0: 'warning', 1: 'success', 2: 'danger', 3: 'info' })[status] || 'info'

const statusText = (status) =>
  ({ 0: '待审核', 1: '已通过', 2: '已拒绝', 3: '已取消' })[status] || '未知'

// date 形如 2026-06-08，取日/月给日期块用
const dayOf = (date) => (date ? String(date).slice(8, 10) : '--')
const monthOf = (date) => (date ? `${Number(String(date).slice(5, 7))}月` : '')

/** 取分页接口的 total，失败时保持原样（'-'） */
const pickTotal = (res, target) => {
  if (res?.code === 200) target.value = res.data?.total ?? 0
}

onMounted(async () => {
  const results = await Promise.allSettled([
    getLabPageList({ page: 1, page_size: 1, status: 1 }),
    getReservationPageList({ page: 1, page_size: 5 }),
    getReservationPageList({ page: 1, page_size: 1, status: 0 }),
    getReservationPageList({ page: 1, page_size: 1, status: 1 })
  ])

  const [labRes, recentRes, pendingRes, approvedRes] = results
  if (labRes.status === 'fulfilled') pickTotal(labRes.value, labTotal)
  if (pendingRes.status === 'fulfilled') pickTotal(pendingRes.value, pendingTotal)
  if (approvedRes.status === 'fulfilled') pickTotal(approvedRes.value, approvedTotal)
  if (recentRes.status === 'fulfilled' && recentRes.value?.code === 200) {
    const page = recentRes.value.data
    recentList.value = page?.list || []
    reservationTotal.value = page?.total ?? 0
  }
})
</script>

<style scoped>
.home {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ---------- 欢迎横幅 ---------- */
.hero {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 26px 28px;
  border-radius: 14px;
  color: #fff;
  background: linear-gradient(120deg, #4f7dfb 0%, #6b5cf6 55%, #9b6bf2 100%);
  box-shadow: 0 10px 24px -12px rgba(80, 90, 220, 0.75);
}

/* 两个模糊光斑，让纯色渐变不那么平 */
.hero::before,
.hero::after {
  content: '';
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.16);
  pointer-events: none;
}

.hero::before {
  width: 220px;
  height: 220px;
  top: -120px;
  right: 12%;
}

.hero::after {
  width: 140px;
  height: 140px;
  bottom: -90px;
  right: 30%;
  background: rgba(255, 255, 255, 0.1);
}

.hero-main {
  position: relative;
  display: flex;
  align-items: center;
  gap: 16px;
  min-width: 0;
}

.hero-avatar img {
  width: 58px;
  height: 58px;
  border-radius: 50%;
  object-fit: cover;
  background: #fff;
  border: 2px solid rgba(255, 255, 255, 0.7);
}

.hero-title {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.hero-sub {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.86);
}

.hero-sub .dot {
  opacity: 0.6;
}

.hero-tag {
  background: rgba(255, 255, 255, 0.22);
  border-color: transparent;
}

.hero-btn {
  position: relative;
  flex-shrink: 0;
  border: none;
  font-weight: 600;
  color: #4f5bfb;
  background: #fff;
}

.hero-btn:hover {
  color: #3d47e0;
  background: #f2f3ff;
}

/* ---------- 数据概览 ---------- */
.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  height: 100%;
  padding: 16px 18px;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 12px;
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px -12px rgba(0, 0, 0, 0.35);
}

.stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 46px;
  height: 46px;
  flex-shrink: 0;
  border-radius: 12px;
  color: var(--accent);
  background: color-mix(in srgb, var(--accent) 12%, #fff);
}

.stat-body {
  min-width: 0;
}

.stat-label {
  font-size: 13px;
  color: #909399;
}

.stat-value {
  margin-top: 4px;
  font-size: 26px;
  font-weight: 700;
  line-height: 1.1;
  color: #303133;
}

/* ---------- 面板通用 ---------- */
.panel {
  height: 100%;
  border-radius: 12px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.panel-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.panel-desc {
  font-size: 12px;
  color: #a8abb2;
}

/* ---------- 快捷入口 ---------- */
.shortcut-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 12px;
}

.shortcut {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px;
  border: 1px solid #ebeef5;
  border-radius: 10px;
  cursor: pointer;
  transition:
    border-color 0.2s ease,
    background 0.2s ease,
    transform 0.2s ease;
}

.shortcut:hover {
  transform: translateY(-2px);
  border-color: color-mix(in srgb, var(--accent) 40%, #fff);
  background: #fafbff;
}

.shortcut-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  border-radius: 10px;
  color: #fff;
  background: var(--accent);
}

.shortcut-text {
  flex: 1;
  min-width: 0;
}

.shortcut-label {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.shortcut-desc {
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.shortcut-arrow {
  color: #c0c4cc;
  transition: transform 0.2s ease;
}

.shortcut:hover .shortcut-arrow {
  color: #409eff;
  transform: translateX(3px);
}

/* ---------- 最近预约 ---------- */
.recent-list {
  display: flex;
  flex-direction: column;
}

.recent-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px dashed #ebeef5;
}

.recent-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.recent-date {
  width: 46px;
  flex-shrink: 0;
  padding: 4px 0;
  text-align: center;
  border-radius: 8px;
  background: #f4f6fb;
}

.recent-day {
  font-size: 16px;
  font-weight: 700;
  line-height: 1.2;
  color: #4f7dfb;
}

.recent-month {
  font-size: 11px;
  color: #909399;
}

.recent-main {
  flex: 1;
  min-width: 0;
}

.recent-name {
  font-size: 14px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.recent-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
}

/* ---------- 系统能做什么 ---------- */
.feature {
  height: 100%;
  padding: 18px;
  border-radius: 10px;
  background: color-mix(in srgb, var(--accent) 6%, #fff);
  border: 1px solid color-mix(in srgb, var(--accent) 14%, #fff);
  transition: transform 0.2s ease;
}

.feature:hover {
  transform: translateY(-2px);
}

.feature-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 42px;
  height: 42px;
  border-radius: 10px;
  color: #fff;
  background: var(--accent);
  margin-bottom: 12px;
}

.feature-title {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}

.feature-desc {
  margin-top: 8px;
  font-size: 13px;
  line-height: 1.7;
  color: #606266;
}

/* 小屏留白收一收 */
@media (max-width: 768px) {
  /* 小屏下栅格会折行，折行后补行间距 */
  .col-row {
    row-gap: 12px;
  }

  .hero {
    flex-direction: column;
    align-items: flex-start;
    padding: 20px;
  }

  .hero-btn {
    width: 100%;
  }

  .feature {
    margin-bottom: 12px;
  }
}
</style>
