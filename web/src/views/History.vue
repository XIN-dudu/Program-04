<template>
  <div class="container">
    <h2>病害记录历史界面</h2>

    <div v-if="records.length === 0" class="no-data">暂无任务记录</div>

    <div
      v-for="(record, index) in records"
      :key="record.disease_id"
      class="record-card"
    >
      <h3>道路编号：{{ record.road_id }}</h3>
      <p><strong>检测时间：</strong>{{ record.detection_date }}</p>
      <p><strong>病害类型：</strong>{{ record.disease_type }}</p>
      <p><strong>严重程度：</strong>{{ record.severity }}</p>

      <template v-if="record.url">
        <img
          v-if="isImageUrl(record.url)"
          :src="getFullUrl(record.url)"
          alt="检测图像"
          class="media"
        />
        <video
          v-else-if="isVideoUrl(record.url)"
          :src="getFullUrl(record.url)"
          controls
          class="media"
        />
        <p v-else class="no-media">⚠️ 不支持的媒体类型</p>
      </template>
      <p v-else class="no-media">无图像信息</p>

      <!-- 管理员和维修工可见 -->
      <button
        v-if="isDeletable"
        class="delete-button"
        @click="deleteRecord(record.disease_id, index)"
      >
        删除记录
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

// 权限判断
const userPermissionRef = ref(localStorage.getItem('permission') || '0')
const isRepairMan = computed(() => userPermissionRef.value === '1')
const isAdmin = computed(() => userPermissionRef.value === '2')

// 删除权限（维修工或管理员）
const isDeletable = computed(() => isRepairMan.value || isAdmin.value)

const backendBaseURL = 'http://localhost:8000'

const records = ref([])

// URL 转换
const getFullUrl = (url) => {
  if (!url) return ''
  const fixedPath = url.replace(/\\/g, '/')
  return fixedPath.startsWith('http') ? fixedPath : backendBaseURL + fixedPath
}

const isImageUrl = (url) => /\.(jpg|jpeg|png|gif|bmp)$/i.test(url)
const isVideoUrl = (url) => /\.(mp4|webm|ogg|avi|mov)$/i.test(url)

// 获取记录
const fetchRecords = async () => {
  try {
    const res = await axios.get(`${backendBaseURL}/api/history/list`, {
      withCredentials: true
    })
    records.value = res.data
  } catch (err) {
    console.error('获取记录失败:', err)
    records.value = []
  }
}

// 删除记录
const deleteRecord = async (diseaseId, index) => {
  if (!confirm('确定要删除这条记录吗？')) return

  try {
    await axios.delete(`${backendBaseURL}/api/history/${diseaseId}/delete`, {
      withCredentials: true
    })
    records.value.splice(index, 1)
  } catch (error) {
    console.error('删除失败:', error)
    alert('删除失败，请稍后重试')
  }
}

onMounted(() => {
  fetchRecords()
})
</script>

<style scoped>
.container {
  padding: 20px;
  max-width: 1000px;
  margin: auto;
  font-family: Arial, sans-serif;
}

h2 {
  margin-bottom: 20px;
}

.no-data {
  font-style: italic;
  color: #666;
}

.record-card {
  background-color: #f9f9f9;
  border-left: 4px solid #007bff;
  padding: 15px;
  border-radius: 6px;
  margin-bottom: 15px;
}

.media {
  width: 100%;
  max-width: 600px;
  margin-top: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.no-media {
  color: #777;
  font-style: italic;
  margin-top: 10px;
}

.delete-button {
  margin-top: 12px;
  padding: 6px 12px;
  background-color: #dc3545;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.delete-button:hover {
  background-color: #b02a37;
}
</style>
