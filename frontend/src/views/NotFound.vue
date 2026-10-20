<template>
  <div style="display: flex; justify-content: center; align-items: center; height: 60vh">
    <el-result icon="warning" title="404" sub-title="抱歉，你访问的页面不存在或功能还未开发">
      <template #extra>
        <el-button type="primary" @click="router.push('/manager/home')">返回首页</el-button>
      </template>
    </el-result>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()
</script>
