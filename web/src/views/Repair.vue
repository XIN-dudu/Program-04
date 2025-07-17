<!-- 首页 -->
<template>
  <div class="repair-bg">
    <div class="repair-container">
      <h2 class="repair-title">维修任务</h2>
      <table class="repair-table">
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
              <button class="detail-btn" @click="showDetail(task)">查看详情</button>
              <button class="detail-btn" style="margin-left:8px;" @click="handleViewImages(task)">查看图片</button>
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
            <button class="upload-btn" @click="uploadImage" :disabled="!selectedFiles.length">上传</button>
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
  </div>
  <!-- 图片预览弹窗 -->
  <div v-if="imageDialog" class="modal-mask" @click.self="handleCloseImageDialog">
    <div class="modal-container" style="max-width:700px;">
      <div style="font-size:18px;font-weight:600;margin-bottom:18px;display:flex;justify-content:space-between;align-items:center;">图片预览 <span style="font-size:22px;color:#888;cursor:pointer;" @click="handleCloseImageDialog">×</span></div>
      <div v-if="imageList.length === 0" style="padding: 24px 0; text-align: center; color: #888;">无图片可预览</div>
      <div v-else style="display: flex; flex-wrap: wrap; gap: 12px;">
        <img v-for="(img, idx) in imageList" :key="idx" :src="img" style="max-width: 200px; max-height: 160px; border-radius: 6px; cursor: pointer;" @click="showBigImage(img)" />
      </div>
    </div>
  </div>

  <!-- 单张大图弹窗 -->
  <div v-if="bigImageDialog" class="modal-mask" @click.self="closeBigImage">
    <div class="modal-container" style="max-width:90vw;max-height:90vh;display:flex;flex-direction:column;align-items:center;">
      <span style="align-self:flex-end;font-size:28px;color:#888;cursor:pointer;margin-bottom:8px;" @click="closeBigImage">×</span>
      <img :src="bigImageUrl" style="max-width:80vw;max-height:80vh;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.18);" />
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

// 图片预览弹窗相关（直接用 description 字段）
const imageDialog = ref(false)
const imageList = ref([])
const bigImageDialog = ref(false)
const bigImageUrl = ref('')

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

function handleViewImages(task) {
  if (!task.description || !Array.isArray(task.description)) {
    imageList.value = []
  } else {
    imageList.value = task.description
      .filter(item => item.url && /\.(jpg|jpeg|png|gif)$/i.test(item.url))
      .map(item => {
        let url = item.url.replace(/\\/g, '/')
        if (!url.startsWith('http')) url = `/media/road/${url}`
        return url
      })
  }
  imageDialog.value = true
}
function handleCloseImageDialog() {
  imageDialog.value = false
  imageList.value = []
}
function showBigImage(url) {
  bigImageUrl.value = url
  bigImageDialog.value = true
}
function closeBigImage() {
  bigImageDialog.value = false
  bigImageUrl.value = ''
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
.repair-bg {
  min-height: 100vh;
  background: #f7f8fa;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 40px;
}
.repair-container {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  padding: 28px 28px 18px 28px;
  min-width: 900px;
  max-width: 1200px;
  margin: 0 auto;
}
.repair-title {
  text-align: left;
  font-size: 22px;
  color: #222;
  font-weight: 600;
  margin-bottom: 18px;
  letter-spacing: 1px;
}
.repair-table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: none;
}
.repair-table th, .repair-table td {
  padding: 10px 8px;
  text-align: center;
  border-bottom: 1px solid #ececec;
  font-size: 15px;
}
.repair-table th {
  background: #f5f7fa;
  color: #3a5a8c;
  font-weight: 600;
  letter-spacing: 0.5px;
}
.repair-table tr:last-child td {
  border-bottom: none;
}
.detail-btn {
  background: #fff;
  color: #2476e8;
  border: 1px solid #2476e8;
  border-radius: 4px;
  padding: 5px 14px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
  box-shadow: none;
}
.detail-btn:hover {
  background: #2476e8;
  color: #fff;
}
.upload-btn {
  background: #fff;
  color: #28a745;
  border: 1px solid #28a745;
  border-radius: 4px;
  padding: 4px 12px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  margin-left: 8px;
  transition: background 0.2s, color 0.2s;
  box-shadow: none;
}
.upload-btn:disabled {
  background: #f0f0f0;
  color: #aaa;
  border: 1px solid #ccc;
  cursor: not-allowed;
}
.upload-btn:not(:disabled):hover {
  background: #28a745;
  color: #fff;
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
  margin-right: 8px;
  margin-bottom: 8px;
}
.img-box img {
  max-width: 100%;
  max-height: 60px;
  display: block;
}
.del-btn {
  margin-top: 6px;
  background: #dc3545;
  color: #fff;
  border-radius: 4px;
  font-size: 12px;
  padding: 2px 8px;
  border: none;
  cursor: pointer;
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
</style>