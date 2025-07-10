<template>
  <div class="container">
    <!-- 搜索栏 -->
    <div class="search-bar">
      <input v-model="search.roadId" type="text" placeholder="输入道路编号" class="input" />
      <input v-model="search.startTime" type="date" class="input" />
      <input v-model="search.endTime" type="date" class="input" />
      <button @click="fetchHistory">搜索</button>
    </div>

    <!-- 结果列表 -->
    <div class="result-list">
      <div v-if="records.length === 0" class="no-data">暂无历史记录</div>
      <div v-for="(record, index) in records" :key="index" class="record-card">
        <h3>道路编号：{{ record.roadId }}</h3>
        <p>检测时间：{{ record.time }}</p>
        <p>问题描述：{{ record.description }}</p>
        <video v-if="record.videoUrl" :src="record.videoUrl" controls class="video"></video>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
// import axios from 'axios' // 实际开发中使用 axios 请求后端

// 搜索条件
const search = ref({
  roadId: '',
  startTime: '',
  endTime: '',
});

// 历史记录列表
const records = ref([]);

// 模拟数据库数据
const mockDB = [
  {
    roadId: 'A001',
    time: '2025-07-01',
    description: '检测到轻微裂缝',
    videoUrl: 'https://www.w3schools.com/html/mov_bbb.mp4',
  },
  {
    roadId: 'A002',
    time: '2025-07-05',
    description: '检测到坑洞',
    videoUrl: 'https://www.w3schools.com/html/movie.mp4',
  },
];

// 模拟数据库访问
const fetchHistory = async () => {
  // 模拟延迟
  await new Promise(resolve => setTimeout(resolve, 500));

  const { roadId, startTime, endTime } = search.value;

  // 实际开发应向后端发送搜索条件
  // const res = await axios.get('/api/road/history', { params: { roadId, startTime, endTime } })
  // records.value = res.data;

  records.value = mockDB.filter(record => {
    const matchesRoad = !roadId || record.roadId.includes(roadId);
    const matchesTime =
      (!startTime || record.time >= startTime) &&
      (!endTime || record.time <= endTime);
    return matchesRoad && matchesTime;
  });
};
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

.video {
  width: 100%;
  max-width: 600px;
  margin-top: 10px;
}

.no-data {
  color: #888;
  font-style: italic;
}
</style>
