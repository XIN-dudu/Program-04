<template>
  <div :class="['liveness-mac-bg', { 'dialog-mode': dialogMode }]">
    <div :class="['liveness-mac-card', { 'dialog-mode': dialogMode }]">
      <button v-if="dialogMode" class="mac-dialog-close" @click="$emit('close')">×</button>
      <h1 class="liveness-title-mac">身份验证</h1>
      <div class="liveness-desc-mac">
        <span>请对准摄像头并眨眼，然后点击 <b>“开始录制”</b> 上传视频进行身份认证（视频录制时长不少于3秒）</span>
        <div class="liveness-tip-mac">⚠️ 请确保人脸始终在摄像头画面内，避免遮挡和离开！</div>
      </div>
      <div v-if="step === 1">
        <div class="camera-area-mac">
          <video ref="video" width="340" height="255" autoplay class="mac-video"></video>
        </div>
        <div class="button-group-mac">
          <button @click="startRecording" :disabled="recording || featureClosed || showResultDialog" class="mac-btn mac-btn-primary">开始录制</button>
          <button @click="stopRecording" :disabled="!recording || featureClosed || showResultDialog" class="mac-btn mac-btn-secondary">停止录制</button>
        </div>
        <div v-if="videoUrl" class="video-preview-mac">
          <video :src="videoUrl" width="340" height="255" controls class="mac-video"></video>
          <div class="button-group-mac">
            <button @click="uploadVideo" :disabled="loading || featureClosed || showResultDialog" class="mac-btn mac-btn-primary">{{ loading ? '检测中...' : '上传验证' }}</button>
            <button v-if="!showResultDialog" @click="resetVideo" :disabled="featureClosed" class="mac-btn mac-btn-secondary">重新录制</button>
          </div>
          <div v-if="loading" class="loading-tip-mac">检测中，请稍候...</div>
        </div>
      </div>
      <!-- 结果弹窗 -->
      <div v-if="showResultDialog" class="result-modal-mask">
        <div class="result-modal-content">
          <div v-if="finalResult && finalResult.success" class="result-success-icon">✔</div>
          <div v-else class="result-fail-icon">✖</div>
          <div class="result-title">{{ finalResult && finalResult.success ? '验证通过' : '验证失败' }}</div>
          <div class="result-msg">{{ finalResult ? finalResult.msg : '' }}</div>
          <button v-if="!dialogMode" class="mac-btn mac-btn-primary" @click="resetAll">重新录制</button>
          <button v-else class="mac-btn mac-btn-primary" @click="closeResultDialog">确定</button>
        </div>
      </div>
      <div v-else-if="step === 2">
        <div class="liveness-tip-mac">活体检测通过！请拍照上传进行身份识别</div>
        <div class="camera-area-mac">
          <video ref="video" width="340" height="255" autoplay class="mac-video"></video>
        </div>
        <div class="button-group-mac">
          <button @click="takePhoto" :disabled="featureClosed" class="mac-btn mac-btn-primary">拍照</button>
        </div>
        <div v-if="imageData" class="photo-preview-mac">
          <img :src="imageData" width="340" class="mac-photo" />
          <div class="button-group-mac">
            <button @click="uploadImage" :disabled="featureClosed" class="mac-btn mac-btn-primary">上传验证</button>
            <button @click="resetPhoto" :disabled="featureClosed" class="mac-btn mac-btn-secondary">重新拍照</button>
          </div>
        </div>
      </div>
      <!-- 统一身份验证结果弹窗 -->
      <div v-if="finalResult" class="result-area-mac">
        <h3>身份验证结果</h3>
        <div v-if="finalResult.success" class="result-success-mac">验证通过</div>
        <div v-else class="result-fail-mac">验证失败：{{ finalResult.msg }}</div>
        <div v-if="finalResult.user && finalResult.success" class="result-user-mac">识别到用户：{{ finalResult.user.username }}，相似度：{{ finalResult.score ? finalResult.score.toFixed(2) : '' }}</div>
        <!-- 新增：失败时显示重试按钮（非入侵告警时） -->
        <div v-if="!finalResult.success && !showBigAlert" style="margin-top: 20px;">
          <button @click="resetAll" class="mac-btn mac-btn-primary">重新录制</button>
        </div>
      </div>
      <!-- 巨大红色警告弹窗 -->
      <div v-if="showBigAlert" class="big-alert-overlay">
        <div class="big-alert-box">
          <h1>警告！检测到非法入侵</h1>
          <button class="big-alert-close" @click="handleAlertClose">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'LivenessDetection',
  props: {
    dialogMode: {
      type: Boolean,
      default: false
    },
    source: {
      type: String,
      default: ''
    }
  },
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
      finalResult: null, // 新增：最终身份验证结果
      username: '',
      capturedFrames: [],
      captureInterval: null,
      loading: false,
      showBigAlert: false,
      featureClosed: false,
      showResultDialog: false,
      internalSource: this.source || window.location.pathname,
    };
  },
  watch: {
    source(newVal) {
      this.internalSource = newVal || window.location.pathname;
    }
  },
  mounted() {
    this.startCamera();
    // 获取当前用户信息
    axios.get('/api/user/profile/').then(res => {
      if(res.data && res.data.username) {
        this.username = res.data.username;
      }
    });
    // 页面加载时检查localStorage
    if (localStorage.getItem('intrusion_alert') === '1') {
      this.showBigAlert = true;
    }
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
      formData.append('user_id', this.username);
      this.capturedFrames.forEach((img, idx) => {
        formData.append('frame' + idx, img, `frame${idx}.jpg`);
      });
      // 保证source有值
      formData.append('source', this.internalSource);
      try {
        const response = await axios.post('/api/liveness_and_face_verify/', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        if (response.data.success) {
          localStorage.setItem('isVerified', '1');
          this.finalResult = {
            success: true,
            user: response.data.user,
            score: response.data.score,
            msg: response.data.msg || '验证通过',
            source: this.internalSource
          };
          this.showResultDialog = true;
          if (this.dialogMode) {
            this.$emit('success', { ...this.finalResult, source: this.internalSource });
          } else {
            setTimeout(() => { this.$router.push('/home'); }, 1000);
          }
        } else {
          this.finalResult = {
            success: false,
            msg: response.data.msg || '验证失败',
            source: this.internalSource
          };
          this.showResultDialog = true;
        }
      } catch (e) {
        this.finalResult = {
          success: false,
          msg: '请求失败',
          source: this.internalSource
        };
        this.showResultDialog = true;
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
      // 兼容：如果活体检测和人脸识别分两步
      const blob = await fetch(this.imageData).then(r => r.blob());
      const formData = new FormData();
      formData.append('image', blob, 'liveness.jpg');
      try {
        const response = await axios.post('/api/liveness_detection', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        // 这里假设后端返回结构和上面一致
        if (response.data.liveness !== false && response.data.user) {
          this.finalResult = {
            success: true,
            user: response.data.user,
            score: response.data.score,
            msg: '验证通过'
          };
        } else {
          this.finalResult = {
            success: false,
            msg: response.data.msg || '身份验证失败'
          };
        }
        this.step = 3;
      } catch (error) {
        this.finalResult = { success: false, msg: error.response?.data?.msg || '检测失败' };
        this.step = 3;
      }
    },
    // 检测到入侵时调用：
    triggerIntrusionAlert() {
      localStorage.setItem('intrusion_alert', '1');
      this.showBigAlert = true;
    },
    resetAll() {
      this.showResultDialog = false; // 关闭结果弹窗
      this.finalResult = null;
      this.step = 1;
      this.videoUrl = '';
      this.livenessResult = null;
      this.imageData = null;
      this.result = null;
      this.recording = false;
      this.startCamera();
    },
    closeResultDialog() {
      this.showResultDialog = false;
      if (this.finalResult && this.finalResult.success && !this.dialogMode) {
        this.$router.push('/home');
      }
    }
  }
};
</script>

<style scoped>
.liveness-mac-bg {
  min-height: 100vh;
  background: linear-gradient(135deg, #f8fafc 0%, #e8eaf6 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}
.liveness-mac-card {
  background: #fff;
  border-radius: 22px;
  box-shadow: 0 8px 32px rgba(60,60,90,0.13), 0 1.5px 4px rgba(30,40,90,0.06);
  padding: 48px 38px 38px 38px;
  max-width: 440px;
  width: 100%;
  margin: 48px 0;
  transition: box-shadow 0.2s;
}
.liveness-title-mac {
  font-size: 2.3rem;
  font-weight: 800;
  color: #222;
  margin-bottom: 18px;
  letter-spacing: 2px;
  text-align: center;
}
.liveness-desc-mac {
  font-size: 1.08rem;
  color: #444;
  margin-bottom: 18px;
  text-align: center;
}
.liveness-tip-mac {
  color: #1976d2;
  font-size: 1.08rem;
  margin-top: 8px;
  font-weight: 600;
  text-align: center;
}
.camera-area-mac {
  display: flex;
  justify-content: center;
  margin-bottom: 18px;
}
.mac-video {
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(30,40,90,0.10);
  background: #000;
}
.button-group-mac {
  display: flex;
  justify-content: center;
  gap: 18px;
  margin-bottom: 10px;
}
.mac-btn {
  min-width: 110px;
  padding: 10px 0;
  border: none;
  border-radius: 8px;
  font-size: 1.08rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.18s, box-shadow 0.18s;
  box-shadow: 0 1.5px 4px rgba(30,40,90,0.06);
}
.mac-btn-primary {
  background: linear-gradient(90deg, #1976d2 0%, #42a5f5 100%);
  color: #fff;
}
.mac-btn-primary:disabled {
  background: #b3c6e6;
  color: #fff;
  cursor: not-allowed;
}
.mac-btn-secondary {
  background: #f5f5f5;
  color: #1976d2;
  border: 1.5px solid #b3c6e6;
}
.mac-btn-secondary:disabled {
  background: #f0f0f0;
  color: #b3c6e6;
  cursor: not-allowed;
}
.video-preview-mac, .photo-preview-mac {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 10px;
}
.mac-photo {
  border-radius: 16px;
  box-shadow: 0 2px 12px rgba(30,40,90,0.10);
  margin-bottom: 10px;
}
.result-area-mac {
  margin-top: 24px;
  text-align: center;
}
.result-success-mac {
  color: #43a047;
  font-size: 1.25rem;
  font-weight: 700;
  margin-bottom: 8px;
}
.result-fail-mac {
  color: #e53935;
  font-size: 1.15rem;
  font-weight: 700;
  margin-bottom: 8px;
}
.result-user-mac {
  color: #1976d2;
  font-size: 1.08rem;
  margin-bottom: 8px;
}
.big-alert-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(255,0,0,0.08);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
}
.big-alert-box {
  background: #fff;
  border-radius: 18px;
  box-shadow: 0 8px 32px rgba(255,0,0,0.13), 0 1.5px 4px rgba(30,40,90,0.06);
  padding: 38px 48px;
  text-align: center;
}
.big-alert-close {
  margin-top: 18px;
  background: #e53935;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 8px 24px;
  font-size: 1.08rem;
  font-weight: 600;
  cursor: pointer;
}
.loading-tip-mac {
  color: #1976d2;
  font-size: 1.08rem;
  margin-top: 8px;
  text-align: center;
}
/* 弹窗模式样式 */
.liveness-mac-bg.dialog-mode {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(30,40,90,0.13);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
}
.liveness-mac-card.dialog-mode {
  position: relative;
  box-shadow: 0 12px 48px rgba(30,40,90,0.18), 0 2px 8px rgba(30,40,90,0.10);
  margin: 0;
}
.mac-dialog-close {
  position: absolute;
  top: 18px;
  right: 18px;
  background: transparent;
  border: none;
  font-size: 2rem;
  color: #888;
  cursor: pointer;
  z-index: 10;
  transition: color 0.18s;
}
.mac-dialog-close:hover {
  color: #1976d2;
}
.result-modal-mask {
  position: fixed;
  left: 0; top: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.18);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
}
.result-modal-content {
  background: #fff;
  border-radius: 18px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.18);
  padding: 38px 48px 32px 48px;
  min-width: 320px;
  text-align: center;
  animation: popin 0.2s;
}
@keyframes popin {
  0% { transform: scale(0.8); opacity: 0; }
  100% { transform: scale(1); opacity: 1; }
}
.result-success-icon {
  font-size: 48px;
  color: #27c97a;
  margin-bottom: 12px;
}
.result-fail-icon {
  font-size: 48px;
  color: #ff4d4f;
  margin-bottom: 12px;
}
.result-title {
  font-size: 22px;
  font-weight: 600;
  margin-bottom: 8px;
}
.result-msg {
  font-size: 16px;
  color: #555;
  margin-bottom: 18px;
}
</style> 