<!-- 人脸识别页面 -->
<template>
  <div class="face-recognition-container">
    <h1>人脸识别</h1>
    <div class="card">
      <div class="tabs">
        <div :class="['tab', { active: activeTab === 'camera' }]" @click="switchTab('camera')">摄像头拍照</div>
        <div :class="['tab', { active: activeTab === 'upload' }]" @click="switchTab('upload')">上传图片</div>
      </div>
      
      <!-- 摄像头区域 -->
      <div v-if="activeTab === 'camera'" class="camera-area">
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
      
      <!-- 上传区域 -->
      <div v-if="activeTab === 'upload'" class="upload-area">
        <div class="drop-zone" @dragover.prevent @drop.prevent="onFileDrop" @click="triggerUpload">
          <input type="file" ref="fileInput" style="display:none" accept="image/*" @change="onFileChange">
          <div v-if="!uploadedImage">
            <p>拖放图片到此处或点击上传</p>
            <div class="icon">+</div>
          </div>
          <img v-else :src="uploadedImage" width="320" />
        </div>
        <div v-if="uploadedImage" class="button-group">
          <button @click="cancelUpload" class="btn cancel">取消</button>
          <button @click="submitUpload" class="btn confirm">确认并识别</button>
        </div>
      </div>

      <!-- 识别结果 -->
      <div v-if="recognitionResult" class="result-area">
        <div :class="['result-box', recognitionStatus]">
          <div v-if="recognitionStatus === 'success'" class="success-result">
            <h3>识别成功</h3>
            <p>欢迎回来，{{ recognitionResult.user.username }}!</p>
            <p>邮箱: {{ recognitionResult.user.email }}</p>
            <p>识别置信度: {{ recognitionResult.user.score.toFixed(2) }}%</p>
          </div>
          <div v-else class="error-result">
            <h3>识别失败</h3>
            <p>{{ recognitionResult.msg }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'FaceRecognition',
  data() {
    return {
      activeTab: 'camera',
      videoStream: null,
      capturedImage: null,
      uploadedImage: null,
      recognitionResult: null,
      recognitionStatus: null,
      loading: false
    };
  },
  mounted() {
    if (this.activeTab === 'camera') {
      this.startCamera();
    }
  },
  beforeUnmount() {
    this.stopCamera();
  },
  methods: {
    switchTab(tab) {
      this.activeTab = tab;
      this.capturedImage = null;
      this.uploadedImage = null;
      this.recognitionResult = null;
      this.recognitionStatus = null;
      
      if (tab === 'camera') {
        this.startCamera();
      } else {
        this.stopCamera();
      }
    },
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
            alert('无法访问摄像头，请检查摄像头权限或使用图片上传。');
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
      await this.recognizeFace(this.capturedImage);
    },
    triggerUpload() {
      this.$refs.fileInput.click();
    },
    onFileChange(event) {
      const file = event.target.files[0];
      if (file) {
        this.handleFile(file);
      }
    },
    onFileDrop(event) {
      const file = event.dataTransfer.files[0];
      if (file && file.type.startsWith('image/')) {
        this.handleFile(file);
      }
    },
    handleFile(file) {
      const reader = new FileReader();
      reader.onload = e => {
        this.uploadedImage = e.target.result;
      };
      reader.readAsDataURL(file);
      this.file = file;
    },
    cancelUpload() {
      this.uploadedImage = null;
      this.file = null;
    },
    async submitUpload() {
      await this.recognizeFace(this.uploadedImage);
    },
    async recognizeFace(imageData) {
      this.loading = true;
      this.recognitionResult = null;
      this.recognitionStatus = null;
      
      try {
        // 将base64图像转换为blob
        let imageBlob;
        if (imageData.startsWith('data:image')) {
          // 从data URL创建blob
          const response = await fetch(imageData);
          imageBlob = await response.blob();
        } else {
          // 直接使用文件对象
          imageBlob = this.file;
        }
        
        // 创建FormData对象并添加图片
        const formData = new FormData();
        formData.append('image', imageBlob);
        
        // 发送到后端API
        const response = await axios.post('http://localhost:8000/face_recognition', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
        
        this.recognitionResult = response.data;
        this.recognitionStatus = 'success';
      } catch (error) {
        console.error('识别失败:', error);
        this.recognitionResult = error.response?.data || { msg: '识别请求失败' };
        this.recognitionStatus = 'error';
      } finally {
        this.loading = false;
      }
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
</style> 