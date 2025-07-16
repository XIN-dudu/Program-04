import { createApp } from 'vue'
import App from './App.vue'
import router from './router' // 导入路由配置
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'

// 创建Vue应用实例
const app = createApp(App)

// 使用路由插件
app.use(router)
app.use(ElementPlus) 
// 挂载应用到DOM
app.mount('#app')