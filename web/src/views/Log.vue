<template>
  <div class="log-viewer">
    <!-- 筛选表单 -->
    <div class="filter-form">
      <label>
        日志级别：
        <select v-model="filters.level">
          <option value="">全部</option>
          <option value="info">Info</option>
          <option value="warning">Warning</option>
          <option value="error">Error</option>
        </select>
      </label>

      <label>
        开始时间：
        <input type="date" v-model="filters.start_date" />
      </label>

      <label>
        结束时间：
        <input type="date" v-model="filters.end_date" />
      </label>

      <button @click="fetchLogs(1)">应用筛选</button>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading">加载中...</div>
    <div v-if="error" class="error">{{ error }}</div>

    <!-- 日志表格 -->
    <table v-if="!loading && !error" class="log-table">
      <thead>
        <tr>
          <th>用户</th>
          <th>级别</th>
          <th>IP 地址</th>
          <th>操作</th>
          <th>时间</th>
          <th>详情</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="log in logs" :key="log.id">
          <td>{{ log.user ? log.user.username : '系统' }}</td>
          <td :class="`level-${log.level}`">{{ log.level }}</td>
          <td>{{ log.ip_address || '未知' }}</td>
          <td>{{ log.action }}</td>
          <td>{{ formatDate(log.timestamp) }}</td>
          <td>{{ log.details || '无' }}</td>
        </tr>
      </tbody>
    </table>

    <!-- 分页控件 -->
    <div v-if="pagination.total_pages > 1" class="pagination">
      <button :disabled="pagination.page <= 1" @click="prevPage">上一页</button>
      <span>第 {{ pagination.page }} 页 / 共 {{ pagination.total_pages }} 页</span>
      <button :disabled="pagination.page >= pagination.total_pages" @click="nextPage">下一页</button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

// 数据定义
const logs = ref([]);
const pagination = ref({
  page: 1,
  page_size: 10,
  total_pages: 1,
  total: 0
});
const filters = ref({
  level: '',
  start_date: '',
  end_date: ''
});
const loading = ref(false);
const error = ref(null);

// 获取日志数据
const fetchLogs = async (page = 1) => {
  loading.value = true;
  error.value = null;

  try {
    const params = {
      page,
      page_size: pagination.value.page_size,
      level: filters.value.level,
      start_date: filters.value.start_date,
      end_date: filters.value.end_date
    };

    const response = await axios.get('/api/logs/', { params });
    logs.value = response.data.results;
    pagination.value = {
      page: response.data.current_page,
      page_size: response.data.page_size,
      total_pages: Math.ceil(response.data.total / response.data.page_size),
      total: response.data.total
    };
  } catch (err) {
    error.value = '加载日志失败，请稍后再试。';
    console.error(err);
  } finally {
    loading.value = false;
  }
};

// 分页操作
const prevPage = () => {
  if (pagination.value.page > 1) {
    fetchLogs(pagination.value.page - 1);
  }
};
const nextPage = () => {
  if (pagination.value.page < pagination.value.total_pages) {
    fetchLogs(pagination.value.page + 1);
  }
};

// 时间格式化
const formatDate = (timestamp) => {
  return new Date(timestamp).toLocaleString();
};

// 初始加载
onMounted(() => {
  fetchLogs();
});
</script>

<style scoped>
.log-viewer {
  font-family: Arial, sans-serif;
  padding: 20px;
}

.filter-form {
  margin-bottom: 20px;
}

.filter-form label {
  margin-right: 15px;
}

.log-table {
  width: 100%;
  border-collapse: collapse;
}

.log-table th, .log-table td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}

.level-info {
  color: #007bff;
}

.level-warning {
  color: #ffc107;
}

.level-error {
  color: #dc3545;
}

.pagination {
  margin-top: 15px;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
}

.loading, .error {
  text-align: center;
  margin-top: 20px;
  font-weight: bold;
}

.loading {
  color: #007bff;
}

.error {
  color: #dc3545;
}
</style>