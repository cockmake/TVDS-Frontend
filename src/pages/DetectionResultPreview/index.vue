<script setup>
import {useRoute} from "vue-router";
import {computed, onMounted, ref, watch, reactive, nextTick, onBeforeUnmount} from "vue";
import {HTTP} from "../../api/service.js";
import {DIRECTION_NAME} from "../../consts.js";

const route = useRoute();
const taskId = route.params.taskId;

const selectedDirection = ref(0); // 新增：当前选择的方位
const componentTypeList = ref([]);
const selectedComponentId = ref('');
const selectedComponentName = ref('');
const componentTypeListComputed = computed(() => {
  return componentTypeList.value.map(item => ({
    label: `${item.componentName}（${item.count}）`,
    value: item.componentId,
    key: item.componentId
  }));
});
const detectionResults = ref([]);
/*
{
    "resultId": "1934947153232752643",
    "detectionConf": 0.905952,
    "isAbnormal": false,
    "x1": 1131,
    "y1": 599,
    "x2": 2066,
    "y2": 2048,
    "taskCreatedAt": "2025-06-17 20:11:58",
    "taskUpdatedAt": "2025-06-17 20:12:05",
    "vehicleId": "1922625555992150016",
    "vehicleInfo": "A",
    "vehicleDesc": "无",
    "recordStation": "2",
    "vehicleIdentity": "1",
    "travelDirection": "1",
    "bureau": "1",
    "section": "1",
    "vehicleSeq": 1,
    "totalSequence": 1,
    "vehicleCreatedAt": "2025-05-14 20:10:28"
}
*/
const columns = [
  {
    title: '入站时间',
    dataIndex: 'vehicleCreatedAt',
    key: 'vehicleCreatedAt',
    sorter: (a, b) => a.vehicleCreatedAt.localeCompare(b.vehicleCreatedAt),
    sortDirections: ['descend', 'ascend'],
    width: '150px',
  },
  {
    title: '检测时间',
    dataIndex: 'taskUpdatedAt',
    key: 'taskUpdatedAt',
    sorter: (a, b) => a.taskUpdatedAt.localeCompare(b.taskUpdatedAt),
    sortDirections: ['descend', 'ascend'],
    width: '150px',
  },
  {
    title: '车次',
    dataIndex: 'vehicleInfo',
    key: 'vehicleInfo',
    sorter: (a, b) => a.vehicleInfo.localeCompare(b.vehicleInfo),
    sortDirections: ['descend', 'ascend'],
    width: '150px',
  },
  {
    title: '探测站',
    dataIndex: 'recordStation',
    key: 'recordStation',
    sorter: (a, b) => a.recordStation.localeCompare(b.recordStation),
    sortDirections: ['descend', 'ascend'],
    width: '150px',
  },
  {
    title: '担当局',
    dataIndex: 'bureau',
    key: 'bureau',
    sorter: (a, b) => a.bureau.localeCompare(b.bureau),
    sortDirections: ['descend', 'ascend'],
    width: '150px',
  },
  {
    title: "置信度",
    dataIndex: "detectionConf",
    key: "detectionConf",
    customRender: ({text}) => {
      return `${(text * 100).toFixed(2)}%`;
    },
    sorter: (a, b) => a.detectionConf - b.detectionConf,
    sortDirections: ['descend', 'ascend'],
    width: '120px',
  },
  {
    title: '故障情况',
    dataIndex: 'isAbnormal',
    key: 'isAbnormal',
    customRender: ({text}) => {
      return text ? '有故障' : '无故障';
    },
    filters: [
      {text: '有故障', value: true},
      {text: '无故障', value: false}
    ],
    onFilter: (value, record) => record.isAbnormal === value,
    width: '120px',
  },
  {
    title: "部件起始位置",
    dataIndex: "x1",
    key: "x1",
    sorter: (a, b) => a.x1 - b.x1,
    sortDirections: ['descend', 'ascend'],
    width: '150px',
  },
  {
    title: "辆序",
    dataIndex: "vehicleSeq",
    key: "vehicleSeq",
    width: 120
  },
  {
    title: "总辆数",
    dataIndex: "totalSequence",
    key: "totalSequence",
    width: 120
  },
  {
    title: "操作",
    key: 'action',
    fixed: 'right',
    width: 250,
  }
];
// 首次获取所有零部件类型
const totalRecords = ref(0);
const totalAbnormalRecords = ref(0); // 新增：故障记录总数
const getComponentTypes = () => {
  HTTP.get(`/detection-result/${taskId}/${selectedDirection.value}`)
      .then(res => {
        componentTypeList.value = res.data;
        if (componentTypeList.value.length) {
          selectedComponentId.value = componentTypeList.value[0].componentId;
          selectedComponentName.value = componentTypeList.value[0].componentName;
        } else {
          selectedComponentId.value = '';
          selectedComponentName.value = '';
          totalRecords.value = 0;
          totalAbnormalRecords.value = 0;
          detectionResults.value = [];
        }
      });
};
watch(selectedDirection, () => {
  // 需要先重置选中的零部件ID
  selectedComponentId.value = '';
  getComponentTypes();

});
// 监听分段选择变化
watch(selectedComponentId, id => {
  if (id) fetchResults(id);
});
// 根据选中组件获取检测结果
const fetchResults = (componentId) => {
  HTTP.get(`/detection-result/${taskId}/${selectedDirection.value}/${componentId}`)
      .then(res => {
        detectionResults.value = res.data.records || []
        totalRecords.value = detectionResults.value.length
        totalAbnormalRecords.value = detectionResults.value.filter(item => item.isAbnormal).length;
      });
};
// 新增 ref
const vehicleImageRef = ref(null);
const canvasRef = ref(null);
const wrapperRef = ref(null);

