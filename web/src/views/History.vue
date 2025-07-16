<template>
  <div class="container">
    <h2>病害记录历史界面</h2>

    <div v-if="records.length === 0" class="no-data">暂无任务记录</div>

    <div class="card-grid" v-else>
      <div
        v-for="(record, index) in records"
        :key="record.road_id"
        class="record-card"
        @click="showCardPreview(record)"
      >
        <h3>道路编号：{{ record.road_id }}</h3>

        <div class="desc-list">
          <div
            v-for="(desc, idx) in record.description"
            :key="idx"
            class="desc-entry"
          >
            <p><strong>病害类型：</strong>{{ desc.disease_type }}</p>
            <p><strong>严重程度：</strong>{{ desc.severity }}</p>
            <p><strong>面积：</strong>{{ desc.area }}㎡</p>
            <p><strong>长度：</strong>{{ desc.length }}m</p>

            <template v-if="desc.url">
              <img
                v-if="isImageUrl(desc.url)"
                :src="getFullUrl(desc.url)"
                alt="检测图像"
                class="media"
                @click.stop
              />
              <video
                v-else-if="isVideoUrl(desc.url)"
                :src="getFullUrl(desc.url)"
                controls
                class="media"
                @click.stop
              />
              <p v-else class="no-media">⚠️ 不支持的媒体类型</p>
            </template>
            <p v-else class="no-media">无图像信息</p>
          </div>
        </div>

        <button
          v-if="isDeletable"
          class="delete-button"
          @click.stop="deleteRecord(record.road_id, index)"
        >
          删除记录
        </button>
      </div>
    </div>

    <!-- 卡片放大预览模态框 -->
    <teleport to="body">
      <div v-if="previewRecord" class="modal-overlay" @click.self="closePreview">
        <div class="modal-content large-card">
          <h3>道路编号：{{ previewRecord.road_id }}</h3>

          <div class="desc-list">
            <div
              v-for="(desc, idx) in previewRecord.description"
              :key="idx"
              class="desc-entry"
            >
              <p><strong>病害类型：</strong>{{ desc.disease_type }}</p>
              <p><strong>严重程度：</strong>{{ desc.severity }}</p>
              <p><strong>面积：</strong>{{ desc.area }}㎡</p>
              <p><strong>长度：</strong>{{ desc.length }}m</p>

              <template v-if="desc.url">
                <img
                  v-if="isImageUrl(desc.url)"
                  :src="getFullUrl(desc.url)"
                  alt="放大图像"
                  class="media"
                />
                <video
                  v-else-if="isVideoUrl(desc.url)"
                  :src="getFullUrl(desc.url)"
                  controls
                  class="media"
                />
                <p v-else class="no-media">⚠️ 不支持的媒体类型</p>
              </template>
              <p v-else class="no-media">无图像信息</p>
            </div>
          </div>

          <button class="modal-close" @click="closePreview">×</button>
        </div>
      </div>
    </teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'

// 权限判断
const userPermissionRef = ref(localStorage.getItem('permission') || '0')
const isRepairMan = computed(() => userPermissionRef.value === '1')
const isAdmin = computed(() => userPermissionRef.value === '2')
const isDeletable = computed(() => isRepairMan.value || isAdmin.value)

const backendBaseURL = 'http://localhost:8000'
const records = ref([])

const getFullUrl = (url) => {
  if (!url) return ''
  const fixedPath = url.replace(/\\/g, '/')
  return fixedPath.startsWith('http') ? fixedPath : backendBaseURL + fixedPath
}

const isImageUrl = (url) => /\.(jpg|jpeg|png|gif|bmp)$/i.test(url)
const isVideoUrl = (url) => /\.(mp4|webm|ogg|avi|mov)$/i.test(url)

const fetchRecords = async () => {
  try {
    const res = await axios.get(`${backendBaseURL}/history/list`, {
      withCredentials: true
    })
    records.value = res.data
  } catch (err) {
    console.error('获取记录失败:', err)
    records.value = []
  }
}

