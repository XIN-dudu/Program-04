<template>
  <div class="container">
    <!-- 左侧：视频/图片区域 + 控制栏 -->
    <div class="left-panel">
      <!-- 视频或图片显示 -->
      <div class="media-display">
        <video ref="videoElement" controls autoplay playsinline muted v-if="isVideo"
          style="max-width: 100%; max-height: 100%;"></video>
        <img v-else-if="isImage" :src="mediaPreviewUrl" alt="上传图片预览" />
        <div v-else class="media-placeholder">
          <p v-if="selectedFile">{{ selectedFile.name }}</p>
          <p v-else>路面视频/图像</p>
        </div>
      </div>

      <!-- 控制按钮区域 -->
      <div class="control-bar">
        <input type="text" v-model="roadId" placeholder="道路编号" class="input" />
        <button @click="openCamera" :disabled="videoActive">打开摄像头</button>
        <button @click="startRecording" :disabled="recording || !videoActive">开始录制</button>
        <button @click="stopRecording" :disabled="!recording">停止录制</button>
        <button @click="takePhoto" :disabled="!videoActive || recording">拍照</button>
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
        <p v-if="results.length === 0">暂无检测结果</p>
        <div v-else>
          <div v-for="(item, index) in results" :key="index" class="result-section">
            <h3 style="margin-top: 10px">道路编号：{{ item.road_id }}</h3>

            <!-- 显示带框整图 -->
            <img v-if="item.full_image_base64" :src="item.full_image_base64" alt="带框检测图"
              style="max-width: 100%; margin-bottom: 10px;" />

            <div v-for="(desc, i) in item.description" :key="i" class="result-card">
              <p><strong>病害类型：</strong>{{ desc.disease_type }}</p>
              <p><strong>危险等级：</strong>{{ desc.severity }}</p>
              <p><strong>面积比例：</strong>{{ desc.area.toFixed(4) }}</p>
              <p><strong>裂缝长度：</strong>{{ desc.length.toFixed(4) }}</p>
              <img v-if="desc.image_base64" :src="desc.image_base64" alt="检测裁剪图" />
              <img v-else-if="desc.url" :src="desc.url.replace(/\\/g, '/')" alt="检测裁剪图" />

            </div>
          </div>
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

let autoStopTimer = null
let frameCaptureTimer = null
let frameCounter = 0

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

        nextTick(() => {
          if (videoElement.value) {
            videoElement.value.srcObject = stream
            videoElement.value.muted = true
            videoElement.value.play().catch(err => {
              console.warn('video.play() 失败:', err)
            })
          }
        })

        // 自动抓图逻辑
        frameCounter = 0
        clearInterval(frameCaptureTimer)
        frameCaptureTimer = setInterval(() => {
          if (!videoElement.value || videoElement.value.readyState < 2) return
          frameCounter++
          if (frameCounter % 10 === 0) {
            captureFrameAndSend()
          }
        }, 100)
      })
      .catch(error => {
        console.error('摄像头访问失败:', error)
      })
  }
}

const captureFrameAndSend = () => {
  const video = videoElement.value
  if (!video) return

  const canvas = document.createElement('canvas')
  canvas.width = video.videoWidth || 640
  canvas.height = video.videoHeight || 480
  const ctx = canvas.getContext('2d')
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height)

  canvas.toBlob(async (blob) => {
    if (!blob) return
    const file = new File([blob], `frame_${Date.now()}.jpg`, { type: 'image/jpeg' })

    const formData = new FormData()
    formData.append('file', file)
    formData.append('roadId', roadId.value || 'unknown')

    try {
      const res = await axios.post('http://localhost:8000/road/streamFrame', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        withCredentials: true
      })

      const data = res.data
      if (!data || !data.description || !Array.isArray(data.description)) return

      // 每一帧结果都作为新的 result 添加
      results.value.unshift({
        road_id: `${data.road_id}（帧时间：${new Date().toLocaleTimeString()}）`,
        description: data.description,
        full_image_base64: data.full_image_base64 || ''
      })

    } catch (error) {
      console.warn('帧上传失败:', error)
    }
  }, 'image/jpeg')
}


