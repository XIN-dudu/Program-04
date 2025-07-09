<template>
  <div class="container">
    <!-- 左侧：视频/图片区域 + 控制栏 -->
    <div class="left-panel">
      <!-- 视频或图片显示 -->
      <div class="media-display">
        <video v-if="isVideo" ref="videoElement" controls autoplay playsinline></video>
        <img v-else-if="isImage" :src="mediaPreviewUrl" alt="上传图片预览" />
        <div v-else class="media-placeholder">
          <p v-if="selectedFile">{{ selectedFile.name }}</p>
          <p v-else>路面视频/图像</p>
        </div>
      </div>

      <!-- 控制按钮区域 -->
      <div class="control-bar">
        <input type="text" v-model="roadId" placeholder="道路编号" class="input" />
        <button @click="openCamera">拍摄上传</button>
        <button @click="triggerUpload">本地上传</button>
        <button @click="detectIssues" :disabled="detectionInProgress">{{ detectionInProgress ? '检测中' : '检测' }}</button>
        <button @click="stopCamera">结束</button>
        <input ref="fileInput" type="file" accept="video/*,image/*" style="display: none" @change="handleUpload" />
      </div>
    </div>

    <!-- 右侧：检测结果 -->
    <div class="right-panel">
      <div class="result-header">检测结果：</div>
      <div class="result-list">
        <p v-if="results.length === 0">具体展示结果</p>
        <div v-for="(item, index) in results" :key="index" class="result-card">
          <h3>{{ item.title }}</h3>
          <p>{{ item.description }}</p>
          <p><strong>严重程度:</strong> {{ item.severity }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue';

const roadId = ref('');
const videoActive = ref(false);
const selectedFile = ref(null);
const detectionInProgress = ref(false);
const results = ref([]);
const videoElement = ref(null);
const fileInput = ref(null);

const mediaPreviewUrl = ref('');
const isImage = ref(false);
const isVideo = ref(false);

const issues = [
  { title: '裂缝检测', description: '检测到裂缝约2.3米', severity: '中等' },
  { title: '坑洞检测', description: '检测到坑洞直径15cm', severity: '严重' },
  { title: '边缘破损', description: '道路边缘破损长度约1.5米', severity: '轻微' },
];

const openCamera = async () => {
  stopCamera();
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    videoElement.value.srcObject = stream;
    videoActive.value = true;
    selectedFile.value = null;
    isVideo.value = true;
    isImage.value = false;
    mediaPreviewUrl.value = '';
  } catch (e) {
    alert('无法访问摄像头，请检查权限');
  }
};
const stopCamera = () => {
  if (videoElement.value?.srcObject) {
    videoElement.value.srcObject.getTracks().forEach(track => track.stop());
    videoElement.value.srcObject = null;
  }

  if (videoElement.value) {
    videoElement.value.src = '';
    videoElement.value.load();
  }

  if (mediaPreviewUrl.value) {
    URL.revokeObjectURL(mediaPreviewUrl.value);
    mediaPreviewUrl.value = '';
  }

  roadId.value = '';
  videoActive.value = false;
  selectedFile.value = null;
  detectionInProgress.value = false;
  results.value = [];
  isImage.value = false;
  isVideo.value = false;

  if (fileInput.value) {
    fileInput.value.value = '';
  }
};




const triggerUpload = () => {
  stopCamera();
  fileInput.value.click();
};

import { nextTick } from 'vue'; // 确保引入 nextTick

const handleUpload = async (e) => {
  const file = e.target.files[0];
  if (file) {
    selectedFile.value = file;
    const fileURL = URL.createObjectURL(file);

    isVideo.value = file.type.startsWith('video/');
    isImage.value = file.type.startsWith('image/');
    results.value = [];

    mediaPreviewUrl.value = fileURL;

    if (isVideo.value) {
      isImage.value = false;
      videoActive.value = true;

      await nextTick(); // 等待 <video> 渲染完毕
      if (videoElement.value) {
        videoElement.value.srcObject = null;
        videoElement.value.src = fileURL;
        videoElement.value.load();
      }
    } else {
      videoActive.value = false;
    }
  }
};


const detectIssues = () => {
  if (!roadId.value || (!videoActive.value && !selectedFile.value)) {
    alert('请填写道路编号并上传视频/图片或开启摄像头');
    return;
  }

  detectionInProgress.value = true;
  setTimeout(() => {
    results.value = issues.sort(() => 0.5 - Math.random()).slice(0, 2 + Math.floor(Math.random() * 2));
    detectionInProgress.value = false;
  }, 2000);
};

onMounted(() => {
  window.addEventListener('beforeunload', stopCamera);
});

onBeforeUnmount(() => {
  stopCamera();
});
</script>

<style scoped>
.container {
  display: flex;
  padding: 20px;
  gap: 20px;
  font-family: Arial, sans-serif;
}

/* 左侧 */
.left-panel {
  flex: 3;
  display: flex;
  flex-direction: column;
}

.media-display {
  height: 400px;
  background: #f0f0f0;
  border: 2px dashed #aaa;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.media-display video,
.media-display img {
  max-width: 100%;
  max-height: 100%;
}

.media-placeholder {
  text-align: center;
  color: #888;
}

.control-bar {
  display: flex;
  gap: 10px;
  margin-top: 15px;
  flex-wrap: wrap;
}

.input {
  flex: 1;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 6px;
}

button {
  padding: 10px 15px;
  border: none;
  background: #1a2980;
  color: white;
  border-radius: 6px;
  cursor: pointer;
  transition: 0.3s;
}

button:hover {
  background: #3c60c0;
}

/* 右侧结果 */
.right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.result-header {
  font-size: 1.2rem;
  font-weight: bold;
  margin-bottom: 10px;
}

.result-list {
  flex: 1;
  background: #fafafa;
  padding: 10px;
  border: 1px solid #ddd;
  overflow-y: auto;
}

.result-card {
  background: white;
  padding: 10px;
  border-left: 4px solid #1a2980;
  margin-bottom: 10px;
  border-radius: 5px;
}
</style>
