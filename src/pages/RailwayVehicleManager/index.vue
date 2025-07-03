<script setup>
import {h, nextTick, onMounted, reactive, ref} from "vue";
import {InfoCircleOutlined, PlusOutlined, QuestionCircleOutlined, SearchOutlined} from "@ant-design/icons-vue";
import VehicleInfoForm from "./components/VehicleInfoForm.vue";
import {HTTP} from "../../api/service.js";
import router from "../../router.js";

const columns = ref([
  {
    title: '入站时间',
    dataIndex: 'createdAt',
    key: 'createdAt',
    sorter: (a, b) => a.createdAt.localeCompare(b.createdAt),
    sortDirections: ['descend', 'ascend'],
    width: 180
  },
  {
    title: "探测站",
    dataIndex: "recordStation",
    key: "recordStation",
    sorter: (a, b) => a.recordStation.localeCompare(b.recordStation),
    sortDirections: ['descend', 'ascend'],
    width: 160
  },
  {
    title: "行车方向",
    dataIndex: "travelDirection",
    key: "travelDirection",
    sorter: (a, b) => a.travelDirection.localeCompare(b.travelDirection),
    sortDirections: ['descend', 'ascend'],
    width: 120
  },
  {
    title: '车次信息',
    dataIndex: 'vehicleInfo',
    key: 'vehicleInfo',
    sorter: (a, b) => a.vehicleInfo.localeCompare(b.vehicleInfo),
    sortDirections: ['descend', 'ascend'],
    width: 120
  },
  {
    title: "车号信息",
    dataIndex: "vehicleIdentity",
    key: "vehicleIdentity",
    sorter: (a, b) => a.vehicleIdentity.localeCompare(b.vehicleIdentity),
    sortDirections: ['descend', 'ascend'],
    width: 120
  },
  {
    title: "担当局",
    dataIndex: "bureau",
    key: "bureau",
    sorter: (a, b) => a.bureau.localeCompare(b.bureau),
    sortDirections: ['descend', 'ascend'],
    width: 150
  },
  {
    title: "当担段",
    dataIndex: "section",
    key: "section",
    sorter: (a, b) => a.section.localeCompare(b.section),
    sortDirections: ['descend', 'ascend'],
    width: 150
  },
  {
    title: '客车备注',
    dataIndex: 'vehicleDesc',
    key: 'vehicleDesc',
    ellipsis: true,
    width: 100
  },
  {
    title: '辆序',
    dataIndex: 'vehicleSeq',
    key: 'vehicleSeq',
    width: 80
  },
  {
    title: '总辆数',
    dataIndex: 'totalSequence',
    key: 'totalSequence',
    width: 80
  },
  {
    title: '操作',
    key: 'action',
    fixed: 'right',
    width: 400,
  },
])
onMounted(() => {
  searchData()
})
const totalData = ref(300)
const dataSource = ref([])
const searchKey = reactive({
  vehicleInfo: '',
  vehicleDesc: '',
  currentPage: 1,
  pageSize: 10,
})

const onPageChange = (currentPage, pageNumber) => {
  // 发起请求
  searchKey.currentPage = currentPage;
  searchKey.pageSize = pageNumber;
  searchData()
}

const newVehicleModal = ref(false)

const searchData = () => {
  HTTP.post(
      '/railway-vehicle/page',
      {
        ...searchKey
      },
      {
        headers: {
          'Content-Type': 'application/json'
        }
      },
  ).then((res) => {
    dataSource.value = res.data.records
    totalData.value = res.data.total
  })
}
const editForm = ref()
const updateVehicleClick = (record) => {
  updateVehicleModal.value = true
  nextTick(() => {
    editForm.value.setVehicleInfo(record)
  })
}
const deleteConfirm = (record) => {
  HTTP.delete(
      '/railway-vehicle/' + record.id,
      {
        headers: {
          'Content-Type': 'application/json'
        }
      },
  ).then(() => {
    searchData()
  })
}
const execDetectionTask = (record) => {
  HTTP.post(
      `/detection-task/exec/${record.id}`,
      {
        headers: {
          'Content-Type': 'application/json'
        }
      },
  )
}
const updateVehicleModal = ref(false)
const previewVehicleVisible = ref(false)
const previewVehicleImage = ref('')
const previewDirection = ref(1)
const currentPreviewRecordId = ref(null)

const fetchPreviewImage = () => {
  if (!currentPreviewRecordId.value) return;
  HTTP.get(
      `/railway-vehicle/${currentPreviewRecordId.value}/${previewDirection.value}/preview`,
      {
        responseType: 'blob'
      },
  ).then((res) => {
    if (previewVehicleImage.value) {
      URL.revokeObjectURL(previewVehicleImage.value);
    }
    previewVehicleImage.value = URL.createObjectURL(res);
  })
}
const previewVehicle = (record) => {
  currentPreviewRecordId.value = record.id;
  previewDirection.value = 1; // 默认选择第一个方位
  fetchPreviewImage(); // 获取默认方位的图片
  previewVehicleVisible.value = true;
}
const handlePreviewDirectionChange = () => {
  fetchPreviewImage(); // 切换方位时重新获取图片
}
const handlePreviewClose = () => {
  if (previewVehicleImage.value) {
    URL.revokeObjectURL(previewVehicleImage.value);
    previewVehicleImage.value = '';
  }
  currentPreviewRecordId.value = null;
}
const viewResults = (record) => {
  router.push({
    path: '/detection-result/' + record.taskItem.taskId
  });
};
</script>

