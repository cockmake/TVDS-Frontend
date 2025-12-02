<script setup>
import {ref, reactive, onMounted, h, nextTick} from "vue";
import {HTTP} from "../../api/service.js";
import {QuestionCircleOutlined, SearchOutlined} from "@ant-design/icons-vue"; // 引入图标
import {message} from 'ant-design-vue';
import router from "../../router.js"; // 引入 message 用于提示

// 表格列定义
const columns = ref([
  {
    title: "任务ID",
    dataIndex: 'id',
    key: 'id',
  },
  {
    title: '行车信息',
    dataIndex: 'vehicleInfo',
    key: 'vehicleInfo',
  },
  {
    title: '创建时间',
    dataIndex: 'createdAt',
    key: 'createdAt',
    sorter: (a, b) => a.createdAt.localeCompare(b.createdAt), // 修正排序比较
    sortDirections: ['descend', 'ascend'],
    width: 180,
  },
  {
    title: '更新时间',
    dataIndex: 'updatedAt',
    key: 'updatedAt',
    sorter: (a, b) => a.updatedAt.localeCompare(b.updatedAt), // 修正排序比较
    sortDirections: ['descend', 'ascend'],
    width: 180,
  },
  {
    title: '任务状态',
    dataIndex: 'taskStatus',
    key: 'taskStatus',
    width: 120,
  },
  {
    title: '操作',
    key: 'action',
    fixed: 'right',
    width: 350, // 调整宽度以容纳按钮
  },
]);

// 响应式状态
const dataSource = ref([]);
const totalData = ref(300);
const loading = ref(false);
const searchParams = reactive({
  currentPage: 1,
  pageSize: 10,
  taskStatus: undefined, // 添加任务状态过滤参数, undefined 表示不过滤
});

// 任务状态显示映射
const taskStatusMap = {
  0: {color: 'grey', text: '未开始'},
  1: {color: 'blue', text: '进行中'},
  2: {color: 'green', text: '已完成'},
  3: {color: 'red', text: '失败'},
};

// 获取任务数据函数
const fetchTasks = () => {
  loading.value = true;
  const payload = {
    currentPage: searchParams.currentPage,
    pageSize: searchParams.pageSize,
  };
  // 只有当 taskStatus 有明确值时才加入请求体
  if (searchParams.taskStatus !== undefined && searchParams.taskStatus !== null && searchParams.taskStatus !== '') {
    payload.taskStatus = searchParams.taskStatus;
  }

  HTTP.post(
      '/detection-task/page',
      payload,
      {
        headers: {
          'Content-Type': 'application/json'
        }
      }
  ).then((res) => {
    // 假设后端返回的数据结构包含 vehicleId
    dataSource.value = res.data.records;
    totalData.value = res.data.total;
  }).finally(() => {
    loading.value = false;
  });
};

// 状态过滤改变处理
const handleStatusFilterChange = () => {
  searchParams.currentPage = 1; // 重置到第一页
  fetchTasks();
};

// 页面变化处理
const onPageChange = (page, pageSize) => {
  searchParams.currentPage = page;
  searchParams.pageSize = pageSize;
  fetchTasks();
};

// 组件挂载后加载数据
onMounted(() => {
  fetchTasks();
});


// 删除任务
const deleteTask = (record) => {
  HTTP.delete(
      `/detection-task/${record.id}`, // 使用任务ID
      {
        headers: {
          'Content-Type': 'application/json'
        }
      },
  ).then(() => {
    fetchTasks(); // 刷新列表
  })
};

// 查看结果 (占位符)
const viewResults = (record) => {
  router.push({
    path: '/detection-result/' + record.id
  });
};

// 重试任务 (占位符)
const retryTask = (record) => {
  console.log("重试任务:", record);
  // 调用后端API重试任务
  HTTP.post(
      `/detection-task/${record.id}/retry`
  ).then(() => {
    fetchTasks(); // 刷新状态
  })
};

</script>

<template>
  <div style="width: 100%">
    <a-table
        :data-source="dataSource"
        :columns="columns"
        :loading="loading"
        bordered
        row-key="id"
        :scroll="{ y: 'calc(100vh - 300px)', x: 1200 }"
        :pagination="false"
    >
      <template #title>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span style="font-size: 20px; font-weight: bold">检测任务管理</span>
          <div style="display: flex; align-items: center; gap: 10px;">
            <span>任务状态:</span>
            <a-select
                v-model:value="searchParams.taskStatus"
                placeholder="全部状态"
                style="width: 150px"
                allow-clear
                @change="handleStatusFilterChange"
            >
              <a-select-option :value="undefined">全部状态</a-select-option>
              <a-select-option v-for="(status, key) in taskStatusMap" :key="key" :value="parseInt(key)">
                {{ status.text }}
              </a-select-option>
            </a-select>
            <!-- 可以保留或添加其他搜索框 -->
            <!-- <a-input placeholder="行车信息搜索..." v-model:value="searchParams.vehicleInfo" style="width: 200px;" /> -->
            <!-- <a-button type="primary" :icon="h(SearchOutlined)" @click="handleStatusFilterChange">搜索</a-button> -->
          </div>
        </div>
      </template>
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'taskStatus'">
          <a-tag
              style="width: 80px; text-align: center;"
              :color="taskStatusMap[record.taskStatus]?.color">
            {{ taskStatusMap[record.taskStatus]?.text || '未知状态' }}
          </a-tag>
        </template>
        <template v-if="column.key === 'action'">
          <div style="display: flex; flex-wrap: nowrap; gap: 8px; justify-content: center;">

            <a-button v-if="record.taskStatus === 2" type="primary" @click="viewResults(record)">查看结果</a-button>
            <a-button v-if="record.taskStatus === 3" @click="retryTask(record)">重试</a-button>
            <a-button v-if="record.taskStatus === 1" loading>
              进行中...
            </a-button>
            <a-popconfirm title="确定删除该任务吗？" ok-text="确定" cancel-text="取消" @confirm="deleteTask(record)">
              <template #icon>
                <question-circle-outlined style="color: red"/>
              </template>
              <a-button danger>删除</a-button>
            </a-popconfirm>
          </div>
        </template>
      </template>
    </a-table>
  </div>
  <!-- 分页 -->
  <div style="text-align: center; width: 100%; margin-top: 15px">
    <a-pagination
        show-quick-jumper
        :total="totalData"
        :current="searchParams.currentPage"
        :page-size="searchParams.pageSize"
        @change="onPageChange"
        show-size-changer
        :page-size-options="['10', '20', '50', '100']"
    />
  </div>

</template>

<style scoped>
/* 可以添加一些自定义样式 */
.ant-table-cell {
  white-space: nowrap; /* 防止单元格内容换行，如果需要的话 */
}
</style>