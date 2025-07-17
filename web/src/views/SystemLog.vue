<template>
  <div class="log-plus-container">
    <div class="log-plus-card">
      <!-- 筛选表单 -->
      <el-form :inline="true" :model="filters" class="filter-form" @submit.prevent>
        <el-form-item label="用户名">
          <el-input v-model="filters.username" placeholder="输入用户名" clearable style="width: 140px;" />
        </el-form-item>
        <el-form-item label="级别">
          <el-select v-model="filters.level" placeholder="全部" clearable style="width: 120px;">
            <el-option label="全部" value="" />
            <el-option label="Info" value="info" />
            <el-option label="Warning" value="warning" />
            <el-option label="Error" value="error" />
          </el-select>
        </el-form-item>
        <el-form-item label="开始时间">
          <el-date-picker
            v-model="filters.start_date"
            type="date"
            placeholder="开始日期"
            value-format="YYYY-MM-DD"
            style="width: 140px;"
            clearable
          />
        </el-form-item>
        <el-form-item label="结束时间">
          <el-date-picker
            v-model="filters.end_date"
            type="date"
            placeholder="结束日期"
            value-format="YYYY-MM-DD"
            style="width: 140px;"
            clearable
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="fetchLogs(1)">筛选</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="log-plus-table-card">
      <el-table
        v-loading="loading"
        :data="logs"
        border
        style="width: 100%;"
        :default-sort="{ prop: 'timestamp', order: 'descending' }"
        highlight-current-row
        size="large"
        empty-text="暂无日志数据"
      >
        <el-table-column prop="user.username" label="用户" width="120" :show-overflow-tooltip="true" />
        <el-table-column prop="level" label="级别" width="100">
          <template #default="scope">
            <el-tag :type="levelTagType(scope?.row?.level)" disable-transitions>{{ scope?.row?.level || '' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="ip_address" label="IP 地址" width="140" :show-overflow-tooltip="true" />
        <el-table-column label="操作" width="180" :show-overflow-tooltip="true">
          <template #default="scope">
            {{ scope?.row?.action || '' }}
          </template>
        </el-table-column>
        <el-table-column prop="timestamp" label="时间" width="180" sortable>
          <template #default="scope">
            {{ formatDate(scope?.row?.timestamp) }}
          </template>
        </el-table-column>
        <el-table-column prop="details" label="详情" min-width="220">
          <template #default="scope">
            <el-tooltip
              class="item"
              effect="dark"
              :content="scope?.row?.details"
              placement="top"
              raw-content
            >
              <span class="details-ellipsis" @dblclick="copyText(scope?.row?.details)">
                <template v-if="scope?.row?.alert_event_video_url">
                  <el-link type="primary" @click.stop="playAlertVideo(scope.row.alert_event_video_url)">
                    {{ scope.row.details }}
                  </el-link>
                </template>
                <template v-else>
                  {{ scope?.row?.details || '' }}
                </template>
              </span>
            </el-tooltip>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="log-plus-pagination">
        <el-pagination
          v-if="pagination.total_pages > 1"
          background
          layout="prev, pager, next, jumper, ->, total"
          :current-page="pagination.page"
          :page-size="pagination.page_size"
          :total="pagination.total"
          @current-change="fetchLogs"
        />
      </div>
    </div>

    <!-- 视频弹窗 -->
    <el-dialog v-model="showVideoDialog" title="告警视频" width="600px" align-center>
      <video v-if="currentVideoUrl" :src="currentVideoUrl" controls style="width:100%;border-radius:8px;" />
    </el-dialog>
  </div>
</template>
  
  <script setup>
  import { ref, onMounted } from 'vue'
  import axios from 'axios'
  import { ElMessage } from 'element-plus'
  
  const logs = ref([])
  const pagination = ref({
    page: 1,
    page_size: 10,
    total_pages: 1,
    total: 0
  })
  const filters = ref({
    username: '',
    level: '',
    start_date: '',
    end_date: ''
  })
  const loading = ref(false)
  const showVideoDialog = ref(false)
  const currentVideoUrl = ref('')
  
  const fetchLogs = async (page = 1) => {
    loading.value = true
    try {
      const params = {
        page,
        page_size: pagination.value.page_size,
        username: filters.value.username,
        level: filters.value.level,
        start_date: filters.value.start_date || '',
        end_date: filters.value.end_date || ''
      }
      const response = await axios.get('/api/logs/', { params })
      logs.value = response.data.results
      pagination.value = {
        page: response.data.current_page,
        page_size: response.data.page_size,
        total_pages: Math.ceil(response.data.total / response.data.page_size),
        total: response.data.total
      }
    } catch (err) {
      ElMessage.error('加载日志失败，请稍后再试。')
      logs.value = []
      pagination.value = { page: 1, page_size: 10, total_pages: 1, total: 0 }
    } finally {
      loading.value = false
    }
  }
  
  const resetFilters = () => {
    filters.value.username = ''
    filters.value.level = ''
    filters.value.start_date = ''
    filters.value.end_date = ''
    fetchLogs(1)
  }
  
  const formatDate = (timestamp) => {
    if (!timestamp) return ''
    const d = new Date(timestamp)
    const pad = n => n < 10 ? '0' + n : n
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
  }
  
  const playAlertVideo = (url) => {
    currentVideoUrl.value = url
    showVideoDialog.value = true
  }
  
  const copyText = (text) => {
    navigator.clipboard.writeText(text)
    ElMessage.success('已复制详情内容')
  }
  
  const levelTagType = (level) => {
    if (level === 'info') return 'info'
    if (level === 'warning') return 'warning'
    if (level === 'error') return 'danger'
    return ''
  }
  
  onMounted(() => {
    fetchLogs()
  })
  </script>
  
  <style scoped>
  .log-plus-container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 32px 12px 40px 12px;
    background: #f5f6fa;
    min-height: 100vh;
  }
  .log-plus-card {
    background: #fff;
    border-radius: 10px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    padding: 24px 24px 10px 24px;
    margin-bottom: 18px;
  }
  .filter-form {
    display: flex;
    flex-wrap: wrap;
    gap: 8px 12px;
    align-items: flex-end;
  }
  .log-plus-table-card {
    background: #fff;
    border-radius: 10px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    padding: 18px 18px 8px 18px;
  }
  .el-table th, .el-table td {
    font-size: 15px;
    padding: 10px 8px;
  }
  .el-table .el-table__row:hover {
    background: #f0f7ff !important;
  }
  .details-ellipsis {
    display: inline-block;
    max-width: 400px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    vertical-align: bottom;
    cursor: pointer;
  }
  .log-plus-pagination {
    margin: 18px 0 0 0;
    display: flex;
    justify-content: flex-end;
  }
  @media (max-width: 900px) {
    .log-plus-container {
      max-width: 100vw;
      padding: 8px 2vw;
    }
    .log-plus-card, .log-plus-table-card {
      padding: 10px 4px;
    }
    .el-table th, .el-table td {
      font-size: 13px;
      padding: 6px 2px;
    }
  }
  </style>