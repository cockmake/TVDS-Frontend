<script setup>
import {ref} from 'vue';
import {useRouter, useRoute} from 'vue-router';
import {
  DesktopOutlined,
  SettingOutlined,
  LogoutOutlined,
  OrderedListOutlined, // Added for template edit, might need better icon
} from '@ant-design/icons-vue';

import {message} from 'ant-design-vue';

const router = useRouter();
const route = useRoute(); // Use useRoute to get current route info

const collapsed = ref(true);

// Determine selected keys based on the current route's path
const selectedKeys = ref([route.path]);

// Update selected keys when route changes
router.afterEach((to) => {
  selectedKeys.value = [to.path];
});

const handleMenuClick = (item) => {
  router.push(item.key);
};

const handleLogout = () => {
  // 清除登录状态
  localStorage.removeItem('userLoggedIn');
  message.success('已退出登录');
  router.push('/login');
};
</script>

<template>
  <a-layout style="min-height: 100vh">
    <a-layout-sider v-model:collapsed="collapsed" collapsible>
      <div class="logo">
        <img v-if="!collapsed" src="../assets/csu-logo.png" alt="Logo" style="height: 100%;"/>
        <img v-else src="../assets/csu-icon.png" alt="Logo" style="height: 100%;"/>
      </div>
      <a-menu theme="dark" v-model:selectedKeys="selectedKeys" mode="inline" @click="handleMenuClick">
        <a-menu-item key="/railway-vehicle-manage">
          <template #icon>
            <DesktopOutlined/>
          </template>
          <span>铁路车辆管理</span>
        </a-menu-item>
        <a-menu-item key="/component-manage">
          <template #icon>
            <SettingOutlined/>
          </template>
          <span>视觉模板管理</span>
        </a-menu-item>
        <a-menu-item key="/detection-task-manage">
          <template #icon>
            <OrderedListOutlined/>
          </template>
          <span>检测任务管理</span>
        </a-menu-item>
        <a-menu-item key="login" @click.stop="handleLogout"> <!-- Use .stop to prevent navigation -->
          <template #icon>
            <LogoutOutlined/>
          </template>
          <span>退出登录</span>
        </a-menu-item>
      </a-menu>
    </a-layout-sider>
    <a-layout>
      <a-layout-header style="background: #fff; padding: 0 16px; display: flex; align-items: center;">
        <!-- You can add breadcrumbs or user info here -->
        <h1 style="font-weight: bold">TVDS作业管理系统</h1>
      </a-layout-header>
      <a-layout-content style="margin: 16px">
        <div :style="{ padding: '24px', background: '#fff', minHeight: 'calc(100vh - 160px)' }">
          <!-- Nested routes will render here -->
          <router-view/>
        </div>
      </a-layout-content>
      <a-layout-footer style="text-align: center">
        客车运行故障动态图像检测系统 ©{{ new Date().getFullYear() }} Created by 中南大学
      </a-layout-footer>
    </a-layout>
  </a-layout>
</template>

<style scoped>
.logo {
  height: 80px;
  padding: 16px;
  text-align: center;
  background: white;
}
</style>