<script setup>
import {useRoute} from "vue-router";
import {computed, onMounted, ref, watch, nextTick, onBeforeUnmount} from "vue";
import {HTTP} from "../../api/service.js";
import {DIRECTION_NAME} from "../../consts.js";
import {message} from "ant-design-vue";

const route = useRoute();
const taskId = route.params.taskId;

const selectedDirection = ref(0);
const componentTypeList = ref([]);
const selectedComponentId = ref('');
const selectedComponentName = ref('');
const componentTypeListComputed = computed(() =>
    componentTypeList.value.map(item => ({
      label: `${item.componentName}（${item.count}）`,
      value: item.componentId,
      key: item.componentId
    }))
);

const detectionResults = ref([]);
const totalRecords = ref(0);
const totalAbnormalRecords = ref(0);

const columns = [
  { title: '入站时间', dataIndex: 'vehicleCreatedAt', key: 'vehicleCreatedAt',
    sorter: (a,b)=>a.vehicleCreatedAt.localeCompare(b.vehicleCreatedAt), sortDirections:['descend','ascend'], width:'150px'},
  { title: '检测时间', dataIndex: 'taskUpdatedAt', key: 'taskUpdatedAt',
    sorter: (a,b)=>a.taskUpdatedAt.localeCompare(b.taskUpdatedAt), sortDirections:['descend','ascend'], width:'150px'},
  { title: '车次', dataIndex: 'vehicleInfo', key: 'vehicleInfo',
    sorter:(a,b)=>a.vehicleInfo.localeCompare(b.vehicleInfo), sortDirections:['descend','ascend'], width:'150px'},
  { title: '探测站', dataIndex: 'recordStation', key: 'recordStation',
    sorter:(a,b)=>a.recordStation.localeCompare(b.recordStation), sortDirections:['descend','ascend'], width:'150px'},
  { title: '担当局', dataIndex: 'bureau', key: 'bureau',
    sorter:(a,b)=>a.bureau.localeCompare(b.bureau), sortDirections:['descend','ascend'], width:'150px'},
  { title: '置信度', dataIndex: 'detectionConf', key: 'detectionConf',
    customRender:({text})=>`${(text*100).toFixed(2)}%`,
    sorter:(a,b)=>a.detectionConf - b.detectionConf, sortDirections:['descend','ascend'], width:'120px'},
  { title: '故障情况', dataIndex: 'isAbnormal', key: 'isAbnormal',
    customRender:({text})=> text?'有故障':'无故障',
    filters:[{text:'有故障',value:true},{text:'无故障',value:false}],
    onFilter:(v,r)=>r.isAbnormal===v, width:'120px'},
  { title: '故障描述', dataIndex: 'abnormalityDesc', key: 'abnormalityDesc', width:'180px'},
  { title: '部件起始位置', dataIndex: 'x1', key: 'x1',
    sorter:(a,b)=>a.x1-b.x1, sortDirections:['descend','ascend'], width:'150px'},
  { title: '辆序', dataIndex: 'vehicleSeq', key: 'vehicleSeq', width:120},
  { title: '总辆数', dataIndex: 'totalSequence', key: 'totalSequence', width:120},
  { title: '操作', key:'action', fixed:'right', width:250 }
];

const getComponentTypes = () => {
  return HTTP.get(`/detection-result/${taskId}/${selectedDirection.value}`).then(res => {
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
  selectedComponentId.value = '';
  getComponentTypes();
});

watch(selectedComponentId, id => {
  const selectedComponent = componentTypeList.value.find(i => i.componentId === id);
  selectedComponentName.value = selectedComponent ? selectedComponent.componentName : '';
  if (id) fetchResults(id);
});

const fetchResults = (componentId) => {
  return HTTP.get(`/detection-result/${taskId}/${selectedDirection.value}/${componentId}`)
      .then(res => {
        detectionResults.value = res.data.records || [];
        totalRecords.value = detectionResults.value.length;
        totalAbnormalRecords.value = detectionResults.value.filter(i => i.isAbnormal).length;
        currentResultIndex.value = -1;
      });
};

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
  resizeObserver && resizeObserver.disconnect();
  removeKeyListener();
});

