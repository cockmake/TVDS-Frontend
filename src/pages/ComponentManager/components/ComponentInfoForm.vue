<script setup>
import {ref, reactive, h} from 'vue'
import {HTTP} from "../../../api/service.js";

const props = defineProps({
  operationType: {
    type: String,
    required: true,
    // 只可以选择 ['add', 'edit'] 两项
  }
})

const emits = defineEmits(['before-submit', 'after-submit', 'close-modal'])
const componentInfo = reactive({
  componentName: '',
  componentType: '默认',
  componentDesc: '',
  detectionIou: 0.1,
  detectionConf: 0.1,
  abnormalityDesc: '',
})
let componentId = null
const editSetComponentInfo = (data) => {
  componentId = data.id
  componentInfo.componentName = data.componentName
  componentInfo.componentType = data.componentType
  componentInfo.componentDesc = data.componentDesc
  componentInfo.detectionIou = data.detectionIou
  componentInfo.detectionConf = data.detectionConf
  componentInfo.abnormalityDesc = data.abnormalityDesc
}
const resetForm = () => {
  componentInfo.componentName = ''
  componentInfo.componentType = '默认'
  componentInfo.componentDesc = ''
  componentInfo.detectionIou = 0.1
  componentInfo.detectionConf = 0.1
  componentInfo.abnormalityDesc = ''
}
const loading = ref(false)
const updateComponent = () => {
  HTTP.put(
      '/component/' + componentId,
      {
        ...componentInfo
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
const addComponent = () => {
  HTTP.post(
      '/component',
      {
        ...componentInfo
      },
      {
        headers: {
          'Content-Type': 'application/json'
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
const handleSubmit = () => {
  emits('before-submit')
  loading.value = true
  if (props.operationType === 'add') {
    addComponent()
  } else if (props.operationType === 'edit') {
    updateComponent()
  }
}
const handleClose = () => {
  emits('close-modal')
}
const labelCol = {
  style: {
    width: '100px'
  }
};

defineExpose({
  editSetComponentInfo
})
</script>

<template>
  <a-form
      :model="componentInfo"
      name="componentForm"
      :label-col="labelCol"
      layout="horizontal"
      autocomplete="off">
    <a-form-item
        label="部件名称"
        name="componentName"
        required>
      <a-input v-model:value="componentInfo.componentName" placeholder="请输入部件名称"/>
    </a-form-item>

    <a-form-item
        label="部件车型"
        name="componentType">
      <a-input v-model:value="componentInfo.componentType" placeholder="请输入部件车型"/>
    </a-form-item>

    <a-form-item
        label="部件备注"
        name="componentDesc">
      <a-textarea v-model:value="componentInfo.componentDesc" placeholder="请输入部件备注" :auto-size="{ minRows: 3, maxRows: 5 }"/>
    </a-form-item>

    <a-form-item
        label="检测置信度"
        name="detectionConf">
      <a-input-number v-model:value="componentInfo.detectionConf" :min="0" :max="1" :step="0.01" style="width: 100%"/>
    </a-form-item>

    <a-form-item
        label="检测交并比"
        name="detectionIou">
      <a-input-number v-model:value="componentInfo.detectionIou" :min="0" :max="1" :step="0.01" style="width: 100%"/>
    </a-form-item>

    <a-form-item
        label="异常检测文本"
        name="abnormalityDesc">
      <a-textarea v-model:value="componentInfo.abnormalityDesc" placeholder="请输入异常检测文本" :auto-size="{ minRows: 3, maxRows: 10 }"/>
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