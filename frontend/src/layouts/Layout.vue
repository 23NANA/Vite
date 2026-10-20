<template>
  <div>
    <el-container style="min-height: 100vh">
      <el-header
        style="
          display: flex;
          align-items: center;
          border-bottom: 1px solid #ddd;
          background-color: #fff;
        "
      >
        <div
          style="flex: 1; display: flex; align-items: center; font-size: 24px; font-weight: bold"
        >
          <img style="width: 40px" src="@/assets/imgs/logo.png" alt="" />
          <div style="margin-left: 5px">智能实验室预约系统</div>
        </div>
        <el-dropdown @command="handleCommand">
          <div style="display: flex; align-items: center; cursor: pointer">
            <img
              :src="userInfo?.avatar || defaultAvatar"
              alt=""
              style="width: 30px; height: 30px; border-radius: 50%; object-fit: cover"
            />
            <div style="margin-left: 3px">{{ userInfo?.name }}</div>
          </div>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="profile">个人信息</el-dropdown-item>
              <el-dropdown-item command="password">修改密码</el-dropdown-item>
              <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>
      <el-container>
        <el-aside width="220px">
          <el-menu router :default-active="route.path" style="height: 100%">
            <el-menu-item index="/manager/home">
              <el-icon><icon-menu /></el-icon>
              系统首页
            </el-menu-item>
            <el-menu-item index="/manager/lablist" v-if="userInfo?.role === 'student'">
              <el-icon><OfficeBuilding /></el-icon>
              实验室列表
            </el-menu-item>
            <el-menu-item index="/manager/lab" v-if="userInfo?.role === 'admin'">
              <el-icon><House /></el-icon>
              实验室管理
            </el-menu-item>
            <el-menu-item index="/manager/equipment" v-if="userInfo?.role === 'admin'">
              <el-icon><Setting /></el-icon>
              设备列表管理
            </el-menu-item>
            <el-menu-item index="/manager/my-reservation" v-if="userInfo?.role === 'student'">
              <el-icon><Tickets /></el-icon>
              我的预约
            </el-menu-item>
            <el-menu-item index="/manager/audit-reservation" v-if="userInfo?.role === 'admin'">
              <el-icon><DocumentChecked /></el-icon>
              预约审核
            </el-menu-item>
            <el-menu-item index="/manager/user" v-if="userInfo?.role === 'admin'">
              <el-icon><User /></el-icon>
              用户管理
            </el-menu-item>
            <el-menu-item index="/manager/ai-chat">
              <el-icon><ChatDotRound /></el-icon>
              AI智能助手
            </el-menu-item>
          </el-menu>
        </el-aside>
        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup>
import { useRouter, useRoute } from 'vue-router'
import { useUser } from '@/utils/user'
import { logout } from '@/utils/auth'
import { resetChat } from '@/stores/chat'
import defaultAvatar from '@/assets/imgs/logo.png'
import {
  Menu as IconMenu,
  House,
  Setting,
  User,
  OfficeBuilding,
  Tickets,
  DocumentChecked,
  ChatDotRound,
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const { userInfo } = useUser()

const handleCommand = (command) => {
  if (command === 'profile') {
    router.push('/manager/profile')
  } else if (command === 'password') {
    router.push('/manager/password')
  }else if (command === 'logout') {
    logout()
    resetChat() // 清掉 AI 对话，共用电脑时下个登录的人不该看到上个人的聊天记录
    router.push('/login')
  }
}
</script>