<template>
  <div class="liveness-container">
    <h1>活体检测与识别</h1>
    <div v-if="step === 1">
      <p>请对准摄像头并眨眼，然后点击“开始录制”上传视频进行活体检测（视频录制时长不少于3秒）</p>
      <video ref="video" width="320" height="240" autoplay></video>
      <div class="button-group">
        <button @click="startRecording" :disabled="recording">开始录制</button>
        <button @click="stopRecording" :disabled="!recording">停止录制</button>
      </div>
      <div v-if="videoUrl">
        <video :src="videoUrl" width="320" height="240" controls></video>
        <div class="button-group">
          <button @click="uploadVideo">上传活体检测</button>
          <button @click="resetVideo">重新录制</button>
        </div>
      </div>
      <div v-if="livenessResult">
        <h3>活体检测结果</h3>
        <p :style="{color: livenessResult.liveness ? 'green' : 'red'}">{{ livenessResult.msg }}</p>
      </div>
    </div>
    <div v-else-if="step === 2">
      <p>活体检测通过！请拍照上传进行身份识别</p>
      <video ref="video" width="320" height="240" autoplay></video>
      <div class="button-group">
        <button @click="takePhoto">拍照</button>
      </div>
      <div v-if="imageData">
        <img :src="imageData" width="320" />
        <div class="button-group">
          <button @click="uploadImage">上传识别</button>
          <button @click="resetPhoto">重新拍照</button>
        </div>
      </div>
      <div v-if="result">
        <h3>识别结果</h3>
        <div v-if="result.liveness !== false && result.user">
          <p style="color:green">识别到用户：{{ result.user.username }}，相似度：{{ result.score ? result.score.toFixed(2) : '' }}</p>
        </div>
        <div v-else-if="result.liveness !== false">
          <p style="color:orange">未识别到已知用户</p>
        </div>
        <div v-else>
          <p style="color:red">识别失败：{{ result.msg }}</p>
        </div>
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
      step: 1,
      recording: false,
      videoStream: null,
      mediaRecorder: null,
      videoChunks: [],
      videoUrl: '',
      livenessResult: null,
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
    // 活体检测相关
    startRecording() {
      // 注释掉录制功能，让按钮无效
      // this.videoChunks = [];
      // this.mediaRecorder = new MediaRecorder(this.videoStream, { mimeType: 'video/webm' });
      // this.mediaRecorder.ondataavailable = e => {
      //   if (e.data.size > 0) {
      //     this.videoChunks.push(e.data);
      //   }
      // };
      // this.mediaRecorder.onstop = () => {
      //   const blob = new Blob(this.videoChunks, { type: 'video/webm' });
      //   this.videoUrl = URL.createObjectURL(blob);
      // };
      // this.mediaRecorder.start();
      // this.recording = true;
    },
    stopRecording() {
      // 注释掉停止录制功能
      // if (this.mediaRecorder && this.recording) {
      //   this.mediaRecorder.stop();
      //   this.recording = false;
      // }
    },
    resetVideo() {
      this.videoUrl = '';
      this.livenessResult = null;
    },
    async uploadVideo() {
      // 上传后不再自动跳转到第二步
      const blob = await fetch(this.videoUrl).then(r => r.blob());
      const formData = new FormData();
      formData.append('video', blob, 'liveness.webm');
      try {
        const response = await axios.post('http://localhost:8000/liveness_check', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        this.livenessResult = response.data;
        // 注释掉自动跳转
        // if (response.data.liveness) {
        //   this.step = 2;
        //   this.livenessResult = null;
        //   this.resetVideo();
        //   this.startCamera();
        // }
      } catch (error) {
        this.livenessResult = { liveness: false, msg: error.response?.data?.msg || '检测失败' };
      }
    },
    // 拍照识别相关
    takePhoto() {
      const video = this.$refs.video;
      const canvas = document.createElement('canvas');
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
      this.imageData = canvas.toDataURL('image/jpeg');
      this.stopCamera();
    },
    resetPhoto() {
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