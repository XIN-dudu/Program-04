<template>
  <div class="container">
    <!-- 搜索栏 -->
    <div class="search-bar">
      <input v-model="search.roadId" type="text" placeholder="输入道路编号" class="input" />
      <input v-model="search.startTime" type="date" class="input" />
      <input v-model="search.endTime" type="date" class="input" />
      <button @click="fetchHistory">搜索</button>
    </div>

    <!-- 结果展示 -->
    <div class="result-list">
      <div v-if="records.length === 0" class="no-data">暂无历史记录</div>
      <div
        v-for="(record, index) in records"
        :key="index"
        class="record-card"
      >
        <h3>道路编号：{{ record.road_id }}</h3>
        <p><strong>检测时间：</strong>{{ record.detection_date }}</p>
        <p><strong>病害类型：</strong>{{ record.disease_type }}</p>
        <p><strong>严重程度：</strong>{{ record.severity }}</p>

        <!-- 媒体展示：自动区分图片和视频 -->
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
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

// 后端地址（根据实际部署修改）
const backendBaseURL = 'http://localhost:8000'

const search = ref({
  roadId: '',
  startTime: '',
  endTime: '',
})

const records = ref([])

// 转换URL（兼容反斜杠）
const getFullUrl = (url) => {
  if (!url) return ''
  const fixedPath = url.replace(/\\/g, '/')
  return fixedPath.startsWith('http') ? fixedPath : backendBaseURL + fixedPath
}

// 判断是否为图片类型
const isImageUrl = (url) => {
  return /\.(jpg|jpeg|png|gif|bmp)$/i.test(url)
}

// 判断是否为视频类型
const isVideoUrl = (url) => {
  return /\.(mp4|webm|ogg|avi|mov)$/i.test(url)
}

const fetchHistory = async () => {
  try {
    const params = {}
    if (search.value.roadId) params.roadId = search.value.roadId
    if (search.value.startTime) params.startTime = search.value.startTime
    if (search.value.endTime) params.endTime = search.value.endTime

    const res = await axios.get(`${backendBaseURL}/api/history/list`, { params })
    let allRecords = res.data

    // 前端过滤：精准匹配
    if (search.value.roadId) {
      allRecords = allRecords.filter(r => String(r.road_id) === String(search.value.roadId))
    }
    if (search.value.startTime) {
      allRecords = allRecords.filter(r => r.detection_date >= search.value.startTime)
    }
    if (search.value.endTime) {
      allRecords = allRecords.filter(r => r.detection_date <= search.value.endTime)
    }

    records.value = allRecords
  } catch (err) {
    console.error('获取数据失败：', err)
    records.value = []
  }
}

onMounted(() => {
  fetchHistory()
})
</script>

<style scoped>
.container {
  padding: 20px;
  font-family: Arial, sans-serif;
}

.search-bar {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 20px;
}

.input {
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 6px;
  flex: 1;
  min-width: 150px;
}

button {
  padding: 8px 12px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}

button:hover {
  background-color: #0056b3;
}

.result-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.record-card {
  background: #f9f9f9;
  border-left: 4px solid #007bff;
  padding: 15px;
  border-radius: 6px;
}

.media {
  width: 100%;
  max-width: 600px;
  margin-top: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.no-data {
  color: #888;
  font-style: italic;
}

.no-media {
  color: #555;
  font-style: italic;
  margin-top: 10px;
}
</style>