const startRecording = () => {
  if (!mediaStream.value) {
    alert('请先打开摄像头')
    return
  }

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
    mediaRecorder.value = new MediaRecorder(mediaStream.value, { mimeType: 'video/mp4' })
  } catch {
    mediaRecorder.value = new MediaRecorder(mediaStream.value)
  }

  mediaRecorder.value.ondataavailable = e => {
    if (e.data.size > 0) recordedChunks.value.push(e.data)
  }

  mediaRecorder.value.onstop = () => {
    const mimeType = mediaRecorder.value.mimeType.includes('mp4') ? 'video/mp4' : 'video/webm'
    const blob = new Blob(recordedChunks.value, { type: mimeType })
    const fileExtension = mimeType.split('/')[1]
    const file = new File([blob], `recording_${Date.now()}.${fileExtension}`, { type: mimeType })
    selectedFile.value = file
    const url = URL.createObjectURL(blob)
    recordedVideoUrl.value = url

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

  mediaRecorder.value.start()
  recording.value = true
}

const stopRecording = () => {
  if (mediaRecorder.value && recording.value) {
    mediaRecorder.value.stop()
    recording.value = false
  }
}

const takePhoto = () => {
  if (!videoElement.value) return

  recordedVideoUrl.value = ''
  mediaPreviewUrl.value = ''
  selectedFile.value = null
  results.value = []
  isImage.value = true
  isVideo.value = false
  videoActive.value = false

  const video = videoElement.value
  const canvas = document.createElement('canvas')
  canvas.width = video.videoWidth || 640
  canvas.height = video.videoHeight || 480
  const ctx = canvas.getContext('2d')
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height)
  const dataUrl = canvas.toDataURL('image/jpg')
  photoDataUrl.value = dataUrl

  if (videoElement.value) {
    videoElement.value.pause()
    videoElement.value.srcObject = null
    videoElement.value.src = ''
    videoElement.value.load()
  }

  canvas.toBlob(async (blob) => {
    const file = new File([blob], `photo_${Date.now()}.jpg`, { type: 'image/jpg' })
    selectedFile.value = file
    mediaPreviewUrl.value = URL.createObjectURL(blob)
    isImage.value = true
    isVideo.value = false
    stop()
  }, 'image/jpg')
}

const stopCamera = () => {
  stop()
  clearInterval(frameCaptureTimer)
  frameCaptureTimer = null

  if (mediaPreviewUrl.value) {
    URL.revokeObjectURL(mediaPreviewUrl.value)
    mediaPreviewUrl.value = ''
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
  clearInterval(frameCaptureTimer)
  frameCaptureTimer = null
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
  if (mediaPreviewUrl.value) {
    URL.revokeObjectURL(mediaPreviewUrl.value)
    mediaPreviewUrl.value = ''
  }

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

const detectIssues = async () => {
  if (!roadId.value || !selectedFile.value) {
    alert('请填写道路编号并上传视频/图片')
    return
  }

  const formData = new FormData()
  formData.append('file', selectedFile.value)
  formData.append('roadId', roadId.value)
  detectionInProgress.value = true

  try {
    const response = await axios.post('http://localhost:8000/road/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      withCredentials: true
    })
    results.value = response.data.map(item => ({
      road_id: item.road_id,
      description: item.description,
      full_image_base64: item.full_image_base64 || ''
    }))
  } catch (err) {
    console.error('上传失败:', err)
    alert('检测失败')
  }

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

.left-panel {
  flex: 3;
  display: flex;
  flex-direction: column;
}

.media-display {
  height: 600px;
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

.right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  max-height: 600px;
  overflow: hidden;
}

.result-list {
  flex: 1;
  overflow-y: auto;
  padding-right: 6px;
}

.result-header {
  font-size: 1.2rem;
  font-weight: bold;
  margin-bottom: 10px;
}

.result-section {
  margin-bottom: 20px;
}

.result-card {
  background: white;
  padding: 10px;
  border-left: 4px solid #1a2980;
  margin-top: 10px;
  border-radius: 5px;
}
.result-section img,
.result-card img {
  max-width: 100%;
  max-height: 300px; /* 限制最大高度 */
  height: auto;
  object-fit: contain;
  border: 1px solid #ccc;
  border-radius: 6px;
  margin-top: 10px;
  display: block;
}

</style>
