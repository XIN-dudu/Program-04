<template>
  <div class="container">
    <!-- 左侧：视频/图片区域 + 控制栏 -->
    <div class="left-panel">
      <!-- 视频或图片显示 -->
      <div class="media-display">
        <video
          ref="videoElement"
          controls
          autoplay
          playsinline
          muted
          v-if="isVideo"
          style="max-width: 100%; max-height: 100%;"
        ></video>
        <img v-else-if="isImage" :src="mediaPreviewUrl" alt="上传图片预览" />
        <div v-else class="media-placeholder">
          <p v-if="selectedFile">{{ selectedFile.name }}</p>
          <p v-else>路面视频/图像</p>
        </div>
      </div>

      <!-- 控制按钮区域 -->
      <div class="control-bar">
        <input type="text" v-model="roadId" placeholder="道路编号" class="input" />

        <!-- 摄像头控制 -->
        <button @click="openCamera" :disabled="videoActive">打开摄像头</button>
        <button @click="startRecording" :disabled="recording || !videoActive">开始录制</button>
        <button @click="stopRecording" :disabled="!recording">停止录制</button>
        <button @click="takePhoto" :disabled="!videoActive || recording">拍照</button>

        <!-- 文件上传 -->
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
import axios from 'axios'
import { ref, nextTick, onMounted, onBeforeUnmount } from 'vue'

const roadId = ref('')
const videoActive = ref(false)
const selectedFile = ref(null)
const detectionInProgress = ref(false)
const results = ref([])
const videoElement = ref(null)
const fileInput = ref(null)

const mediaPreviewUrl = ref('')
const isImage = ref(false)
const isVideo = ref(false)

const photoDataUrl = ref('')
const recordedVideoUrl = ref('')
const recording = ref(false)

const mediaStream = ref(null)
const mediaRecorder = ref(null)
const recordedChunks = ref([])

const issues = [
  { title: '裂缝检测', description: '检测到裂缝约2.3米', severity: '中等' },
  { title: '坑洞检测', description: '检测到坑洞直径15cm', severity: '严重' },
  { title: '边缘破损', description: '道路边缘破损长度约1.5米', severity: '轻微' },
]
const openCamera = () => {
  if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    navigator.mediaDevices.getUserMedia({ video: true, audio: true })
      .then(stream => {
        mediaStream.value = stream
        videoActive.value = true
        isVideo.value = true
        isImage.value = false
        selectedFile.value = null
        recordedVideoUrl.value = ''
        photoDataUrl.value = ''
        mediaPreviewUrl.value = ''

        // 设置摄像头流到 video 元素
        nextTick(() => {
          if (videoElement.value) {
            videoElement.value.srcObject = stream
            videoElement.value.muted = true
            videoElement.value.play().catch(err => {
              console.warn('video.play() 失败:', err)
            })
          }
        })

        // 设置自动关闭定时器
        clearTimeout(autoStopTimer)
        autoStopTimer = setTimeout(() => {
          alert('摄像头使用时间到，自动关闭')
          stopCamera()
        }, 3 * 60 * 1000)
      })
      .catch(error => {
        console.error('摄像头访问失败:', error)
      })
  } else {
    //alert('当前浏览器不支持摄像头访问')
  }
}

const startRecording = () => {
  if (!mediaStream.value) {
    alert('请先打开摄像头')
    return
  }

  // 清空上一次录制的视频 URL 和播放器内容
  recordedVideoUrl.value = ''
  isVideo.value = true
  isImage.value = false

  if (videoElement.value) {
    videoElement.value.srcObject = mediaStream.value
    videoElement.value.src = ''
    videoElement.value.controls = false
    videoElement.value.load()
    videoElement.value.play()
  }

  recordedChunks.value = []
  try {
    mediaRecorder.value = new MediaRecorder(mediaStream.value, { mimeType: 'video/webm; codecs=vp9' })
  } catch (e) {
    mediaRecorder.value = new MediaRecorder(mediaStream.value)
  }

  mediaRecorder.value.ondataavailable = event => {
    if (event.data.size > 0) {
      recordedChunks.value.push(event.data)
    }
  }

  mediaRecorder.value.onstop = () => {
    const blob = new Blob(recordedChunks.value, { type: 'video/webm' })
    const url = URL.createObjectURL(blob)
    recordedVideoUrl.value = url

    // 显示录制结果视频
    if (videoElement.value) {
      videoElement.value.srcObject = null
      videoElement.value.src = url
      videoElement.value.controls = true
      videoElement.value.load()
      videoElement.value.play()
    }

  }

  mediaRecorder.value.start()
  recording.value = true
}

