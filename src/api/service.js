// 封装axios
// 后端返回的格式是{code: 200, message: 'success', data: []}
// 简单做code校验和只返回data
import axios from 'axios';
import {SERVER_API_URL} from "../consts.js";
import {notification} from 'ant-design-vue';
import {message} from 'ant-design-vue';

const HTTP = axios.create({
    baseURL: SERVER_API_URL
});


// 添加请求拦截器
HTTP.interceptors.request.use(config => {
    // 在发送请求之前做些什么
    const notShowLoading = config.notShowLoading;
    if (notShowLoading) {
        delete config.notShowLoading;
    } else {
        message.info({
            content: '请求中...',
            duration: 1
        }).then(() => {

        })
    }
    return config;
}, error => {
    // 对请求错误做些什么
    return Promise.reject(error);
});
// 添加响应拦截器
HTTP.interceptors.response.use((response) => {
    // 对响应数据做点什么
    if (response.status === 200) {
        if (!(response.data instanceof Blob)) {
            message.success({
                content: '请求成功',
                duration: 1
            }).then(() => {

            })
        }
        return response.data;
    } else {
        return Promise.reject(response);
    }
}, async (error) => {
    // 对响应错误做点什么
    // 服务器返回了错误状态码
    const responseData = error.response.data;
    if (responseData instanceof Blob) {
        const errorText = await responseData.text(); // 异步读取 Blob 内容
        const errorJson = JSON.parse(errorText); // 解析为 JSON
        responseData.message = responseData.message || errorJson.message || '操作失败';
        responseData.data = responseData.data || errorJson.data || {}; // 假设错误详情在 data 字段
    }
    const message = responseData.message
    const errors = responseData.data
    for (const key in errors) {
        notification['error']({
            message: message,
            description: errors[key],
            duration: 3
        })
    }
    return Promise.reject(error);
});

export {HTTP};

