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
        redirect: '/component-manage', // Default redirect after login or direct access
        children: [
            {
                path: '/component-manage',
                name: '模板管理',
                component: () => import("./pages/ComponentManager/index.vue"),
                meta: {requiresAuth: true} // Mark route as requiring authentication
            },
            {
                path: '/template-edit/:componentId',
                name: '模板编辑',
                component: () => import("./pages/ComponentTemplateImageManager/index.vue"),
                meta: {requiresAuth: true} // Mark route as requiring authentication
            },
            {
                path: '/railway-train-manage',
                name: '铁路任务管理',
                component: () => import("./pages/RailwayVehicleManager/index.vue"),
                meta: {requiresAuth: true} // Mark route as requiring authentication
            }
            // Add other management routes as children here
        ]
    },
    // Optional: Add a 404 page
    // { path: '/:pathMatch(.*)*', name: 'NotFound', component: NotFoundComponent },
];
const router = createRouter({
    history: createWebHashHistory(),
    routes
})

router.beforeEach((to, from, next) => {
    const hide = message.loading('页面加载...', 0);
    next()
    setTimeout(hide, 0);
})

export default router