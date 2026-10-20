<template>
  <AuthLayout
    :title="brandTitle"
    subtitle="实验室、设备与审核进度，一个入口全部搞定"
    heading="欢迎回来"
    description="登录后即可浏览实验室、预约设备"
  >
    <el-form
      ref="formRef"
      class="auth-form"
      :rules="rules"
      :model="form"
      label-position="top"
      style="width: 100%"
    >
      <el-form-item prop="username" label="账号">
        <el-input
          size="large"
          v-model="form.username"
          placeholder="请输入账号"
          :prefix-icon="User"
        />
      </el-form-item>
      <el-form-item prop="password" label="密码">
        <el-input
          type="password"
          size="large"
          v-model="form.password"
          placeholder="请输入密码"
          :prefix-icon="Lock"
          show-password
        />
      </el-form-item>

      <el-button
        class="submit-btn"
        size="large"
        type="primary"
        @click="login"
        :loading="loadingValue"
      >
        登 录
      </el-button>

      <div class="auth-switch">还没有账号？<router-link to="/register">立即注册</router-link></div>
    </el-form>
  </AuthLayout>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { User, Lock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import router from '@/router'
import { loginApi } from '@/api/auth'
import { useUser } from '@/utils/user'
import AuthLayout from '@/components/AuthLayout.vue'

const { saveLoginData } = useUser()

const formRef = ref()

const brandTitle = '让每一次预约\n都更省心'

const form = reactive({
  username: '',
  password: ''
})

const loadingValue = ref(false)

const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

const login = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) {
    return
  }
  loadingValue.value = true
  try {
    const res = await loginApi(form)
    if (res.code == 200) {
      saveLoginData(res.data)
      ElMessage.success('登录成功')
      router.push('/manager/home')
    }
  } finally {
    loadingValue.value = false
  }
}
</script>