const getImageUrl = async (resultId) => {
  const res = await HTTP.get(`/detection-result/${resultId}/preview`, { responseType:'blob', notShowLoading:true });
  return URL.createObjectURL(res);
};

const currentItem = ref(null);
const drawRectAndScroll = async () => {
  if (!previewVehicleVisible.value || !currentItem.value) return;
  const item = currentItem.value;
  const img = vehicleImageRef.value;
  const canvas = canvasRef.value;
  const wrapper = wrapperRef.value;
  await new Promise(resolve => { if (img.complete) resolve(); else img.onload = resolve; });
  await nextTick(() => {
    const nw = img.naturalWidth, nh = img.naturalHeight;
    const dw = img.clientWidth, dh = img.clientHeight;
    const sx = dw / nw, sy = dh / nh;
    canvas.width = dw;
    canvas.height = dh;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0,0,dw,dh);
    ctx.strokeStyle = 'lime';
    ctx.lineWidth = 2;
    const x = item.x1 * sx, y = item.y1 * sy;
    const w = (item.x2 - item.x1) * sx, h = (item.y2 - item.y1) * sy;
    ctx.strokeRect(x,y,w,h);
    wrapper.scrollTo({
      left: x - wrapper.clientWidth / 2 + w / 2,
      top: y - wrapper.clientHeight / 2 + h / 2,
      behavior: 'smooth'
    });
  });
};

const previewVehicleImage = ref('');
const previewVehicleVisible = ref(false);
const previewVehicle = async (vehicleId) => {
  const res = await HTTP.get(
      `/railway-vehicle/${vehicleId}/${selectedDirection.value}/preview`,
      { responseType:'blob' }
  );
  if (previewVehicleImage.value) URL.revokeObjectURL(previewVehicleImage.value);
  previewVehicleImage.value = URL.createObjectURL(res);
  previewVehicleVisible.value = true;
};

const selectedDetectionResult = ref(null);
const detailModalVisible = ref(false);

// 翻页状态
const currentResultIndex = ref(-1);
const isFirstResult = computed(() => currentResultIndex.value <= 0);

// 全局最后一条（方向+部件+结果）
const isLastResult = computed(() => {
  if (!detectionResults.value.length) return true;
  const atLastRecord = currentResultIndex.value >= detectionResults.value.length - 1 && currentResultIndex.value !== -1;
  const compIdx = componentTypeList.value.findIndex(c => c.componentId === selectedComponentId.value);
  const atLastComponent = compIdx !== -1 && compIdx === componentTypeList.value.length - 1;
  const atLastDirection = selectedDirection.value === 4;
  return atLastRecord && atLastComponent && atLastDirection;
});

const openDetailAt = (index) => {
  if (index < 0 || index >= detectionResults.value.length) return;
  currentResultIndex.value = index;
  const record = detectionResults.value[index];
  (record.imageUrl ? Promise.resolve(record.imageUrl) : getImageUrl(record.resultId).then(url => {
    record.imageUrl = url; return url;
  })).then(() => {
    applyDetailRecord(record);
  });
};

const applyDetailRecord = (record) => {
  record.componentName = selectedComponentName.value;
  selectedDetectionResult.value = record;
  detailModalVisible.value = true;
};

const displayResultDetail = (record) => {
  const idx = detectionResults.value.findIndex(r => r.resultId === record.resultId);
  openDetailAt(idx);
};

const waitAndOpenFirst = () => {
  const stop = watch(detectionResults, (list) => {
    if (detailModalVisible.value && list.length > 0) {
      nextTick(() => openDetailAt(0));
      stop();
    }
  }, { immediate: true });
};

