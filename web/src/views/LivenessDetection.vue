<template>
  <div class="liveness-container">
    <h1>活体检测与识别</h1>
    <div v-if="!imageData">
      <p>请对准摄像头，点击“拍照”上传进行活体检测与识别</p>
      <video ref="video" width="320" height="240" autoplay></video>
      <div class="button-group">
        <button @click="takePhoto">拍照</button>
      </div>
    </div>
    <div v-else>
      <p>拍照完成，请点击上传进行活体检测与识别</p>
      <img :src="imageData" width="320" />
      <div class="button-group">
        <button @click="uploadImage">上传检测</button>
        <button @click="reset">重新拍照</button>
      </div>
    </div>
    <div v-if="result">
      <h3>检测结果</h3>
      <div v-if="result.liveness !== false && result.user">
        <p style="color:green">活体检测通过，识别到用户：{{ result.user.user_id }}，相似度：{{ result.score ? result.score.toFixed(2) : '' }}</p>
      </div>
      <div v-else-if="result.liveness !== false">
        <p style="color:orange">活体检测通过，但未识别到已知用户</p>
      </div>
      <div v-else>
        <p style="color:red">活体检测未通过：{{ result.msg }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'LivenessDetection',
  data() {
    return {
      videoStream: null,
      imageData: null,
      result: null
    };
  },
  mounted() {
    this.startCamera();
  },
  beforeUnmount() {
    this.stopCamera();
  },
  methods: {
    startCamera() {
      navigator.mediaDevices.getUserMedia({ video: true, audio: false })
        .then(stream => {
          this.videoStream = stream;
          this.$refs.video.srcObject = stream;
        })
        .catch(err => {
          alert('无法访问摄像头: ' + err);
        });
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
      this.imageData = canvas.toDataURL('image/jpeg');
      this.stopCamera();
    },
    reset() {
      this.imageData = null;
      this.result = null;
      this.startCamera();
    },
    async uploadImage() {
      const blob = await fetch(this.imageData).then(r => r.blob());
      const formData = new FormData();
      formData.append('image', blob, 'liveness.jpg');
      try {
        const response = await axios.post('http://localhost:8000/liveness_detection', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        this.result = response.data;
      } catch (error) {
        this.result = { liveness: false, msg: error.response?.data?.msg || '检测失败' };
      }
    }
  }
};
</script>

<style scoped>
.liveness-container {
  max-width: 500px;
  margin: 40px auto;
  background: #fff;
  padding: 32px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  text-align: center;
}
.button-group {
  margin-top: 16px;
  display: flex;
  justify-content: center;
  gap: 16px;
}
</style> 