<template>
  <div style="width: 100%">
    <a-table :data-source="dataSource"
             :columns="columns"
             bordered
             row-key="id"
             :scroll="{ y: 'calc(100vh - 300px)' }"
             :expand-column-width="85"
             :pagination="false">
      <template #title>
        <div style="display: flex; justify-content: space-between">
          <span style="font-size: 20px; font-weight: bold">TVDS行车入站信息</span>
          <div style="display: flex; flex-wrap: nowrap; align-items: center">
            <a-button :icon="h(PlusOutlined)" @click="newVehicleModal = true">客车入站</a-button>
            <a-input v-model:value="searchKey.vehicleInfo" placeholder="行车信息" allow-clear>
              <template #suffix>
                <a-tooltip title="行车信息精准搜索">
                  <info-circle-outlined style="color: rgba(0, 0, 0, 0.45)"/>
                </a-tooltip>
              </template>
            </a-input>
            <a-input v-model:value="searchKey.vehicleDesc" placeholder="行车备注" allow-clear>
              <template #suffix>
                <a-tooltip title="行车备注模糊搜索">
                  <info-circle-outlined style="color: rgba(0, 0, 0, 0.45)"/>
                </a-tooltip>
              </template>
            </a-input>
            <a-button type="primary" :icon="h(SearchOutlined)" @click="searchData">搜索</a-button>
          </div>
        </div>
      </template>
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'action'">
          <div
              style="display: flex; flex-direction: row; flex-wrap: nowrap; justify-content: center; align-items: center;">
            <a-button @click="previewVehicle(record)" style="margin-right: 5px">行车预览</a-button>
            <!--            <a-divider type="vertical" style="height: 30px"/>-->
            <!--            <a-button @click="updateVehicleClick(record)">编辑信息</a-button>-->
            <!--            <a-divider type="vertical" style="height: 30px"/>-->
            <!--            <a-popconfirm title="删除该行车？" @confirm="deleteConfirm(record)">-->
            <!--              <template #icon>-->
            <!--                <question-circle-outlined style="color: red"/>-->
            <!--              </template>-->
            <!--              <a-button>删除</a-button>-->
            <!--            </a-popconfirm>-->
            <a-button style="margin-right: 5px" v-if="record.taskItem === null" @click="execDetectionTask(record)">开始检测</a-button>
            <div v-else>
              <a-button style="margin-right: 5px" @click="execDetectionTask(record)">再次检测</a-button>
              <a-button style="margin-right: 5px" v-if="record.taskItem.taskStatus === 1" type="primary" loading>进行中</a-button>
              <a-button style="margin-right: 5px" v-else-if="record.taskItem.taskStatus === 2" type="primary" @click="viewResults(record)">查看结果</a-button>
              <a-button style="margin-right: 5px" v-else-if="record.taskItem.taskStatus === 3" type="primary" danger>检测失败</a-button>
            </div>

          </div>
        </template>
      </template>
    </a-table>
  </div>
  <!--  分页-->
  <div style="text-align: center; width: 100%; margin-top: 15px">
    <a-pagination show-quick-jumper :total="totalData" @change="onPageChange"/>
  </div>
  <!--  行车大图预览-->
  <!--  行车大图预览-->
  <a-modal v-model:open="previewVehicleVisible"
           title="行车大图预览"
           :footer="null"
           width="70%"
           :mask-closable="false"
           destroy-on-close
           @after-close="handlePreviewClose">
    <div style="text-align: center; margin-bottom: 16px;">
      <a-radio-group v-model:value="previewDirection" @change="handlePreviewDirectionChange" button-style="solid">
        <a-radio-button :value="0">方位1</a-radio-button>
        <a-radio-button :value="1">方位2</a-radio-button>
        <a-radio-button :value="2">方位3</a-radio-button>
        <a-radio-button :value="3">方位4</a-radio-button>
        <a-radio-button :value="4">方位5</a-radio-button>
      </a-radio-group>
    </div>
    <div style="overflow-x: auto">
      <img alt="行车大图"
           :src="previewVehicleImage"
           style="height: 70vh; display: block; margin: auto; border: 1px solid #eee;"/>
    </div>
  </a-modal>
  <!--  编辑行车信息-->
  <a-modal v-model:open="updateVehicleModal"
           :mask-closable="false"
           :footer="null"
           title="修改行车信息">
    <VehicleInfoForm @after-submit="searchData" @close-modal="() => updateVehicleModal = false"
                     operation-type="edit" ref="editForm"/>
  </a-modal>
  <!--  新建行车信息-->
  <a-modal v-model:open="newVehicleModal"
           :mask-closable="false"
           :footer="null"
           style="top: 10px"
           destroy-on-close title="新增行车信息">
    <VehicleInfoForm @after-submit="searchData" @close-modal="() => newVehicleModal = false" operation-type="add"/>
  </a-modal>
</template>

<style scoped>

</style>