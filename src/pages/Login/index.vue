<script setup>
import {reactive} from 'vue';
import {useRouter} from 'vue-router';
import {message} from 'ant-design-vue';
import {UserOutlined, LockOutlined} from '@ant-design/icons-vue';

const router = useRouter();
const formState = reactive({
  username: '',
  password: '',
});

const onFinish = values => {
  // --- 模拟登录逻辑 ---
  if (values.username === 'admin' && values.password === 'password') {
    localStorage.setItem('userLoggedIn', 'true');
    message.success('登录成功!');
    router.push('/railway-vehicle-manage');
  } else {
    message.error('用户名或密码错误!');
  }
  // --- 模拟登录逻辑结束 ---
};

const onFinishFailed = errorInfo => {
  console.log('Failed:', errorInfo);
  message.error('请完整填写登录信息');
};
</script>

<template>
  <div class="login-container">
    <a-card class="login-card" :bordered="false">
      <template #title>
        <img src="/src/assets/csu-logo.png" alt="Logo" class="login-logo"/>
        <div class="login-title">TVDS客车作业异常检测系统</div>
      </template>
      <a-form
          :model="formState"
          name="login"
          @finish="onFinish"
          @finishFailed="onFinishFailed"
          autocomplete="off"
          layout="vertical"
      >
        <a-form-item
            label="用户名"
            name="username"
            :rules="[{ required: true, message: '请输入用户名!' }]">
          <a-input size="large" v-model:value="formState.username" placeholder="请输入用户名">
            <template #prefix>
              <UserOutlined style="color: rgba(0,0,0,.25)"/>
            </template>
          </a-input>
        </a-form-item>

        <a-form-item
            label="密码"
            name="password"
            :rules="[{ required: true, message: '请输入密码!' }]"
        >
          <a-input-password size="large" v-model:value="formState.password" placeholder="请输入密码">
            <template #prefix>
              <LockOutlined style="color: rgba(0,0,0,.25)"/>
            </template>
          </a-input-password>
        </a-form-item>

        <a-form-item>
          <a-button type="primary" html-type="submit" block size="large">
            登 录
          </a-button>
        </a-form-item>
      </a-form>
    </a-card>
  </div>
</template>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  /* 背景图片 */
  background-image: url('/src/assets/background-login.jpg');
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  overflow: hidden;
}

.login-logo {
  display: block; /* 让图片成为块级元素，以便使用 margin auto 居中 */
  max-height: 60px; /* 调整 Logo 高度 */
  margin: 0 auto 20px auto; /* 上下边距，左右自动居中 */
}

.login-card {
  width: 400px;
  padding: 20px;
  background-color: rgba(255, 255, 255, 0.9); /* 登录表单透明度 */
  border-radius: 8px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  /* 表单位置 */
  transform: translateY(-100px);
  /* 添加动画 */
  animation: fadeIn 0.5s ease-out;
}

/* Override Ant Design's default card header padding and style */
:deep(.ant-card-head) {
  border-bottom: none; /* Remove default border */
  padding: 0 0 24px 0; /* Adjust padding */
  text-align: center;
}

.login-title {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

/* Style form items for better spacing and alignment */
:deep(.ant-form-item-label > label) {
  color: #111; /* Slightly lighter label color */
  font-size: 16px; /* Adjust label font size */
}

:deep(.ant-form-item) {
  margin-bottom: 20px; /* Adjust spacing between form items */
}

/* Ensure button has some top margin */
:deep(.ant-form-item:last-child) {
  margin-bottom: 0; /* Remove margin from the last item */
}

:deep(.ant-form-item-control-input-content > .ant-btn) {
  margin-top: 10px; /* Add space above the button */
}

/* Optional fade-in animation */
@keyframes fadeIn {
  from {
    opacity: 0;
    /* Adjust initial translateY if needed, or keep it simple */
    transform: translateY(-120px); /* Start slightly higher to animate down to -100px */
  }
  to {
    opacity: 1;
    transform: translateY(-100px); /* Final position */
  }
}
</style>