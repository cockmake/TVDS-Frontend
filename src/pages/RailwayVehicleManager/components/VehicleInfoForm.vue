<script setup>
import {ref, reactive, h} from 'vue'
import {HTTP} from "../../../api/service.js";
import {InfoCircleOutlined, PlusOutlined, QuestionCircleOutlined, SearchOutlined} from '@ant-design/icons-vue';
import {message, notification} from "ant-design-vue";
import {DIRECTION_NAME} from "../../../consts.js";

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
  imageFiles: [null, null, null, null, null],
  recordStation: '',
  travelDirection: '',
  vehicleInfo: '',
  vehicleIdentity: '',
  bureau: '',
  section: '',
  vehicleSeq: 1,
  totalSequence: 1,
  vehicleDesc: '',
})

const fileLists = ref([[], [], [], [], []])

const loading = ref(false)

const handleClose = () => {
  emits('close-modal')
}
const handleSubmit = () => {
  if (props.operationType === 'add') {
    const uploadedCount = vehicleInfo.imageFiles.filter(f => f).length;
    if (uploadedCount < 5) {
      notification['error']({
        message: '行车图片未上传完整',
        description: `必须上传5张方位图片，当前已上传 ${uploadedCount} 张。`,
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
// 为指定的上传组件处理文件选择
const beforeUpload = (file, index) => {
  vehicleInfo.imageFiles[index] = file;
  // 手动更新对应上传组件的文件列表
  fileLists.value[index] = [file];
  // 阻止 antd 的默认上传行为
  return false
}

const handleRemove = (index) => {
  vehicleInfo.imageFiles[index] = null;
  fileLists.value[index] = [];
}
let vehicleId = null
const setVehicleInfo = (data) => {
  vehicleId = data.id
  vehicleInfo.recordStation = data.recordStation
  vehicleInfo.travelDirection = data.travelDirection
  vehicleInfo.vehicleInfo = data.vehicleInfo
  vehicleInfo.vehicleIdentity = data.vehicleIdentity
  vehicleInfo.bureau = data.bureau
  vehicleInfo.section = data.section
  vehicleInfo.vehicleDesc = data.vehicleDesc
}
const updateVehicle = () => {
  emits('before-submit')
  loading.value = true
  HTTP.put(
      '/railway-vehicle/' + vehicleId,
      {
        recordStation: vehicleInfo.recordStation,
        travelDirection: vehicleInfo.travelDirection,
        vehicleInfo: vehicleInfo.vehicleInfo,
        vehicleIdentity: vehicleInfo.vehicleIdentity,
        bureau: vehicleInfo.bureau,
        section: vehicleInfo.section,
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
  formData.append('recordStation', vehicleInfo.recordStation)
  formData.append('travelDirection', vehicleInfo.travelDirection)
  formData.append('vehicleInfo', vehicleInfo.vehicleInfo)
  formData.append('vehicleIdentity', vehicleInfo.vehicleIdentity)
  formData.append('bureau', vehicleInfo.bureau)
  formData.append('section', vehicleInfo.section)
  formData.append('vehicleSeq', vehicleInfo.vehicleSeq)
  formData.append('totalSequence', vehicleInfo.totalSequence)
  formData.append('vehicleDesc', vehicleInfo.vehicleDesc)
  // 追加所有5张图片文件。后端应能接收一个文件数组
  vehicleInfo.imageFiles.forEach(file => {
    if (file) {
      formData.append('imageFiles', file)
    }
  })
  HTTP.post(
      '/railway-vehicle',
      formData,
      {
        headers: {
          // 'Content-Type': 'multipart/form-data'
        }
      },
  ).then((res) => {
    // 添加成功了
    emits('after-submit')
    resetForm()
    emits('close-modal')
  }).finally(() => {
    loading.value = false
  })
}
const resetForm = () => {
  vehicleInfo.recordStation = ''
  vehicleInfo.travelDirection = ''
  vehicleInfo.vehicleInfo = ''
  vehicleInfo.vehicleIdentity = ''
  vehicleInfo.bureau = ''
  vehicleInfo.section = ''
  vehicleInfo.vehicleDesc = ''
  vehicleInfo.imageFiles = [null, null, null, null, null]
  fileLists.value = [[], [], [], [], []]
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
        label="行车图片">
      <div style="display: flex; flex-direction: row; flex-wrap: wrap;">
        <div v-for="(index) in 5"
             style="display: flex; flex-direction: column; justify-content: center; align-items: center;  ">
          <span style="white-space: nowrap; margin-bottom: 8px">{{ DIRECTION_NAME[index - 1] }}：</span>
          <div>
            <a-upload
                :before-upload="(file) => beforeUpload(file, index - 1)"
                @remove="handleRemove(index - 1)"
                v-model:file-list="fileLists[index - 1]"
                :max-count="1"
                accept="image/png, image/jpg, image/jpeg"
                list-type="picture-card">
              <div v-if="!fileLists[index - 1] || fileLists[index - 1].length < 1">
                <plus-outlined/>
                <div style="margin-top: 8px">上传图片</div>
              </div>
            </a-upload>
          </div>

        </div>
      </div>
    </a-form-item>
    <a-form-item
        label="探测站"
        name="recordStation">
      <a-input v-model:value="vehicleInfo.recordStation" placeholder="请输入探测站"/>
    </a-form-item>
    <a-form-item
        label="行车方向"
        name="travelDirection">
      <a-input v-model:value="vehicleInfo.travelDirection" placeholder="请输入行车方向"/>
    </a-form-item>
    <a-form-item
        label="车次信息"
        name="vehicleInfo">
      <a-input v-model:value="vehicleInfo.vehicleInfo" placeholder="请输入车次信息"/>
    </a-form-item>
    <a-form-item
        label="车号信息"
        name="vehicleIdentity">
      <a-input v-model:value="vehicleInfo.vehicleIdentity" placeholder="请输入车号信息"/>
    </a-form-item>
    <a-form-item
        label="局信息"
        name="bureau">
      <a-input v-model:value="vehicleInfo.bureau" placeholder="请输入局段信息"/>
    </a-form-item>
    <a-form-item
        label="段信息"
        name="section">
      <a-input v-model:value="vehicleInfo.section" placeholder="请输入车次信息"/>
    </a-form-item>
    <a-form-item
        label="辆序"
        name="vehicleSeq">
      <a-input-number style="width: 100%" v-model:value="vehicleInfo.vehicleSeq" :min="1" placeholder="请输入行车序号"/>
    </a-form-item>
    <a-form-item

        label="总辆数"
        name="totalSequence">
      <a-input-number style="width: 100%" v-model:value="vehicleInfo.totalSequence" :min="1"
                      placeholder="请输入总序号"/>
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