let resizeObserver;
let hasObserved = false;

onMounted(() => {
  getComponentTypes();
  resizeObserver = new ResizeObserver(() => {
    drawRectAndScroll();
  });
});
onBeforeUnmount(() => {
  // 断开所有观察
  resizeObserver.disconnect();
});
const getImageUrl = async (resultId) => {
  const res = await HTTP.get(
      `/detection-result/${resultId}/preview`,
      {
        responseType: 'blob',
        notShowLoading: true,
      },
  )
  return URL.createObjectURL(res);
};

const currentItem = ref(null)
const drawRectAndScroll = async () => {
  if (previewVehicleVisible.value === false || !currentItem.value) {
    return;
  }
  const item = currentItem.value;
  const img = vehicleImageRef.value;
  const canvas = canvasRef.value;
  const wrapper = wrapperRef.value;
  // 等待图片加载完成
  // 第一次要等待图片加载完成
  await new Promise((resolve) => {
    if (img.complete) {
      resolve();
    } else {
      img.onload = resolve;
    }
  });

  await nextTick(() => {
    const nw = img.naturalWidth, nh = img.naturalHeight;
    const dw = img.clientWidth, dh = img.clientHeight;
    const sx = dw / nw, sy = dh / nh;

    canvas.width = dw;
    canvas.height = dh;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, dw, dh);
    ctx.strokeStyle = 'lime';
    ctx.lineWidth = 2;

    const x = item.x1 * sx, y = item.y1 * sy;
    const w = (item.x2 - item.x1) * sx, h = (item.y2 - item.y1) * sy;
    ctx.strokeRect(x, y, w, h);

    // wrapper.scrollLeft = x - wrapper.clientWidth / 2 + w / 2;
    // wrapper.scrollTop = y - wrapper.clientHeight / 2 + h / 2;
    // 移动到中心
    wrapper.scrollTo({
      left: x - wrapper.clientWidth / 2 + w / 2,
      top: y - wrapper.clientHeight / 2 + h / 2,
      behavior: 'smooth',
    });

  })
};

const previewDetectionResult = async (item) => {
  currentItem.value = item
  await previewVehicle(item.vehicleId);
  // 监听后会自动触发一次
  if (!hasObserved && wrapperRef.value) {
    resizeObserver.observe(wrapperRef.value);
    hasObserved = true;
  }
};
// 行车预览
const previewVehicleImage = ref('');
const previewVehicleVisible = ref(false);
const previewVehicle = async (vehicleId) => {
  const res = await HTTP.get(
      `/railway-vehicle/${vehicleId}/${selectedDirection.value}/preview`, // 使用模板字符串
      {
        responseType: 'blob'
      },
  )
  if (previewVehicleImage.value) {
    URL.revokeObjectURL(previewVehicleImage.value);
  }
  previewVehicleImage.value = URL.createObjectURL(res);
  previewVehicleVisible.value = true;
};
const selectedDetectionResult = ref(null);
const detailModalVisible = ref(false);
const displayResultDetail = (record) => {
  getImageUrl(record.resultId).then(url => {
    record.imageUrl = url;
    record.componentName = selectedComponentName.value;
    selectedDetectionResult.value = record;
    detailModalVisible.value = true;
  });
};
</script>

