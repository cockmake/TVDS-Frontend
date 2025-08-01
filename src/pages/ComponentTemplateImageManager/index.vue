<script setup>
import router from "../../router.js";
import {computed, onMounted, ref} from "vue";
import {PlusOutlined, ArrowLeftOutlined, LeftOutlined, RightOutlined} from '@ant-design/icons-vue';
import {SERVER_API_URL} from "../../consts.js";
import {HTTP} from "../../api/service.js";
import ComponentTemplateImageLabel from "./components/ComponentTemplateImageLabel.vue";
// 获取参数
let componentId = null
let token = ref('')
let uploadAction = ref(SERVER_API_URL + '/component-template-image')

function initImageList() {
  HTTP.get(
      '/component-template-image/' + componentId
  ).then((res) => {
    fileList.value = res.data.map((item) => {
      return {
        uid: item.id,
        name: item.id + '.png',
        status: 'done',
        url: SERVER_API_URL + '/component-template-image' + `/${componentId}/${item.id}`
      }
    })
  })
}

const goBack = () => {
  router.back();
}
onMounted(() => {
  componentId = router.currentRoute.value.params['componentId'];
  token.value = localStorage.getItem("token");
  uploadAction.value += `/${componentId}`;
  initImageList()
})

function getBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onload = () => resolve(reader.result);
    reader.onerror = error => reject(error);
  });
}

const previewVisible = ref(false);
const previewImage = ref('');
const fileList = ref([]);
const handleCancel = () => {
  previewVisible.value = false;
};
const labelModalVisible = ref(false);
const currentImageIndex = ref(0);

const switchToImage = (index) => {
  if (index < 0 || index >= fileList.value.length) {
    return;
  }
  currentImageIndex.value = index;
  const file = fileList.value[index];
  previewImage.value = file.url || file.preview;
  currentTemplateImageId.value = file.uid;
}

const showPreviousImage = () => {
  switchToImage(currentImageIndex.value - 1);
}

const showNextImage = () => {
  switchToImage(currentImageIndex.value + 1);
}

const isFirstImage = computed(() => currentImageIndex.value === 0);
const isLastImage = computed(() => currentImageIndex.value === fileList.value.length - 1);

const handlePreview = async file => {
  if (!file.url && !file.preview) {
    file.preview = await getBase64(file.originFileObj);
  }
  const index = fileList.value.findIndex(item => item.uid === file.uid);
  if (index !== -1) {
    switchToImage(index);
  }
  labelModalVisible.value = true;
};
const handleRemove = (fileStatus) => {


  if (fileStatus.status === 'done') {
    // 弹出对话框确认删除
    // 这里可以使用 Ant Design Vue 的 confirm 对话框
    let confirm = window.confirm('确定要删除这个部件模板吗？');
    if (!confirm) {
      return false;
    }
    HTTP.delete(
        '/component-template-image/' + componentId + '/' + fileStatus.uid,
        {
          headers: {
            'Content-Type': 'application/json'
          }
        },
    ).then((res) => {
      console.log(res)
    })
  }
}
const handleChange = ({file, fileList}) => {
  if (file.status === 'done') {
    // 上传完成
    file.uid = file.response.data.imageIdList[0];
    file.url = SERVER_API_URL + '/component-template-image' + `/${componentId}/${file.uid}`;
  }
}
const labelImgSrc = ref(null)
const currentTemplateImageId = ref('')


const previewVisualPromptVisible = ref(false)
const previewVisualPromptImage = ref('')
const visualPromptPreview = () => {
  HTTP.get(
      '/component/' + componentId + '/visual-prompt/preview',
      {
        responseType: 'blob'
      },
  ).then((res) => {
    previewVisualPromptImage.value = URL.createObjectURL(res);
    previewVisualPromptVisible.value = true
  })
}
</script>

<template>
  <div>
    <a-upload
        multiple
        :headers="{'Token': token}"
        v-model:file-list="fileList"
        :action="uploadAction"
        @remove="handleRemove"
        @change="handleChange"
        list-type="picture-card"
        name="imageFiles"
        accept="image/png, image/jpeg, image/jpg"
        @preview="handlePreview">
      <div>
        <PlusOutlined/>
        <div style="margin-top: 8px">上传部件模板</div>
      </div>
    </a-upload>
    <div style="width: 100%; display: flex; justify-content: flex-end; align-items: center;">
      <a-button @click="visualPromptPreview" type="dashed">预览当前视觉模板</a-button>
    </div>
    <a-modal
        style="min-width: 1500px"
        v-model:open="labelModalVisible"
        title="零部件标注"
        destroy-on-close
        :footer="null">
      <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 10px; gap: 10px;">
        <a-button @click="showPreviousImage" :disabled="isFirstImage">
          <template #icon><LeftOutlined /></template>
          上一张
        </a-button>
        <span>{{ currentImageIndex + 1 }} / {{ fileList.length }}</span>
        <a-button @click="showNextImage" :disabled="isLastImage">
          下一张
          <template #icon><RightOutlined /></template>
        </a-button>
      </div>
      <ComponentTemplateImageLabel
          style="margin-top: 10px; width: 100%"
          :key="previewImage"
          v-if="currentTemplateImageId !== ''"
          :img-src="previewImage"
          :template-image-id="currentTemplateImageId"/>
    </a-modal>


    <!--    预览单张图片-->
    <a-modal
        :open="previewVisible"
        title="绘制视觉提示"
        :footer="null"
        @cancel="handleCancel"
        destroy-on-close>
      <img alt="零部件" style="width: 100%" :src="previewImage"/>
    </a-modal>
    <!--    预览视觉提示模板-->
    <a-modal v-model:open="previewVisualPromptVisible"
             title="视觉提示模板预览"
             :footer="null"
             style="width: 640px"
             destroy-on-close>
      <img alt="视觉提示模板" style="width: 100%" :src="previewVisualPromptImage"/>
    </a-modal>
    <a-float-button
        @click="goBack"
        tooltip="返回"
        :style="{
          right: '35px',
          top: '100px',
        }">
      <template #icon>
        <ArrowLeftOutlined/>
      </template>
    </a-float-button>

  </div>
</template>

<style scoped>
</style>