// 跨部件 / 方位前进
const advanceToNextScope = () => {
  const compIdx = componentTypeList.value.findIndex(c => c.componentId === selectedComponentId.value);
  // 下一个部件
  if (compIdx !== -1 && compIdx < componentTypeList.value.length - 1) {
    selectedComponentId.value = componentTypeList.value[compIdx + 1].componentId;
    waitAndOpenFirst();
    return;
  }
  // 下一个方位
  if (selectedDirection.value < 4) {
    selectedDirection.value += 1;
    // 等待新的方位加载组件与结果
    const stopComp = watch(componentTypeList, (list) => {
      if (list.length) {
        waitAndOpenFirst();
        stopComp();
      }
    });
    return;
  }
  message.info('已是最后一条结果');
};

const showPrevResult = () => {
  if (currentResultIndex.value > 0) {
    openDetailAt(currentResultIndex.value - 1);
  }
};

const showNextResult = () => {
  // 当前结果还未到当前部件最后
  if (currentResultIndex.value < detectionResults.value.length - 1) {
    openDetailAt(currentResultIndex.value + 1);
    return;
  }
  // 当前部件最后 -> 跨部件/方位
  advanceToNextScope();
};

// 键盘支持 ↑ / ↓
const keyListener = (e) => {
  if (!detailModalVisible.value) return;
  if (e.key === 'ArrowUp') {
    e.preventDefault();
    showPrevResult();
  } else if (e.key === 'ArrowDown') {
    e.preventDefault();
    showNextResult();
  }
};
const addKeyListener = () => window.addEventListener('keydown', keyListener);
const removeKeyListener = () => window.removeEventListener('keydown', keyListener);

watch(detailModalVisible, open => {
  if (open) addKeyListener(); else removeKeyListener();
});

// 预览行车大图并高亮框
const previewDetectionResult = async (item) => {
  currentItem.value = item;
  await previewVehicle(item.vehicleId);
  if (!hasObserved && wrapperRef.value) {
    resizeObserver.observe(wrapperRef.value);
    hasObserved = true;
  }
};
</script>

