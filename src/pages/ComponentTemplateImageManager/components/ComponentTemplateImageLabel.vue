<script setup>
import CanvasSelect from "canvas-select";
import {onMounted, ref} from "vue";
import {HTTP} from "../../../api/service.js";

const props = defineProps({
  templateImageId: {
    type: String,
    required: true,
  },
  imgSrc: {
    required: true,
  }
})
let instance = null
let output = ref('')
const option = [];

const getCoors = async () => {
  // 使用 await 等待 HTTP 请求完成
  const res = await HTTP.get('/component-template-image-box/' + props.templateImageId);
  return res.data.coors;
}

onMounted(async () => {
  console.log('画布加载完成')
  instance = new CanvasSelect(
      ".container",
      props.imgSrc
  );
  // 加载方框
  const coors = await getCoors()
  console.log(coors)
  coors.forEach(item => {
    option.push({
      coor: [
        [item[0], item[1]],
        [item[2], item[3]]
      ],
      type: 1
    })
  })
  instance.labelMaxLen = 10;
  instance.setData(option);

  // 图片加载完成
  instance.on("load", (src) => {
    console.log("image loaded", src);
  });
  // 添加
  instance.on("add", (info) => {
    console.log("add", info);
    window.info = info;
  });
  // 删除
  instance.on("delete", (info) => {
    console.log("delete", info);
    window.info = info;
  });
  // 选中
  instance.on("select", (shape) => {
    console.log("select", shape);
    window.shape = shape;
  });

  instance.on("updated", (result) => {
    const list = [...result];
    list.sort((a, b) => a.index - b.index);
    output.value = JSON.stringify(list, null, 2);
  });
})

function change(num) {
  instance.createType = num;
}

function zoom(type) {
  instance.setScale(type);
}

function fitting() {
  instance.fitZoom();
}

function parseDataset(dataset) {
  const coors = [];
  dataset.forEach((item) => {
    const {coor} = item;
    coors.push({
      coor: [coor[0][0], coor[0][1], coor[1][0], coor[1][1]]
    })
  });
  return coors;
}

function onFinish() {
  if (!instance) {
    return;
  }
  const coors = parseDataset(instance.dataset)
  HTTP.put(
      '/component-template-image-box/' + props.templateImageId,
      {
        coors: coors,
      }
  )
}

</script>

<template>
  <div class="box">
    <div class="left">
      <canvas class="container"></canvas>
      <div>
        <a-button @click="change(1)">绘制方框</a-button>
        <a-button @click="change(0)">取消绘制</a-button>
        <a-button @click="zoom(true)">放大</a-button>
        <a-button @click="zoom(false)">缩小</a-button>
        <a-button @click="fitting">自适应</a-button>
        <a-button @click="onFinish">完成标记</a-button>
      </div>
    </div>
    <div class="right">
      <a-textarea
          style="width: 400px"
          v-model:value="output"
          :auto-size="{ minRows: 20, maxRows: 30 }"
      ></a-textarea>
    </div>
    <div class="right">
      <pre>
1.创建矩形时，按住鼠标左键拖动完成创建。

2.按住鼠标右键拖动画布。

3.鼠标滚轮缩放画布。

4.取消绘制后，选中形状，Backspace删除。

5.绘制完成后点击完成标记，保存数据。
      </pre>
    </div>
  </div>
</template>

<style scoped>
.box {
  display: flex;
  flex-wrap: nowrap;
  justify-content: center;
}

.container {
  background-color: #ccc;
  width: 600px;
  height: 600px;
}

.right {
  margin-left: 20px;
}

</style>