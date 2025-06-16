<script setup>
import {h, nextTick, onMounted, reactive, ref} from "vue";
import {InfoCircleOutlined, PlusOutlined, QuestionCircleOutlined, SearchOutlined} from '@ant-design/icons-vue';
import router from "../../router.js";
import ComponentInfoForm from "./components/ComponentInfoForm.vue";
import {HTTP} from "../../api/service.js";

const dataSource = ref([])
const columns = ref([
  {
    title: '部件名称',
    dataIndex: 'componentName',
    key: 'componentName',
    sorter: (a, b) => a.componentName.localeCompare(b.componentName),
    sortDirections: ['descend', 'ascend'],
  },
  {
    title: '部件车型',
    dataIndex: 'componentType',
    key: 'componentType',
    sorter: (a, b) => a.componentType.localeCompare(b.componentType),
    sortDirections: ['descend', 'ascend'],
  },
  {
    title: "总数",
    dataIndex: "totalCount",
    key: "totalCount",
    sorter: (a, b) => a.totalCount.localeCompare(b.totalCount),
    sortDirections: ['descend', 'ascend'],
  },
  {
    title: '部件备注',
    dataIndex: 'componentDesc',
    key: 'componentDesc',
    ellipsis: true,
  },
  {
    title: '创建时间',
    dataIndex: 'createdAt',
    key: 'createdAt',
    sorter: (a, b) => a.createdAt.localeCompare(b.createdAt),
    sortDirections: ['descend', 'ascend'],
  },
  {
    title: '操作',
    key: 'action',
    fixed: 'right',
    width: 400,
  },
])
const deleteConfirm = (record) => {
  HTTP.delete(
      '/component/' + record.id,
      {
        headers: {
          'Content-Type': 'application/json'
        }
      },
  ).then((res) => {
    searchData()
  })
};
const templateEdit = (record) => {
  router.push(`/template-edit/${record.id}`);
}
const totalData = ref(0)
const searchKey = reactive({
  componentName: '',
  componentType: '',
  currentPage: 1,
  pageSize: 10,
})
const onPageChange = (currentPage, pageNumber) => {
  // 发起请求
  searchKey.currentPage = currentPage;
  searchKey.pageSize = pageNumber;
  searchData()
}
const searchData = () => {
  HTTP.post(
      '/component/page',
      {
        ...searchKey,
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
onMounted(() => {
  // 发起请求
  searchData()
})
const newComponentModal = ref(false)
const updateComponentModal = ref(false)
const editForm = ref()
const updateComponentClick = (record) => {
  updateComponentModal.value = true
  nextTick(() => {
    editForm.value.editSetComponentInfo(record)
  })
}
const previewVisible = ref(false)
const previewImage = ref('')
const visualPromptPreview = (record) => {
  // 方法一
  // previewImage.value = SERVER_API_URL + `/component/${record.id}/visual-prompt/preview`
  // previewVisible.value = true
  // 方法二
  // responseType: 'blob'  // 设置响应类型为blob
  HTTP.get(
      '/component/' + record.id + '/visual-prompt/preview',
      {
        responseType: 'blob'
      },
  ).then((res) => {
    previewImage.value = URL.createObjectURL(res);
    previewVisible.value = true
  })
}
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
          <span style="font-size: 20px; font-weight: bold">TVDS客车零部件视觉模板库</span>
          <div style="display: flex; flex-wrap: nowrap; align-items: center">
            <a-button :icon="h(PlusOutlined)" @click="newComponentModal = true">新建零部件</a-button>
            <a-input v-model:value="searchKey.componentName" placeholder="部件名称" allow-clear>
              <template #suffix>
                <a-tooltip title="部件名称模糊搜索">
                  <info-circle-outlined style="color: rgba(0, 0, 0, 0.45)"/>
                </a-tooltip>
              </template>
            </a-input>
            <a-input v-model:value="searchKey.componentType" placeholder="部件车型" allow-clear>
              <template #suffix>
                <a-tooltip title="部件车型精确搜索">
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
            <a-button @click="templateEdit(record)">模板编辑</a-button>
            <a-divider type="vertical" style="height: 30px"/>
            <a-button @click="visualPromptPreview(record)">预览模板</a-button>
            <a-divider type="vertical" style="height: 30px"/>
            <a-button @click="updateComponentClick(record)">编辑配置</a-button>
            <a-divider type="vertical" style="height: 30px"/>
            <a-popconfirm title="确认删除该零部件模板？" @confirm="deleteConfirm(record)">
              <template #icon>
                <question-circle-outlined style="color: red"/>
              </template>
              <a-button>删除</a-button>
            </a-popconfirm>
          </div>
        </template>
      </template>
      <template #expandedRowRender="{ record }">
        <div style="margin: 0; padding: 0">
          <p>检测置信度：{{ record.detectionConf }}</p>
          <p>检测交并比：{{ record.detectionIou }}</p>
          <p>异常检测文本：{{ record.abnormalityDesc }}</p>
        </div>
      </template>
      <template #expandColumnTitle>
        <span style="color: red; white-space: nowrap">推理配置</span>
      </template>
    </a-table>
  </div>
  <!--  分页-->
  <div style="text-align: center; width: 100%; margin-top: 15px">
    <a-pagination show-quick-jumper :total="totalData" @change="onPageChange"/>
  </div>
  <!--  视觉提示模板预览-->
  <a-modal v-model:open="previewVisible"
           title="视觉提示模板预览"
           :footer="null"
           :mask-closable="false"
           style="width: 640px"
           destroy-on-close>
    <img alt="视觉提示模板" style="width: 100%" :src="previewImage"/>
  </a-modal>
  <!--  编辑零部件信息-->
  <a-modal v-model:open="updateComponentModal"
           :mask-closable="false"
           :footer="null"
           title="修改零部件信息">
    <ComponentInfoForm @after-submit="searchData" @close-modal="() => updateComponentModal = false"
                       operation-type="edit" ref="editForm"/>
  </a-modal>
  <!--  新建部件-->
  <a-modal v-model:open="newComponentModal"
           :mask-closable="false"
           :footer="null"
           destroy-on-close title="新增零部件">
    <ComponentInfoForm @after-submit="searchData" @close-modal="() => newComponentModal = false" operation-type="add"/>
  </a-modal>

</template>

<style scoped>

</style>