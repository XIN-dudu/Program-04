<template>
  <div class="liveness-container">
    <!-- 巨大红色警告弹窗 -->
    <div v-if="showBigAlert" class="big-alert-overlay">
      <div class="big-alert-box">
        <h1>警告！检测到非法入侵</h1>
        <button class="big-alert-close" @click="handleAlertClose">关闭</button>
      </div>
    </div>
    <!-- 主体内容卡片 -->
    <div v-if="!showBigAlert" class="card">
      <h1 class="liveness-title">身份验证</h1>
      <div class="liveness-desc" v-if="featureClosed">该功能暂时关闭，如需使用请联系管理员。</div>
      <div v-if="step === 1">
        <p class="liveness-tip">请对准摄像头并眨眼，然后点击“开始录制”上传视频进行身份认证（视频录制时长不少于3秒）</p>
        <div class="camera-area">
          <video ref="video" width="320" height="240" autoplay></video>
        </div>
        <div class="button-group">
          <button @click="startRecording" :disabled="recording || featureClosed">开始录制</button>
          <button @click="stopRecording" :disabled="!recording || featureClosed">停止录制</button>
        </div>
        <div v-if="videoUrl" class="video-preview">
          <video :src="videoUrl" width="320" height="240" controls></video>
          <div class="button-group">
            <button @click="uploadVideo" :disabled="loading || featureClosed">{{ loading ? '检测中...' : '上传验证' }}</button>
            <button @click="resetVideo" :disabled="featureClosed">重新录制</button>
          </div>
          <div v-if="loading" class="loading-tip">检测中，请稍候...</div>
        </div>
      </div>
      <div v-else-if="step === 2">
        <p class="liveness-tip">活体检测通过！请拍照上传进行身份识别</p>
        <div class="camera-area">
          <video ref="video" width="320" height="240" autoplay></video>
        </div>
        <div class="button-group">
          <button @click="takePhoto" :disabled="featureClosed">拍照</button>
        </div>
        <div v-if="imageData" class="photo-preview">
          <img :src="imageData" width="320" />
          <div class="button-group">
            <button @click="uploadImage" :disabled="featureClosed">上传验证</button>
            <button @click="resetPhoto" :disabled="featureClosed">重新拍照</button>
          </div>
        </div>
      </div>
      <!-- 统一身份验证结果弹窗 -->
      <div v-if="finalResult" class="result-area">
        <h3>身份验证结果</h3>
        <div v-if="finalResult.success" class="result-success">验证通过</div>
        <div v-else class="result-fail">验证失败：{{ finalResult.msg }}</div>
        <div v-if="finalResult.user && finalResult.success" class="result-user">识别到用户：{{ finalResult.user.username }}，相似度：{{ finalResult.score ? finalResult.score.toFixed(2) : '' }}</div>
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
      finalResult: null, // 新增：最终身份验证结果
      username: '',
      capturedFrames: [],
      captureInterval: null,
      loading: false,
      showBigAlert: false,
      featureClosed: false
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
      try {
        const response = await axios.post('/api/liveness_and_face_verify/', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        // 直接判断最终结果
        if (response.data.success) {
          // 通过则直接显示最终结果
          this.finalResult = {
            success: true,
            user: response.data.user,
            score: response.data.score,
            msg: response.data.msg || '验证通过'
          };
        } else {
          // 失败时区分原因
          this.finalResult = {
            success: false,
            msg: response.data.msg || (response.data.fail_type === 'liveness' ? '活体检测未通过' : (response.data.fail_type === 'intrusion' ? '检测到非法入侵' : '身份验证失败'))
          };
          if (response.data.fail_type === 'intrusion') {
            this.showBigAlert = true;
            localStorage.setItem('intrusion_alert', '1');
          }
        }
        // 只要有结果就不再进入step2
        this.step = 3;
      } catch (error) {
        this.finalResult = { success: false, msg: error.response?.data?.msg || '检测失败' };
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
    }
  }
};
</script>

<style scoped>
.liveness-container {
  max-width: 800px;
  margin: 40px auto;
  padding: 20px;
  background: #f7f8fa;
  min-height: 100vh;
}
.card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0,0,0,.1);
  padding: 32px 32px 24px 32px;
  margin: 0 auto;
  max-width: 520px;
}
.liveness-title {
  text-align: left;
  font-size: 2.1em;
  color: #222;
  font-weight: 700;
  margin-bottom: 18px;
  letter-spacing: 1px;
}
.liveness-desc {
  color: #d9534f;
  font-size: 1.1em;
  margin-bottom: 18px;
  font-weight: bold;
}
.liveness-tip {
  color: #444;
  font-size: 1.08em;
  margin-bottom: 18px;
}
.camera-area {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 18px;
}
.button-group {
  margin-top: 10px;
  display: flex;
  justify-content: center;
  gap: 16px;
}
.button-group button {
  padding: 8px 22px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 15px;
  background: #00a1d6;
  color: white;
  font-weight: 500;
  transition: background 0.2s;
}
.button-group button:disabled {
  background: #e0e0e0;
  color: #aaa;
  cursor: not-allowed;
}
.button-group button:hover:not(:disabled) {
  background: #007bb8;
}
.video-preview, .photo-preview {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 10px;
}
.loading-tip {
  color: #007bff;
  margin-top: 10px;
}
.result-area {
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #eee;
  text-align: center;
}
.result-success {
  color: #67c23a;
  font-size: 1.3em;
  font-weight: bold;
}
.result-fail {
  color: #f56c6c;
  font-size: 1.3em;
  font-weight: bold;
}
.result-user {
  margin-top: 8px;
  color: #333;
}
.big-alert-overlay {
  position: fixed; left: 0; top: 0; right: 0; bottom: 0;
  background: #ff3b3b !important;
  z-index: 9999;
  display: flex; align-items: center; justify-content: center;
}
.big-alert-box {
  background: #fff;
  border-radius: 18px;
  box-shadow: 0 8px 40px rgba(255,0,0,0.18);
  padding: 60px 60px 40px 60px;
  min-width: 420px;
  max-width: 90vw;
  text-align: center;
}
.big-alert-box h1 {
  color: #ff2222;
  font-size: 2.4rem;
  font-weight: bold;
  margin-bottom: 36px;
  letter-spacing: 2px;
}
.big-alert-close {
  background: #ff3b3b;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 1.3rem;
  padding: 12px 38px;
  margin-top: 18px;
  cursor: pointer;
  font-weight: 600;
  transition: background 0.2s;
}
.big-alert-close:hover {
  background: #d90000;
}
</style> 