const deleteRecord = async (roadId, index) => {
  if (!confirm('确定要删除这条记录吗？')) return
  try {
    await axios.delete(`${backendBaseURL}/history/${roadId}/delete`, {
      withCredentials: true
    })
    records.value.splice(index, 1)
  } catch (error) {
    console.error('删除失败:', error)
    alert('删除失败，请稍后重试')
  }
}

// 放大卡片预览控制
const previewRecord = ref(null)

const showCardPreview = (record) => {
  previewRecord.value = record
}

const closePreview = () => {
  previewRecord.value = null
}

onMounted(() => {
  fetchRecords()
})
</script>

<style scoped>
.container {
  padding: 30px;
  font-family: "Segoe UI", sans-serif;
  background-color: #f5f7fa;
}

h2 {
  margin-bottom: 24px;
  font-size: 24px;
  color: #333;
  font-weight: 600;
}

.no-data {
  font-style: italic;
  color: #888;
  text-align: center;
  margin-top: 50px;
}

/* 卡片网格布局 */
.card-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  justify-content: center;
}

/* 卡片样式 */
.record-card {
  flex: 1 1 340px;
  max-width: 360px;
  background-color: #fff;
  border-left: 5px solid #3399ff;
  padding: 18px;
  border-radius: 12px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  cursor: pointer;
}

.record-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
}

.record-card {
  flex: 1 1 340px;
  max-width: 360px;
  background-color: #fff;
  border: 2px solid #3399ff;    /* 改这里 */
  padding: 18px;
  border-radius: 12px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  cursor: pointer;
}

/* 描述滚动区域 */
.desc-list {
  max-height: 280px;
  overflow-y: auto;
  margin-top: 8px;
  padding-right: 10px;
  border: 1px solid #e5e5e5;
  border-radius: 6px;
  background-color: #fdfdfd;
}

.desc-entry {
  border-top: 1px dashed #ccc;
  padding-top: 10px;
  margin-top: 10px;
  font-size: 14px;
  color: #333;
  line-height: 1.5;
}

.media {
  width: 100%;
  max-width: 100%;
  margin-top: 10px;
  border: 1px solid #ccc;
  border-radius: 6px;
  cursor: pointer;
  transition: transform 0.2s ease;
}

.media:hover {
  transform: scale(1.02);
}

.no-media {
  color: #999;
  font-style: italic;
  margin-top: 10px;
  font-size: 13px;
}

/* 删除按钮 */
.delete-button {
  margin-top: 16px;
  padding: 8px 14px;
  background-color: #e74c3c;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: bold;
  transition: background-color 0.2s ease;
}
.delete-button:hover {
  background-color: #c0392b;
}

/* 滚动条美化 */
.desc-list::-webkit-scrollbar {
  width: 6px;
}
.desc-list::-webkit-scrollbar-thumb {
  background-color: #bbb;
  border-radius: 3px;
}
.desc-list::-webkit-scrollbar-thumb:hover {
  background-color: #999;
}

/* 模态预览样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  z-index: 9999;
  display: flex;
  justify-content: center;
  align-items: center;
}

.modal-content.large-card {
  max-width: 800px;
  max-height: 90vh;
  overflow-y: auto;
  padding: 20px;
  border-radius: 10px;
  background-color: white;
}

.modal-content.large-card h3 {
  font-size: 20px;
  margin-bottom: 16px;
}

.modal-content.large-card .desc-list {
  max-height: none;
  border: none;
  background: none;
  padding-right: 0;
}

.modal-close {
  position: absolute;
  top: -10px;
  right: -10px;
  background-color: #e74c3c;
  color: white;
  border: none;
  border-radius: 50%;
  width: 28px;
  height: 28px;
  font-size: 18px;
  cursor: pointer;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
}

/* 防止点击媒体触发卡片点击，增加指针事件 */
.media {
  pointer-events: auto;
}

/* 阻止媒体点击冒泡 */
</style>
