<template>
  <div class="log-viewer">
    <!-- 筛选表单 -->
    <form class="filter-form" @submit.prevent="fetchLogs(1)">
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
      <button type="submit" class="btn-primary">应用筛选</button>
      <button type="button" class="btn-reset" @click="resetFilters">重置</button>
    </form>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading">加载中...</div>
    <div v-if="error" class="error">{{ error }}</div>

    <!-- 日志表格 -->
    <table v-if="!loading && !error && logs.length" class="log-table">
      <thead>
        <tr>
          <th style="width: 100px;">用户</th>
          <th style="width: 80px;">级别</th>
          <th style="width: 120px;">IP 地址</th>
          <th style="width: 180px;">操作</th>
          <th style="width: 170px;">时间</th>
          <th style="width: 220px;">详情</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="log in logs" :key="log.id">
          <td class="ellipsis">{{ log.user ? log.user.username : '系统' }}</td>
          <td>
            <span :class="['level-tag', `level-${log.level}`]">{{ log.level }}</span>
          </td>
          <td class="ellipsis">{{ log.ip_address || '未知' }}</td>
          <td class="ellipsis" :title="log.action">{{ log.action }}</td>
          <td>{{ formatDate(log.timestamp) }}</td>
          <td class="ellipsis" :title="log.details">{{ log.details || '无' }}</td>
        </tr>
      </tbody>
    </table>
    <div v-if="!loading && !error && !logs.length" class="empty-tip">暂无日志数据</div>

    <!-- 分页控件 -->
    <div v-if="pagination.total_pages > 1" class="pagination">
      <button :disabled="pagination.page <= 1" @click="prevPage">上一页</button>
      <span>第 {{ pagination.page }} 页 / 共 {{ pagination.total_pages }} 页</span>
      <button :disabled="pagination.page >= pagination.total_pages" @click="nextPage">下一页</button>
      <span style="margin-left: 12px;">
        跳转到
        <input
          type="number"
          min="1"
          :max="pagination.total_pages"
          v-model.number="jumpPage"
          style="width: 60px; margin: 0 4px;"
        />
        页
        <button @click="goToPage">跳转</button>
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

const logs = ref([]);
const pagination = ref({
  page: 1,
  page_size: 15,
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
const jumpPage = ref(1);

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
      end_date: filters.value.end_date,
    };
    const response = await axios.get('/api/logs/', { params });
    logs.value = response.data.results;
    pagination.value = {
      page: response.data.current_page,
      page_size: response.data.page_size,
      total_pages: Math.ceil(response.data.total / response.data.page_size),
      total: response.data.total
    };
    jumpPage.value = pagination.value.page;
  } catch (err) {
    error.value = '加载日志失败，请稍后再试。';
    console.error(err);
  } finally {
    loading.value = false;
  }
};

const resetFilters = () => {
  filters.value.level = '';
  filters.value.start_date = '';
  filters.value.end_date = '';
  fetchLogs(1);
};

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
const goToPage = () => {
  let page = jumpPage.value;
  if (typeof page !== 'number' || isNaN(page)) page = 1;
  if (page < 1) page = 1;
  if (page > pagination.value.total_pages) page = pagination.value.total_pages;
  fetchLogs(page);
};

const formatDate = (timestamp) => {
  if (!timestamp) return '';
  const d = new Date(timestamp);
  const pad = n => n < 10 ? '0' + n : n;
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
};

onMounted(() => {
  fetchLogs();
});
</script>

<style scoped>
.log-viewer {
  font-family: Arial, sans-serif;
  padding: 20px;
  background: #fafbfc;
  min-height: 100vh;
}

.filter-form {
  margin-bottom: 20px;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}
.filter-form label {
  margin-right: 10px;
  font-size: 14px;
}
.filter-form .btn-primary {
  background: #007bff;
  color: #fff;
  border: none;
  padding: 6px 18px;
  border-radius: 4px;
  cursor: pointer;
  margin-left: 8px;
}
.filter-form .btn-reset {
  background: #f5f5f5;
  color: #333;
  border: 1px solid #ccc;
  padding: 6px 14px;
  border-radius: 4px;
  cursor: pointer;
  margin-left: 4px;
}

.log-table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
  box-shadow: 0 2px 8px #f0f1f2;
}
.log-table th, .log-table td {
  border: 1px solid #eee;
  padding: 8px 10px;
  text-align: left;
  font-size: 14px;
  max-width: unset;
  white-space: nowrap;
}
.log-table th {
  background: #f7f7f7;
}
.log-table tr:nth-child(even) {
  background: #f9f9f9;
}
.log-table tr:hover {
  background: #e6f7ff;
}
.ellipsis {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 180px;
}

.level-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 13px;
  font-weight: bold;
  color: #fff;
}
.level-info {
  background: #007bff;
}
.level-warning {
  background: #ffc107;
  color: #333;
}
.level-error {
  background: #dc3545;
}

.pagination {
  margin-top: 18px;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
}
.pagination button {
  background: #fff;
  border: 1px solid #007bff;
  color: #007bff;
  padding: 4px 14px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}
.pagination button:disabled {
  color: #aaa;
  border-color: #eee;
  cursor: not-allowed;
  background: #fafafa;
}

.loading, .error, .empty-tip {
  text-align: center;
  margin-top: 30px;
  font-weight: bold;
  font-size: 16px;
}
.loading {
  color: #007bff;
}
.error {
  color: #dc3545;
}
.empty-tip {
  color: #888;
}
</style>