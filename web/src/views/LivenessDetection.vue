<template>
  <div class="liveness-container">
    <div v-if="showBigAlert" class="big-alert-overlay">
      <div class="big-alert-box">
        <h1>警告！检测到非法入侵</h1>
        <button @click="handleAlertClose">关闭</button>
      </div>
    </div>
    <h1>活体检测与识别</h1>
    <div style="color: #d9534f; font-size: 1.2em; margin-bottom: 18px; font-weight: bold;">该功能暂时关闭，如需使用请联系管理员。</div>
    <div v-if="step === 1">
      <p>请对准摄像头并眨眼，然后点击“开始录制”上传视频进行活体检测（视频录制时长不少于3秒）</p>
      <video ref="video" width="320" height="240" autoplay></video>
      <div class="button-group">
        <button @click="startRecording" :disabled="recording || featureClosed">开始录制</button>
        <button @click="stopRecording" :disabled="!recording || featureClosed">停止录制</button>
      </div>
      <div v-if="videoUrl">
        <video :src="videoUrl" width="320" height="240" controls></video>
        <div class="button-group">
          <button @click="uploadVideo" :disabled="loading || featureClosed">{{ loading ? '检测中...' : '上传活体检测' }}</button>
          <button @click="resetVideo" :disabled="featureClosed">重新录制</button>
        </div>
        <div v-if="loading" style="color: #007bff; margin-top: 10px;">检测中，请稍候...</div>
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
        <button @click="takePhoto" :disabled="featureClosed">拍照</button>
      </div>
      <div v-if="imageData">
        <img :src="imageData" width="320" />
        <div class="button-group">
          <button @click="uploadImage" :disabled="featureClosed">上传识别</button>
          <button @click="resetPhoto" :disabled="featureClosed">重新拍照</button>
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
      result: null,
      username: '', // 新增字段
      capturedFrames: [], // 新增：存储截帧图片blob
      captureInterval: null, // 新增：定时器句柄
      loading: false, // 新增：检测中 loading 状态
      showBigAlert: false, // 新增：入侵大弹窗
      // 软关闭开关，true=禁用所有功能，false=恢复所有功能。要开启活体检测请改为 false
      featureClosed: true // ← 改为 false 即可恢复活体检测与识别功能
    };
  },
  mounted() {
    this.startCamera();
    // 获取当前用户信息
    axios.get('/api/user/profile/').then(res => {
      if(res.data && res.data.username) {
        this.username = res.data.username;
      }
    });
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
      this.videoChunks = [];
      this.capturedFrames = [];
      this.mediaRecorder = new MediaRecorder(this.videoStream, { mimeType: 'video/webm' });
      this.mediaRecorder.ondataavailable = e => {
        if (e.data.size > 0) {
          this.videoChunks.push(e.data);
        }
      };
      this.mediaRecorder.onstop = () => {
        const blob = new Blob(this.videoChunks, { type: 'video/webm' });
        this.videoUrl = URL.createObjectURL(blob);
        // 录制结束时清除定时器
        if (this.captureInterval) {
          clearInterval(this.captureInterval);
          this.captureInterval = null;
        }
      };
      this.mediaRecorder.start();
      this.recording = true;
      // 新增：定时截帧（每秒一帧）
      this.captureInterval = setInterval(() => {
        const video = this.$refs.video;
        if (video && video.videoWidth && video.videoHeight) {
          const canvas = document.createElement('canvas');
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
          canvas.toBlob(blob => {
            if (blob) this.capturedFrames.push(blob);
          }, 'image/jpeg');
        }
      }, 1000); // 每秒截一帧
    },
    stopRecording() {
      if (this.mediaRecorder && this.recording) {
        this.mediaRecorder.stop();
        this.recording = false;
        // 录制结束时清除定时器
        if (this.captureInterval) {
          clearInterval(this.captureInterval);
          this.captureInterval = null;
        }
      }
    },
    resetVideo() {
      this.videoUrl = '';
      this.livenessResult = null;
    },
    async uploadVideo() {
      this.loading = true;
      const blob = await fetch(this.videoUrl).then(r => r.blob());
      const formData = new FormData();
      formData.append('video', blob, 'liveness.webm');
      formData.append('user_id', this.username); // 自动带上当前用户名
      this.capturedFrames.forEach((img, idx) => {
        formData.append('frame' + idx, img, `frame${idx}.jpg`);
      });
      try {
        const response = await axios.post('/api/liveness_and_face_verify/', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        this.livenessResult = response.data;
        if (!response.data.success) {
          if (response.data.fail_type === 'intrusion') {
            this.showBigAlert = true;
            localStorage.setItem('intrusion_alert', '1');
          } else {
            alert(response.data.msg || '检测失败，请重试');
          }
        }
      } catch (error) {
        this.livenessResult = { success: false, msg: error.response?.data?.msg || '检测失败' };
        alert(this.livenessResult.msg);
      } finally {
        this.loading = false;
      }
    },
    handleAlertClose() {
      this.showBigAlert = false;
      localStorage.removeItem('intrusion_alert');
      this.$router.push('/login');
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
        const response = await axios.post('/api/liveness_detection', formData, {
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