const stopRecording = () => {
  if (mediaRecorder.value && recording.value) {
    mediaRecorder.value.stop()
    recording.value = false

    mediaRecorder.value.onstop = () => {
      const blob = new Blob(recordedChunks.value, { type: 'video/webm' })
      const file = new File([blob], `recording_${Date.now()}.webm`, {
        type: 'video/webm'
      });
      selectedFile.value = file
      const url = URL.createObjectURL(blob)
      recordedVideoUrl.value = url

      //设置 video 显示录制内容
      if (videoElement.value) {
        videoElement.value.srcObject = null
        videoElement.value.src = url
        videoElement.value.controls = true
        videoElement.value.load()
        videoElement.value.play()
      }

      isVideo.value = true
      isImage.value = false
      videoActive.value = false
      stop()
    }
  }
}

const takePhoto = () => {
  if (!videoElement.value) return

  // 清空状态
  recordedVideoUrl.value = ''
  mediaPreviewUrl.value = ''
  selectedFile.value = null
  results.value = []
  isImage.value = true
  isVideo.value = false
  videoActive.value = false
  
  
  const video = videoElement.value
  selectedFile.value = video
  const canvas = document.createElement('canvas')
  canvas.width = video.videoWidth || 640
  canvas.height = video.videoHeight || 480
  const ctx = canvas.getContext('2d')
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
  const dataUrl = canvas.toDataURL('image/png')
  photoDataUrl.value = dataUrl

  //清空 video 内容，确保视频不再显示
  if (videoElement.value) {
    videoElement.value.pause()
    videoElement.value.srcObject = null
    videoElement.value.src = ''
    videoElement.value.load()
  }

  //设置图片预览
  mediaPreviewUrl.value = dataUrl
  // 生成Blob对象
  canvas.toBlob(async (blob) => {
    const file = new File([blob], `photo_${Date.now()}.png`, {
      type: 'image/png'
    })
    // 更新状态
    selectedFile.value = file
    mediaPreviewUrl.value = URL.createObjectURL(blob)
    isImage.value = true
    isVideo.value = false
    videoActive.value = false
    stop()
  }, 'image/png')

}


const stopCamera = async () => {

  stop()
  if (mediaPreviewUrl.value) {
    URL.revokeObjectURL(mediaPreviewUrl.value)
    mediaPreviewUrl.value = ''
  }

  if (selectedFile.value) {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('roadId', roadId.value)

    try {
      await axios.post('/road/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      const result = await res.json()
      console.log('上传成功:', result)
    } catch (err) {
      console.error('上传失败:', err)
    }
  }
  roadId.value = ''
  videoActive.value = false
  selectedFile.value = null
  detectionInProgress.value = false
  results.value = []
  isImage.value = false
  isVideo.value = false
  photoDataUrl.value = ''
  recordedVideoUrl.value = ''
  recording.value = false

  if (fileInput.value) fileInput.value.value = ''

}

const stop = () => {
  if (videoElement.value?.srcObject) {
    videoElement.value.srcObject.getTracks().forEach(track => track.stop())
    videoElement.value.srcObject = null
  }
  if (mediaStream.value) {
    mediaStream.value.getTracks().forEach(track => track.stop())
    mediaStream.value = null
  }
}

const triggerUpload = () => {
  if (recording.value) {
    alert('请先停止录制')
    return
  }
  stopCamera()
  fileInput.value.click()
}

const handleUpload = async e => {
  const file = e.target.files[0]
  if (!file) return
  selectedFile.value = file
  const url = URL.createObjectURL(file)
  mediaPreviewUrl.value = url
  isVideo.value = file.type.startsWith('video/')
  isImage.value = file.type.startsWith('image/')
  videoActive.value = isVideo.value
  photoDataUrl.value = ''
  recordedVideoUrl.value = ''
  results.value = []

  if (isVideo.value) {
    await nextTick()
    if (videoElement.value) {
      videoElement.value.srcObject = null
      videoElement.value.src = url
      videoElement.value.load()
      videoElement.value.play()
    }
  }
}
const detectIssues = () => {
  if (!roadId.value || !selectedFile.value) {
    alert('请填写道路编号并上传视频/图片')
    return
  }
  detectionInProgress.value = true
  results.value = issues.sort(() => 0.5 - Math.random()).slice(0, 2 + Math.floor(Math.random() * 2))
  detectionInProgress.value = false
}

onMounted(() => {
  window.addEventListener('beforeunload', stopCamera)
})

onBeforeUnmount(() => {
  stopCamera()
})
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

button:hover:not(:disabled) {
  background: #3c60c0;
}

button:disabled {
  background: #888;
  cursor: not-allowed;
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

.photo-result img,
.video-result video {
  max-width: 100%;
  border-radius: 6px;
  border: 1px solid #ccc;
  margin-top: 8px;
}
</style>
