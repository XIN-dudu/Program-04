<!-- 人脸识别页面 -->
<template>
  <div class="face-recognition-container">
    <!-- 新增：巨型警告弹窗 -->
    <div v-if="showBigAlert" class="big-alert-overlay">
      <div class="big-alert-box">
        <h1>警告！检测到非法入侵</h1>
        <button @click="handleAlertClose">关闭</button>
      </div>
    </div>
    <h1>人脸识别</h1>
    <div class="card">
      <!-- 只保留摄像头拍照区域 -->
      <div class="camera-area">
        <video v-if="!capturedImage" ref="video" width="320" height="240" autoplay></video>
        <img v-else :src="capturedImage" width="320" height="240" />
        <div class="button-group">
          <button v-if="!capturedImage" @click="takePhoto" class="btn">拍照</button>
          <template v-else>
            <button @click="retakePhoto" class="btn cancel">重拍</button>
            <button @click="submitPhoto" class="btn confirm">确认并识别</button>
          </template>
        </div>
      </div>
      <!-- 识别结果 -->
      <div v-if="recognitionResult" class="result-area">
        <div :class="['result-box', recognitionStatus]">
          <div v-if="recognitionStatus === 'success'" class="success-result">
            <h3>认证通过</h3>
            <p>{{ recognitionResult.msg }}</p>
            <p>比对分数: {{ recognitionResult.score && recognitionResult.score.toFixed ? recognitionResult.score.toFixed(2) : recognitionResult.score }}</p>
          </div>
          <div v-else class="error-result">
            <h3>认证未通过</h3>
            <p>{{ recognitionResult.msg }}</p>
            <p>比对分数: {{ recognitionResult.score && recognitionResult.score.toFixed ? recognitionResult.score.toFixed(2) : recognitionResult.score }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { ref } from 'vue'

export default {
  name: 'FaceRecognition',
  data() {
    return {
      videoStream: null,
      capturedImage: null,
      recognitionResult: null,
      recognitionStatus: null,
      loading: false,
      showBigAlert: false // 新增弹窗控制变量
    };
  },
  mounted() {
    if (localStorage.getItem('intrusion_alert') === '1') {
      this.showBigAlert = true;
    }
    this.startCamera();
  },
  beforeUnmount() {
    this.stopCamera();
  },
  methods: {
    startCamera() {
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices.getUserMedia({ video: true })
          .then(stream => {
            this.videoStream = stream;
            if (this.$refs.video) {
              this.$refs.video.srcObject = stream;
            }
          })
          .catch(error => {
            console.error('摄像头访问失败:', error);
            alert('无法访问摄像头，请检查摄像头权限。');
          });
      }
    },
    stopCamera() {
      if (this.videoStream) {
        this.videoStream.getTracks().forEach(track => track.stop());
        this.videoStream = null;
      }
    },
    takePhoto() {
      const video = this.$refs.video;
      const canvas = document.createElement('canvas');
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
      this.capturedImage = canvas.toDataURL('image/jpeg');
    },
    retakePhoto() {
      this.capturedImage = null;
      this.startCamera();
    },
    async submitPhoto() {
      this.loading = true;
      this.recognitionResult = null;
      this.recognitionStatus = null;
      try {
        const response = await fetch(this.capturedImage);
        const imageBlob = await response.blob();
        const formData = new FormData();
        formData.append('username', localStorage.getItem('name'));
        formData.append('image', imageBlob);
        const res = await axios.post('/api/face_verify_one_to_one/', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        const data = res.data;
        if (data.passed) {
          this.recognitionResult = { msg: '本人认证通过', score: data.score };
          this.recognitionStatus = 'success';
        } else {
          this.recognitionResult = { msg: '认证未通过/告警', score: data.score };
          this.recognitionStatus = 'error';
          this.showBigAlert = true; // 只在主动识别失败时弹窗
          localStorage.setItem('intrusion_alert', '1'); // 新增：写入入侵标记
        }
      } catch (err) {
        this.recognitionResult = { msg: err.response?.data?.msg || '比对失败', score: 0 };
        this.recognitionStatus = 'error';
        this.showBigAlert = true; // 只在主动识别异常时弹窗
        localStorage.setItem('intrusion_alert', '1'); // 新增：写入入侵标记
      } finally {
        this.loading = false;
      }
    },
    handleAlertClose() {
      this.showBigAlert = false;
      localStorage.removeItem('intrusion_alert');
      this.$router.push('/login');
    }
  }
};
</script>

<style scoped>
.face-recognition-container {
  max-width: 800px;
  margin: 40px auto;
  padding: 20px;
}

h1 {
  text-align: center;
  margin-bottom: 30px;
  color: #222;
}

.card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,.1);
  padding: 20px;
}

.tabs {
  display: flex;
  border-bottom: 1px solid #eee;
  margin-bottom: 20px;
}

.tab {
  padding: 10px 20px;
  cursor: pointer;
  margin-right: 10px;
  border-bottom: 2px solid transparent;
}

.tab.active {
  border-bottom-color: #00a1d6;
  color: #00a1d6;
}

.camera-area,
.upload-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin: 20px 0;
}

.drop-zone {
  width: 320px;
  height: 240px;
  border: 2px dashed #ccc;
  border-radius: 5px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  transition: border-color 0.2s;
}

.drop-zone:hover {
  border-color: #00a1d6;
}

.drop-zone .icon {
  font-size: 48px;
  color: #ccc;
  margin-top: 10px;
}

.button-group {
  margin-top: 15px;
  display: flex;
  gap: 10px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  background: #00a1d6;
  color: white;
}

.btn.cancel {
  background: #f5f5f5;
  color: #666;
}

.btn.confirm {
  background: #00a1d6;
}

.result-area {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.result-box {
  padding: 15px;
  border-radius: 5px;
  text-align: center;
}

.result-box.success {
  background: #f0f9eb;
  color: #67c23a;
}

.result-box.error {
  background: #fef0f0;
  color: #f56c6c;
}

.success-result h3,
.error-result h3 {
  margin-bottom: 10px;
}

.big-alert-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(255,0,0,0.7);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
}
.big-alert-box {
  background: #fff;
  border: 6px solid #ff0000;
  border-radius: 24px;
  padding: 80px 120px;
  text-align: center;
  box-shadow: 0 0 60px #ff0000;
}
.big-alert-box h1 {
  color: #ff0000;
  font-size: 3.5em;
  margin-bottom: 40px;
}
.big-alert-box button {
  font-size: 2em;
  padding: 16px 60px;
  border: none;
  border-radius: 12px;
  background: #ff0000;
  color: #fff;
  cursor: pointer;
}
</style> 