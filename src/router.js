import {createRouter, createWebHashHistory} from 'vue-router'
import {message} from 'ant-design-vue';
import MainLayout from "./layouts/MainLayout.vue";

export const routes = [
    {
        path: '/login',
        name: '登录',
        component: () => import("./pages/Login/index.vue")
    },
    {
        path: '/', // Main layout route
        component: MainLayout,
        redirect: '/railway-vehicle-manage', // Default redirect after login or direct access
        children: [
            {
                path: '/component-manage',
                name: '视觉模板管理',
                component: () => import("./pages/ComponentManager/index.vue"),
                meta: {requiresAuth: true} // Mark route as requiring authentication
            },
            {
                path: '/template-edit/:componentId',
                name: '视觉模板编辑',
                component: () => import("./pages/ComponentTemplateImageManager/index.vue"),
                meta: {requiresAuth: true} // Mark route as requiring authentication
            },
            {
                path: '/railway-vehicle-manage',
                name: '铁路车辆管理',
                component: () => import("./pages/RailwayVehicleManager/index.vue"),
                meta: {requiresAuth: true} // Mark route as requiring authentication
            },
            {
                path: '/detection-task-manage',
                name: '检测任务管理',
                component: () => import("./pages/DetectionTaskManager/index.vue"),
                meta: {requiresAuth: true} // Mark route as requiring authentication
            },
            {
                path: '/detection-result/:taskId',
                name: '检测结果预览',
                component: () => import("./pages/DetectionResultPreview/index.vue"),
                meta: {requiresAuth: true} // Mark route as requiring authentication
            }
        ]
    },
];
const router = createRouter({
    history: createWebHashHistory(),
    routes
})

router.beforeEach((to, from, next) => {
    const hide = message.loading('页面加载...', 0);
    const isLoggedIn = localStorage.getItem('userLoggedIn') === 'true';
    const requiresAuth = to.matched.some(record => record.meta.requiresAuth);

    if (requiresAuth && !isLoggedIn) {
        // 如果路由需要认证但用户未登录，重定向到登录页
        message.error('请先登录！').then(() => {
        })
        next({path: '/login'});
    } else {
        // 其他情况正常放行
        next();
    }

    // 确保在 next() 调用后隐藏加载提示
    // 使用 setTimeout 确保在 DOM 更新后执行
    setTimeout(hide, 0);
})

export default router