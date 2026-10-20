<template>
  <AuthLayout
    :title="brandTitle"
    subtitle="创建账号后即可浏览实验室、预约设备"
    heading="创建账号"
    description="只需一个账号，开始你的实验计划"
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
      <el-form-item prop="confirmPassword" label="确认密码">
        <el-input
          type="password"
          size="large"
          v-model="form.confirmPassword"
          placeholder="请确认密码"
          :prefix-icon="Lock"
          show-password
        />
      </el-form-item>

      <el-button
        class="submit-btn"
        size="large"
        type="primary"
        :loading="loadingValue"
        @click="register"
      >
        注 册
      </el-button>

      <div class="auth-switch">已有账号？<router-link to="/login">去登录</router-link></div>
    </el-form>
  </AuthLayout>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { User, Lock } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { registerApi } from '@/api/auth'
import router from '@/router'
import AuthLayout from '@/components/AuthLayout.vue'

const brandTitle = '开始你的\n实验计划'

const form = reactive({
  username: '',
  password: '',
  confirmPassword: ''
})

const loadingValue = ref(false)

const formRef = ref()

const validatePass = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请确认密码'))
  } else {
    if (value !== form.password) {
      callback(new Error('两次密码输入不一致'))
    } else {
      callback()
    }
  }
}
const rules = {
  username: [{ required: true, message: '请输入账号', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  confirmPassword: [{ validator: validatePass, trigger: 'blur' }]
}

const register = async () => {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  loadingValue.value = true
  try {
    const res = await registerApi(form)
    if (res.code === 200) {
      ElMessage.success('注册成功')
      await router.push('/login')
    }
  } finally {
    loadingValue.value = false
  }
}
</script>
