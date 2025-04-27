<script setup>
import {ref, reactive, h} from 'vue'
import {HTTP} from "../../../api/service.js";
import {InfoCircleOutlined, PlusOutlined, QuestionCircleOutlined, SearchOutlined} from '@ant-design/icons-vue';
import {message, notification} from "ant-design-vue";

const emits = defineEmits(['before-submit', 'after-submit', 'close-modal'])
const props = defineProps({
  operationType: {
    type: String,
    required: true,
    // 只可以选择 ['add', 'edit'] 两项
  }
})
const labelCol = {
  style: {
    width: '100px'
  }
};
const vehicleInfo = reactive({
  vehicleInfo: '',
  vehicleDesc: '',
  imageFile: null
})

const fileList = ref([])

const loading = ref(false)

const handleClose = () => {
  emits('close-modal')
}
const handleSubmit = () => {
  if (props.operationType === 'add') {
    if (!vehicleInfo.imageFile) {
      notification['error']({
        message: '传行车图片未上传',
        description: '请上传行车图片',
        placement: 'topRight',
        duration: 3,
      })
      return
    }
    addVehicle()
  } else if (props.operationType === 'edit') {
    updateVehicle()
  }
}
const beforeUpload = (file) => {
  fileList.value = [...(fileList.value || []), file];
  vehicleInfo.imageFile = file;
  return false
}

const handleRemove = (file) => {
  vehicleInfo.imageFile = null;
}
let vehicleId = null
const setVehicleInfo = (data) => {
  vehicleId = data.id
  vehicleInfo.vehicleInfo = data.vehicleInfo
  vehicleInfo.vehicleDesc = data.vehicleDesc
}
const updateVehicle = () => {
  emits('before-submit')
  loading.value = true
  HTTP.put(
      '/railway-vehicle/' + vehicleId,
      {
        vehicleInfo: vehicleInfo.vehicleInfo,
        vehicleDesc: vehicleInfo.vehicleDesc,
      },
      {
        headers: {
          'Content-Type': 'application/json'
        }
      },
  ).then((res) => {
    // 修改成功了
    emits('after-submit')
    emits('close-modal')
  }).finally(() => {
    loading.value = false
  })
}
const addVehicle = () => {
  emits('before-submit')
  loading.value = true
  const formData = new FormData()
  formData.append('vehicleInfo', vehicleInfo.vehicleInfo)
  formData.append('vehicleDesc', vehicleInfo.vehicleDesc)
  formData.append('imageFile', vehicleInfo.imageFile)
  HTTP.post(
      '/railway-vehicle',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      },
  ).then((res) => {
    // 添加成功了
    emits('after-submit')
    resetForm()
  }).finally(() => {
    loading.value = false
  })
}
const resetForm = () => {
  vehicleInfo.vehicleInfo = ''
  vehicleInfo.vehicleDesc = ''
  vehicleInfo.imageFile = null
  fileList.value = []
}


defineExpose({
  setVehicleInfo
})
</script>

<template>
  <a-form
      :model="vehicleInfo"
      name="vehicleForm"
      :label-col="labelCol"
      layout="horizontal"
      autocomplete="off">
    <a-form-item
        v-if="props.operationType === 'add'"
        required
        label="行车图片"
        name="imageFile">
      <a-upload
          :before-upload="beforeUpload"
          @remove="handleRemove"
          accept="image/png, image/jpg, image/jpeg"
          v-model:file-list="fileList"
          list-type="picture-card">
        <div v-if="fileList.length < 1">
          <plus-outlined/>
          <div style="margin-top: 8px">上传行车图像</div>
        </div>
        <template #previewIcon></template>
      </a-upload>
    </a-form-item>

    <a-form-item
        label="行车信息"
        name="vehicleInfo">
      <a-input v-model:value="vehicleInfo.vehicleInfo" placeholder="请输入行车信息"/>
    </a-form-item>

    <a-form-item
        label="行车备注"
        name="vehicleDesc">
      <a-input v-model:value="vehicleInfo.vehicleDesc" placeholder="请输入行车备注"/>
    </a-form-item>

    <a-form-item>
      <div style="display: flex; justify-content: flex-end; gap: 8px">
        <a-button @click="handleClose">取消</a-button>
        <a-button type="primary" :loading="loading" @click="handleSubmit">确定</a-button>
      </div>
    </a-form-item>


  </a-form>
</template>

<style scoped>

</style>