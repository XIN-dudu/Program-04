<!-- 首页 -->
<template>
  <div class="container">
    <h2>你的任务</h2>
    <table>
      <thead>
        <tr>
          <th>道路编号</th>
          <th>病害类型</th>
          <th>严重程度</th>
          <th>状态</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="task in tasks" :key="task.disease_id">
          <td>{{ task.road_id }}</td>
          <td>{{ task.disease_type }}</td>
          <td>{{ task.severity }}</td>
          <td>{{ getTaskStatus(task) }}</td>
          <td>
            <button @click="showDetail(task)">查看详情</button>
          </td>
        </tr>
      </tbody>
    </table>
    <!-- 详情弹窗 -->
    <div v-if="detailVisible" class="modal-mask">
      <div class="modal-container">
        <h3>任务详情</h3>
        <div class="detail-row"><b>道路编号：</b>{{ currentTask.road_id }}</div>
        <div class="detail-row"><b>病害类型：</b>{{ currentTask.disease_type }}</div>
        <div class="detail-row"><b>严重程度：</b>{{ currentTask.severity }}</div>
        <div class="detail-row">
          <label>上传维修完成图片：</label>
          <input type="file" @change="handleFileChange" accept="image/*" multiple />
          <button @click="uploadImage" :disabled="!selectedFiles.length">上传</button>
        </div>
        <div v-if="uploadMsg" :style="{color: uploadSuccess ? 'green' : 'red', margin:'8px 0'}">{{ uploadMsg }}</div>
        <div class="uploaded-images" v-if="uploadedImageUrls.length">
          <div v-for="(url, idx) in uploadedImageUrls" :key="url" class="img-box">
            <img :src="url" alt="维修图片" />
            <button class="del-btn" @click="deleteImage(idx)">删除</button>
          </div>
        </div>
        <button v-if="uploadedImageUrls.length" @click="markTaskFinished" style="margin-top:12px;background:#28a745;">认证完成</button>
        <button @click="detailVisible=false" style="margin-top:20px;">关闭</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const tasks = ref([])
const detailVisible = ref(false)
const currentTask = ref({})
const selectedFiles = ref([])
const uploadMsg = ref('')
const uploadSuccess = ref(false)
const uploadedImageUrls = ref([])
const uploadedImageIds = ref([])

async function loadTasks() {
  const res = await axios.get('/api/my_tasks/', { withCredentials: true })
  tasks.value = res.data
}

async function loadImages(task) {
  try {
    const res = await axios.get(`/api/tasks/${task.disease_id}/images/`, { withCredentials: true })
    uploadedImageUrls.value = res.data.image_urls || []
    uploadedImageIds.value = res.data.image_ids || []
  } catch {
    uploadedImageUrls.value = []
    uploadedImageIds.value = []
  }
}

function showDetail(task) {
  currentTask.value = task
  detailVisible.value = true
  selectedFiles.value = []
  uploadMsg.value = ''
  uploadSuccess.value = false
  uploadedImageUrls.value = []
  uploadedImageIds.value = []
  loadImages(task)
}

function handleFileChange(e) {
  selectedFiles.value = Array.from(e.target.files)
}

async function uploadImage() {
  if (!selectedFiles.value.length) return
  const formData = new FormData()
  selectedFiles.value.forEach(file => formData.append('file', file))
  try {
    const res = await axios.post(`/api/tasks/${currentTask.value.disease_id}/complete/`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      withCredentials: true
    })
    uploadMsg.value = '上传成功'
    uploadSuccess.value = true
    uploadedImageUrls.value = res.data.image_urls || []
    loadImages(currentTask.value)
    selectedFiles.value = []
  } catch (e) {
    uploadMsg.value = '上传失败'
    uploadSuccess.value = false
  }
}

async function deleteImage(idx) {
  const imageId = uploadedImageIds.value[idx]
  if (!imageId) return
  try {
    const res = await axios.post(`/api/tasks/image/${imageId}/delete/`, {}, { withCredentials: true })
    uploadMsg.value = '删除成功'
    uploadedImageUrls.value = res.data.image_urls || []
    loadImages(currentTask.value)
  } catch (e) {
    uploadMsg.value = '删除失败'
  }
}

async function markTaskFinished() {
  try {
    await axios.post(`/api/tasks/${currentTask.value.disease_id}/mark_finished/`, {}, { withCredentials: true })
    uploadMsg.value = '任务已认证完成！'
    uploadSuccess.value = true
    loadTasks()
  } catch (e) {
    uploadMsg.value = '认证失败'
    uploadSuccess.value = false
  }
}

function getTaskStatus(task) {
  // 只看当前用户的分配状态
  // 假设后端 RoadRecordSerializer 返回了当前用户的分配状态字段 assignment_status
  if (task.assignment_status === 'finished') return '已认证';
  return '待认证';
}

onMounted(loadTasks)
</script>

<style scoped>
.container {
  max-width: 1200px;
  margin: 30px auto;
  padding: 20px;
  background: #fefefe;
  border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}
h2 {
  text-align: center;
  margin-bottom: 20px;
}
table {
  width: 100%;
  border-collapse: collapse;
  background: white;
}
th, td {
  border: 1px solid #ddd;
  padding: 10px;
  text-align: center;
}
th {
  background-color: #f0f0f0;
}
button {
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  background-color: #007bff;
  color: white;
  cursor: pointer;
  font-size: 14px;
}
button:disabled {
  background-color: #999;
  cursor: not-allowed;
}
.del-btn {
  margin-top: 6px;
  background: #dc3545;
  color: #fff;
  border-radius: 4px;
  font-size: 12px;
  padding: 2px 8px;
}
.modal-mask {
  position: fixed; left: 0; top: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center;
  z-index: 1000;
}
.modal-container {
  background: #fff; padding: 30px; border-radius: 10px; min-width: 350px; max-width: 420px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.15);
}
.detail-row {
  margin-bottom: 12px;
  font-size: 16px;
}
.uploaded-images {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin: 12px 0 0 0;
}
.img-box {
  width: 90px;
  height: 90px;
  border: 1.5px solid #eee;
  border-radius: 8px;
  overflow: hidden;
  background: #fafbfc;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.img-box img {
  max-width: 100%;
  max-height: 60px;
  display: block;
}
</style>