<template>
  <div>
    <div style="margin-bottom: 16px;">
      <span style="margin-right: 8px;">车辆方位:</span>
      <a-radio-group v-model:value="selectedDirection" button-style="solid">
        <a-radio-button :value="0">右侧</a-radio-button>
        <a-radio-button :value="1">左侧</a-radio-button>
        <a-radio-button :value="2">底中</a-radio-button>
        <a-radio-button :value="3">底右</a-radio-button>
        <a-radio-button :value="4">底左</a-radio-button>
      </a-radio-group>
    </div>
    <div style="margin-bottom: 16px;">
      <span style="margin-right: 8px;">部件结果:</span>
      <a-segmented
          v-model:value="selectedComponentId"
          :options="componentTypeListComputed"
          style="margin-bottom: 16px;"/>
    </div>

    <div style="display: flex; flex-wrap: wrap; gap: 16px;">
      <a-table :data-source="detectionResults"
               :columns="columns"
               bordered
               row-key="id"
               style="width: 100%"
               :scroll="{ y: 'calc(100vh - 300px)' }"
               :pagination="false">
        <template #title>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span>检测结果查询</span>
            <span>该方位共 <a-tag>{{ totalRecords }}</a-tag> 条检测结果，
              其中故障信息有<a-tag color="red">{{ totalAbnormalRecords }}</a-tag>条</span>
          </div>
        </template>
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'action'">
            <a-space style="width: 100%; justify-content: center;">
              <a-button @click="displayResultDetail(record)">
                查看详情
              </a-button>
              <a-button v-if="record.isAbnormal"
                        danger
                        type="primary">
                上报故障
              </a-button>
            </a-space>
          </template>
          <template v-if="column.key === 'isAbnormal'">
            <a-space style="width: 100%; justify-content: center;">
              <a-tag
                  :color="record.isAbnormal ? 'red' : 'green'"
                  style="width: 100%; text-align: center; line-height: 25px;">
                {{ record.isAbnormal ? '有故障' : '无故障' }}
              </a-tag>
            </a-space>
          </template>
        </template>
      </a-table>
    </div>

  </div>
  <a-modal v-model:open="detailModalVisible"
           :footer="null"
           :z-index="1000"
           destroy-on-close
           width="80%">
    <a-descriptions title="检测结果详情" bordered>
      <a-descriptions-item label="车辆入站时间">
        {{ selectedDetectionResult.vehicleCreatedAt }}
      </a-descriptions-item>
      <a-descriptions-item label="检测发起时间">
        {{ selectedDetectionResult.taskCreatedAt }}
      </a-descriptions-item>
      <a-descriptions-item label="检测完成时间">
        {{ selectedDetectionResult.taskUpdatedAt }}
      </a-descriptions-item>
      <a-descriptions-item label="车次">
        {{ selectedDetectionResult.vehicleInfo }}
      </a-descriptions-item>
      <a-descriptions-item label="车号">
        {{ selectedDetectionResult.vehicleIdentity }}
      </a-descriptions-item>
      <a-descriptions-item label="行驶方向">
        {{ selectedDetectionResult.travelDirection }}
      </a-descriptions-item>
      <a-descriptions-item label="探测站">
        {{ selectedDetectionResult.recordStation }}
      </a-descriptions-item>
      <a-descriptions-item label="担当局">
        {{ selectedDetectionResult.bureau }}
      </a-descriptions-item>
      <a-descriptions-item label="检测置信度">
        {{ (selectedDetectionResult.detectionConf * 100).toFixed(2) }}%
      </a-descriptions-item>
      <a-descriptions-item label="零部件位置">
        ({{ selectedDetectionResult.x1 }}, {{ selectedDetectionResult.y1 }}) -
        ({{ selectedDetectionResult.x2 }}, {{ selectedDetectionResult.y2 }})
      </a-descriptions-item>
      <a-descriptions-item label="故障情况">
        <a-tag :color="selectedDetectionResult.isAbnormal ? 'red' : 'green'">
          {{ selectedDetectionResult.isAbnormal ? '有故障' : '无故障' }}
        </a-tag>
      </a-descriptions-item>
      <a-descriptions-item label="辆序">
        {{ selectedDetectionResult.vehicleSeq }}
      </a-descriptions-item>
      <a-descriptions-item label="总辆数">
        {{ selectedDetectionResult.totalSequence }}
      </a-descriptions-item>
      <a-descriptions-item label="车辆备注">
        {{ selectedDetectionResult.vehicleDesc || '无' }}
      </a-descriptions-item>
      <a-descriptions-item label="部件名称">
        {{ selectedDetectionResult.componentName }}
      </a-descriptions-item>
      <a-descriptions-item label="拍摄方位">
        {{ DIRECTION_NAME[selectedDetectionResult.direction] }}
      </a-descriptions-item>
      <a-descriptions-item label="结果图像">
        <div style="height: 400px; text-align: center;">
          <img
              :src="selectedDetectionResult.imageUrl"
              alt="检测结果图"
              style="height: 100%; object-fit: cover;"/>
          <a-button style="margin-left: 50px" @click="previewDetectionResult(selectedDetectionResult)">
            整体预览
          </a-button>
        </div>
      </a-descriptions-item>
    </a-descriptions>
  </a-modal>
  <a-modal v-model:open="previewVehicleVisible"
           :z-index="1001"
           title="行车大图预览"
           :footer="null"
           width="70%">
    <div ref="wrapperRef"
         style="overflow-x: auto; position: relative;">
      <img ref="vehicleImageRef"
           alt="行车大图"
           :src="previewVehicleImage"
           style="display: block; height: 70vh;"/>
      <canvas ref="canvasRef"
              style="position: absolute; left: 0; top: 0; pointer-events: none;"/>
    </div>
  </a-modal>
</template>

<style scoped>

</style>