<template>
  <div>
    <div style="margin-bottom:16px;">
      <span style="margin-right:8px;">车辆方位:</span>
      <a-radio-group v-model:value="selectedDirection" button-style="solid">
        <a-radio-button :value="0">右侧</a-radio-button>
        <a-radio-button :value="1">左侧</a-radio-button>
        <a-radio-button :value="2">底中</a-radio-button>
        <a-radio-button :value="3">底右</a-radio-button>
        <a-radio-button :value="4">底左</a-radio-button>
      </a-radio-group>
    </div>
    <div style="margin-bottom:16px;">
      <span style="margin-right:8px;">部件结果:</span>
      <a-segmented v-model:value="selectedComponentId"
                   :options="componentTypeListComputed"
                   style="margin-bottom:16px;"/>
    </div>

    <div style="display:flex; flex-wrap:wrap; gap:16px;">
      <a-table
          :data-source="detectionResults"
          :columns="columns"
          bordered
          :row-key="record => record.resultId"
          style="width:100%"
          :scroll="{ y: 'calc(100vh - 300px)' }"
          :pagination="false">
        <template #title>
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <span>检测结果查询</span>
            <span>该方位共 <a-tag>{{ totalRecords }}</a-tag> 条检测结果，
              其中故障信息有 <a-tag color="red">{{ totalAbnormalRecords }}</a-tag> 条</span>
          </div>
        </template>
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'action'">
            <a-space style="width:100%; justify-content:center;">
              <a-button @click="displayResultDetail(record)">查看详情</a-button>
              <a-button v-if="record.isAbnormal" danger type="primary">上报故障</a-button>
            </a-space>
          </template>
          <template v-if="column.key === 'isAbnormal'">
            <a-space style="width:100%; justify-content:center;">
              <a-tag :color="record.isAbnormal ? 'red':'green'" style="width:100%; text-align:center; line-height:25px;">
                {{ record.isAbnormal ? '有故障':'无故障' }}
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
           style="top:5vh; width:80%">
    <template #title>
      <div style="display:flex; align-items:center; gap:8px;">
        <a-button size="small" @click="showPrevResult" :disabled="isFirstResult">上一条 ↑</a-button>
        <a-button size="small" @click="showNextResult" :disabled="isLastResult">下一条 ↓</a-button>
        <span style="margin-left:4px;">检测结果详情 ({{ currentResultIndex + 1 }}/{{ detectionResults.length }})</span>
      </div>
    </template>
    <a-descriptions
        v-if="selectedDetectionResult"
        :column="{ xxl:4, xl:3, lg:3, md:3, sm:2, xs:1 }"
        bordered
        style="height:100%; overflow-y:auto;">
      <a-descriptions-item label="车辆入站时间">{{ selectedDetectionResult.vehicleCreatedAt }}</a-descriptions-item>
      <a-descriptions-item label="检测发起时间">{{ selectedDetectionResult.taskCreatedAt }}</a-descriptions-item>
      <a-descriptions-item label="检测完成时间">{{ selectedDetectionResult.taskUpdatedAt }}</a-descriptions-item>
      <a-descriptions-item label="车次">{{ selectedDetectionResult.vehicleInfo }}</a-descriptions-item>
      <a-descriptions-item label="车号">{{ selectedDetectionResult.vehicleIdentity }}</a-descriptions-item>
      <a-descriptions-item label="行驶方向">{{ selectedDetectionResult.travelDirection }}</a-descriptions-item>
      <a-descriptions-item label="探测站">{{ selectedDetectionResult.recordStation }}</a-descriptions-item>
      <a-descriptions-item label="担当局">{{ selectedDetectionResult.bureau }}</a-descriptions-item>
      <a-descriptions-item label="检测置信度">{{ (selectedDetectionResult.detectionConf * 100).toFixed(2) }}%</a-descriptions-item>
      <a-descriptions-item label="零部件位置">
        ({{ selectedDetectionResult.x1 }}, {{ selectedDetectionResult.y1 }}) -
        ({{ selectedDetectionResult.x2 }}, {{ selectedDetectionResult.y2 }})
      </a-descriptions-item>
      <a-descriptions-item label="故障情况">
        <a-tag :color="selectedDetectionResult.isAbnormal ? 'red':'green'">
          {{ selectedDetectionResult.isAbnormal ? '有故障':'无故障' }}
        </a-tag>
      </a-descriptions-item>
      <a-descriptions-item label="辆序">{{ selectedDetectionResult.vehicleSeq }}</a-descriptions-item>
      <a-descriptions-item label="总辆数">{{ selectedDetectionResult.totalSequence }}</a-descriptions-item>
      <a-descriptions-item label="车辆备注">{{ selectedDetectionResult.vehicleDesc || '无' }}</a-descriptions-item>
      <a-descriptions-item label="部件名称">{{ selectedComponentName }}</a-descriptions-item>
      <a-descriptions-item label="拍摄方位">{{ DIRECTION_NAME[selectedDetectionResult.direction] }}</a-descriptions-item>
      <a-descriptions-item label="异常描述">{{ selectedDetectionResult.abnormalityDesc || '无' }}</a-descriptions-item>
      <a-descriptions-item label="结果图像">
        <div style="height:400px; text-align:center;">
          <img :src="selectedDetectionResult.imageUrl"
               alt="检测结果图"
               style="height:100%; object-fit:cover;"/>
          <a-button style="margin-left:50px"
                    @click="previewDetectionResult(selectedDetectionResult)">
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
    <div ref="wrapperRef" style="overflow-x:auto; position:relative;">
      <img ref="vehicleImageRef"
           alt="行车大图"
           :src="previewVehicleImage"
           style="display:block; height:70vh;"/>
      <canvas ref="canvasRef"
              style="position:absolute; left:0; top:0; pointer-events:none;"/>
    </div>
  </a-modal>
</template>

<style scoped>
</style>
