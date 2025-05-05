<script setup>
import {useRoute} from "vue-router";
import {computed, onMounted, ref, watch, reactive} from "vue";
import {HTTP} from "../../api/service.js";

const route = useRoute();
const taskId = route.params.taskId;
const vehicleInfo = reactive({
  vehicleInfo: '',
  createdAt: null,
  updatedAt: null,
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

onMounted(() => {
  getComponentTypes();
  let record = sessionStorage.getItem('taskInfo');
  if (record) {
    record = JSON.parse(record);
    vehicleInfo.vehicleInfo = record.vehicleInfo;
    vehicleInfo.createdAt = record.createdAt;
    vehicleInfo.updatedAt = record.updatedAt;
  }
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
const previewDetectionResult = (item) => {
  previewModalVisible.value = true;
  previewImageUrl.value = item.imageUrl;
};
</script>

<template>
  <div>
    <a-descriptions title="任务信息" bordered column="1" style="margin-bottom: 16px;">
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
        style="margin-bottom: 16px;"
    />
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
  <a-modal v-model:open="previewModalVisible"
           title="检测部件预览"
           :footer="null"
           :mask-closable="false"
           destroy-on-close>
    <div style="overflow: auto; text-align: center; max-height: 500px; max-width: 500px;">
      <img alt="部件预览"
           style="max-height: 100%; max-width: 100%; object-fit: cover; margin: auto; border: 1px solid #eee;"
           :src="previewImageUrl"/>
    </div>
  </a-modal>
</template>

<style scoped>
</style>