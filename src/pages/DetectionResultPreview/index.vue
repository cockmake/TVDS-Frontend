<script setup>
import {useRoute} from "vue-router";
import {computed, onMounted, ref, watch, reactive, nextTick, onBeforeUnmount} from "vue";
import {HTTP} from "../../api/service.js";

const route = useRoute();
const taskId = route.params.taskId;
const vehicleInfo = reactive({
  vehicleInfo: '',
  createdAt: null,
  updatedAt: null,
  vehicleId: null,
})
const componentTypeList = ref([]);
const selectedComponentId = ref('');
const componentTypeListComputed = computed(() => {
  return componentTypeList.value.map(item => ({
    label: `${item.componentName}（${item.count}）`,
    value: item.componentId,
    key: item.componentId
  }));
});
const detectionResults = ref([]);

// 首次获取所有零部件类型
const getComponentTypes = () => {
  HTTP.get(`/detection-result/${taskId}`)
      .then(res => {
        componentTypeList.value = res.data;
        if (componentTypeList.value.length) {
          selectedComponentId.value = componentTypeList.value[0].componentId;
        }
      });
};

// 根据选中组件获取检测结果
const fetchResults = (componentId) => {
  HTTP.get(`/detection-result/${taskId}/${componentId}`)
      .then(res => {
        detectionResults.value = res.data
        // 获取图像
        detectionResults.value.forEach(item => {
          getImageUrl(item.resultId).then(url => {
            item.imageUrl = url;
          });
        });
      });
};

// 监听分段选择变化
watch(selectedComponentId, id => {
  if (id) fetchResults(id);
});

// 新增 ref
const vehicleImageRef = ref(null);
const canvasRef = ref(null);
const wrapperRef = ref(null);

let resizeObserver;
let hasObserved = false;

onMounted(() => {
  getComponentTypes();
  let record = sessionStorage.getItem('taskInfo');
  if (record) {
    record = JSON.parse(record);
    vehicleInfo.vehicleInfo = record.vehicleInfo;
    vehicleInfo.createdAt = record.createdAt;
    vehicleInfo.updatedAt = record.updatedAt;
    vehicleInfo.vehicleId = record.vehicleId;
  }
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
const previewModalVisible = ref(false);
const previewImageUrl = ref('');

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

    wrapper.scrollLeft = x - wrapper.clientWidth / 2 + w / 2;
    wrapper.scrollTop = y - wrapper.clientHeight / 2 + h / 2;

  })
};

const previewDetectionResult = async (item) => {
  // 单个组件预览暂时不用
  // previewModalVisible.value = true;
  // previewImageUrl.value = item.imageUrl;
  currentItem.value = item
  await previewVehicle(vehicleInfo.vehicleId);
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
  if (!previewVehicleImage.value) {
    const res = await HTTP.get(
        `/railway-vehicle/${vehicleId}/preview`, // 使用模板字符串
        {
          responseType: 'blob'
        },
    )
    previewVehicleImage.value = URL.createObjectURL(res);
  }
  previewVehicleVisible.value = true;
};
</script>

<template>
  <div>
    <a-descriptions title="任务信息" bordered style="margin-bottom: 16px;">
      <a-descriptions-item label="行车信息">
        {{ vehicleInfo.vehicleInfo }}
      </a-descriptions-item>
      <a-descriptions-item label="创建时间">
        {{ vehicleInfo.createdAt }}
      </a-descriptions-item>
      <a-descriptions-item label="更新时间">
        {{ vehicleInfo.updatedAt }}
      </a-descriptions-item>
    </a-descriptions>

    <a-segmented
        v-model:value="selectedComponentId"
        :options="componentTypeListComputed"
        style="margin-bottom: 16px;"/>
    <div style="display: flex; flex-wrap: wrap; gap: 16px;">
      <a-card
          v-for="item in detectionResults"
          :key="item.resultId"
          hoverable
          @click="previewDetectionResult(item)"
          style="width: 240px;">
        <template #cover>
          <div style="height: 160px; text-align: center;">
            <img
                :src="item.imageUrl"
                alt="检测结果图"
                style="height: 100%; object-fit: cover;"/>
          </div>

        </template>
        <a-space direction="vertical" style="margin-top: 8px;">
          <div>置信度：{{ item.detectionConf }}</div>
          <div>
            异常：
            <span :style="{ color: item.isAbnormal ? 'red' : 'inherit' }">
              {{ item.isAbnormal ? '是' : '否' }}
            </span>
          </div>
          <div>坐标：({{ item.x1 }}, {{ item.y1 }}) - ({{ item.x2 }}, {{ item.y2 }})</div>
        </a-space>
      </a-card>
    </div>
  </div>
  <!--    单个组件预览暂时不用-->
  <!--  <a-modal v-model:open="previewModalVisible"-->
  <!--           title="检测部件预览"-->
  <!--           :footer="null"-->
  <!--           :mask-closable="false"-->
  <!--           destroy-on-close>-->
  <!--    <div style="display: flex; justify-content: center; align-items: center; height: 50vh;">-->
  <!--      <img alt="部件预览"-->
  <!--           style="max-width: 100%; max-height: 100%; object-fit: contain;"-->
  <!--           :src="previewImageUrl"/>-->
  <!--    </div>-->
  <!--  </a-modal>-->
  <a-modal v-model:open="previewVehicleVisible"
           title="行车大图预览"
           :footer="null"
           width="70%"
           :mask-closable="false">
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