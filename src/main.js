import {createApp} from 'vue'
import './style.css'
import App from './App.vue'
// ant-design-vue
import 'ant-design-vue/dist/reset.css';
import Antd from 'ant-design-vue';

// router
import router from "./router.js";

const app = createApp(App)
app.use(Antd)
app.use(router)
app.mount('#app')
