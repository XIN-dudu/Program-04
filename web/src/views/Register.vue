<!-- 注册 -->
<template>
  <div class="login-bg">
    <div class="auth-container">
      <div class="auth-box">
        <h2 class="form-title">注册账号</h2>
        <form @submit.prevent="onSubmit" enctype="multipart/form-data">
          <div class="form-group">
            <label for="username">账户：</label>
            <input type="text" id="username" v-model="form.username" required />
          </div>
          <div class="form-group">
            <label for="password">密码：</label>
            <input type="password" id="password" v-model="form.password" required />
          </div>
          <div class="form-group">
            <label for="confirmPassword">确认密码：</label>
            <input type="password" id="confirmPassword" v-model="form.confirmPassword" required />
          </div>
          <div class="form-group">
            <label for="email">邮箱：</label>
            <input type="email" id="email" v-model="form.email" required />
          </div>
          <div class="form-group">
            <label for="phone">手机号：</label>
            <input type="tel" id="phone" v-model="form.phone" required />
          </div>
          <div class="form-group">
            <label for="permission">用户角色：</label>
            <select id="permission" v-model="form.permission" required>
              <option value="0">普通用户</option>
              <option value="1">维修工</option>
            </select>
          </div>
          <div class="form-group">
            <label for="faceImages">人脸图片（至少三张）：</label>
            <div class="file-upload-wrapper">
              <button type="button" class="code-btn" @click="() => $refs.fileInput.click()">选择文件</button>
              <span class="file-upload-text">{{ faceImages.length ? faceImages.map(f => f.name || '已选图片').join('、') : '未选择文件' }}</span>
              <input type="file" id="faceImages" ref="fileInput" multiple accept="image/*" @change="onFileChange" style="display:none;" />
              <button type="button" @click="openCamera" class="code-btn" style="margin-left:10px;">打开摄像头拍照</button>
            </div>
            <div v-if="faceImages.length" style="margin-top:8px;">
              <span v-for="(img, idx) in faceImages" :key="idx" style="display:inline-block;margin:2px;position:relative;">
                <img :src="img.preview" style="width:60px;height:60px;object-fit:cover;border:1.5px solid #b6e6fa;" />
                <span @click="removeImage(idx)" style="position:absolute;top:0;right:0;background:#fff;color:#e74c3c;cursor:pointer;font-size:16px;">×</span>
              </span>
            </div>
            <!-- 摄像头弹窗 -->
            <div v-if="showCamera" class="camera-modal">
              <video ref="video" autoplay style="width:240px;height:180px;"></video>
              <br />
              <button type="button" @click="takePhoto" class="code-btn">拍照</button>
              <button type="button" @click="closeCamera" class="code-btn" style="margin-left:10px;">关闭</button>
            </div>
          </div>
          <button type="submit" class="submit-btn" :disabled="loading">{{ loading ? '注册中...' : '注册' }}</button>
        </form>
        <div v-if="errorMsg" class="error">{{ errorMsg }}</div>
        <div v-if="successMsg" class="success">{{ successMsg }}</div>
        <!-- 已有账号去登录，改为文字链接 -->
        <router-link to="/login" class="switch-link">已有账号？去登录</router-link>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { useRouter } from 'vue-router'

export default {
  name: "Register",
  data() {
    return {
      form: {
        username: '',
        password: '',
        confirmPassword: '',
        email: '',
        phone: '',
        permission: '0'  // 默认普通用户
      },
      faceImages: [], // 存储图片文件
      errorMsg: '',
      successMsg: '',
      showCamera: false,
      videoStream: null,
      loading: false // 新增loading状态
    };
  },
  mounted() {
    const regEmail = localStorage.getItem('register_email');
    if (regEmail) {
      this.form.email = regEmail;
      localStorage.removeItem('register_email');
    }
  },
  methods: {
    onFileChange(e) {
      const files = Array.from(e.target.files);
      this.faceImages.push(...files.map(file => {
        file.preview = URL.createObjectURL(file);
        return file;
      }));
    },
    removeImage(idx) {
      this.faceImages.splice(idx, 1);
    },
    openCamera() {
      this.showCamera = true;
      navigator.mediaDevices.getUserMedia({ video: true }).then(stream => {
        this.videoStream = stream;
        this.$refs.video.srcObject = stream;
      });
    },
    closeCamera() {
      this.showCamera = false;
      if (this.videoStream) {
        this.videoStream.getTracks().forEach(track => track.stop());
        this.videoStream = null;
      }
    },
    takePhoto() {
      const video = this.$refs.video;
      const canvas = document.createElement('canvas');
      canvas.width = video.videoWidth || 240;
      canvas.height = video.videoHeight || 180;
      canvas.getContext('2d').drawImage(video, 0, 0, canvas.width, canvas.height);
      canvas.toBlob(blob => {
        blob.preview = URL.createObjectURL(blob);
        this.faceImages.push(blob);
      }, 'image/jpeg');
    },
    async onSubmit() {
      if (this.form.password !== this.form.confirmPassword) {
        this.errorMsg = '两次输入的密码不一致！';
        this.successMsg = '';
        alert(this.errorMsg);
        return;
      }
      if (this.faceImages.length < 3) {
        this.errorMsg = '请上传或拍照至少三张人脸图片！';
        alert(this.errorMsg);
        return;
      }
      this.errorMsg = '';
      this.successMsg = '';
      this.loading = true; // 开始loading
      this.router = useRouter();
      try {
        const formData = new FormData();
        formData.append('username', this.form.username);
        formData.append('password', this.form.password);
        formData.append('email', this.form.email);
        formData.append('phone', this.form.phone);
        formData.append('permission', this.form.permission);
        this.faceImages.forEach((file, idx) => {
          formData.append('face_images', file);
        });
        const res = await axios.post('/api/register', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        this.successMsg = res.data.msg || '注册成功';
        this.loading = false;
        // 注册成功弹窗，确认后跳转到登录页
        alert(this.successMsg);
        this.$router.push('/login');
      } catch (err) {
        this.loading = false;
        console.log('注册失败详细信息:', err.response);
        this.errorMsg = (err.response && err.response.data && (err.response.data.msg || JSON.stringify(err.response.data)))
          || err.message
          || '注册失败';
        alert(this.errorMsg);
      }
    }
  }
};
</script>

<style scoped>
.login-bg {
  position: fixed;
  left: 0; right: 0; top: 0; bottom: 0;
  width: 100vw;
  height: 100vh;
  overflow-y: auto;
  z-index: 0;
  background: url('@/assets/login-bg.gif') center center / cover no-repeat;
}
/* 深色半透明遮罩 */
.login-bg::before {
  content: '';
  position: absolute;
  left: 0; right: 0; top: 0; bottom: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(20, 30, 60, 0.38);
  z-index: 0;
}
.auth-container {
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
}
.auth-box {
  width: 100%;
  max-width: 420px;
  background: rgba(255,255,255,0.82);
  border-radius: 28px;
  box-shadow: 0 10px 40px rgba(0,0,0,0.22);
  padding: 48px 24px 32px 24px;
  margin: 32px 0;
  position: relative;
  z-index: 2;
  border: 2px solid #b6e6fa;
}
.form-title {
  text-align: center;
  margin-bottom: 32px;
  color: #1a2236;
  font-size: 2.2rem;
  font-weight: 800;
  letter-spacing: 2px;
  text-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.form-group {
  margin-bottom: 22px;
}
.form-group label {
  display: block;
  margin-bottom: 7px;
  color: #3a466e;
  font-weight: 600;
  letter-spacing: 1px;
}
.form-group input, .form-group select {
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  padding: 13px 14px;
  border: 1.5px solid #b6e6fa;
  border-radius: 12px;
  font-size: 1.08rem;
  background: rgba(255,255,255,0.92);
  box-shadow: 0 2px 8px rgba(30,40,90,0.04);
  transition: border 0.2s, box-shadow 0.2s;
}
.form-group input:focus, .form-group select:focus {
  border-color: #00a1d6;
  outline: none;
  box-shadow: 0 0 0 2px #b6e6fa;
}
.submit-btn {
  width: 100%;
  background: linear-gradient(90deg,#00a1d6 0%,#00c6fb 100%);
  color: white;
  padding: 15px 0;
  border: none;
  border-radius: 16px;
  cursor: pointer;
  font-size: 1.18rem;
  font-weight: bold;
  transition: background 0.2s, box-shadow 0.2s;
  margin-top: 12px;
  box-shadow: 0 4px 16px rgba(0,161,214,0.10);
  letter-spacing: 2px;
  display: block;
}
.submit-btn:hover {
  background: linear-gradient(90deg,#00b5e5 0%,#00a1d6 100%);
  box-shadow: 0 6px 24px rgba(0,161,214,0.18);
}
.switch-btn {
  width: 100%;
  background: #fff;
  color: #00a1d6;
  border: 1.5px solid #00a1d6;
  border-radius: 12px;
  margin: 18px 0 0 0;
  font-size: 1.05rem;
  font-weight: 600;
  padding: 12px 0;
  transition: background 0.18s, color 0.18s;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.switch-btn:hover {
  background: #e6f7fd;
  color: #00a1d6;
}
.error {
  color: #e74c3c;
  margin-top: 10px;
  text-align: center;
}
.success {
  color: #2ecc40;
  margin-top: 10px;
  text-align: center;
}
.camera-modal {
  position: fixed;
  left: 0; right: 0; top: 0; bottom: 0;
  background: rgba(0,0,0,0.3);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
/* 人脸图片预览美化 */
.form-group span[style*='display:inline-block'] img {
  border: 1.5px solid #b6e6fa !important;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(30,40,90,0.04);
}
.form-group span[style*='display:inline-block'] span {
  top: -8px !important;
  right: -8px !important;
  background: #fff !important;
  color: #e74c3c !important;
  border-radius: 50%;
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px !important;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}
.auth-box form {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.auth-box .form-group {
  width: 100%;
}
/* 统一按钮样式（如验证码、文件、拍照等） */
.code-btn, .file-btn::-webkit-file-upload-button, .file-btn::file-selector-button {
  background: #f3f7fa;
  color: #00a1d6;
  border: none;
  border-radius: 8px;
  padding: 6px 18px;
  font-size: 1rem;
  font-weight: 600;
  transition: background 0.18s, color 0.18s;
  margin-top: 6px;
  margin-left: 0;
  margin-bottom: 0;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
  cursor: pointer;
}
.code-btn:hover, .file-btn::-webkit-file-upload-button:hover, .file-btn::file-selector-button:hover {
  background: #e6f7fd;
  color: #00a1d6;
}
/* 文字链接样式 */
.switch-link {
  color: #00a1d6;
  cursor: pointer;
  font-size: 1.01rem;
  display: block;
  text-align: center;
  margin-top: 20px;
  text-decoration: underline;
  font-weight: 500;
}
.file-upload-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 6px;
}
.file-upload-text {
  color: #222;
  font-size: 1rem;
  background: rgba(255,255,255,0.92);
  border-radius: 8px;
  padding: 6px 12px;
  border: 1.5px solid #b6e6fa;
  min-width: 120px;
  box-shadow: 0 2px 8px rgba(30,40,90,0.04);
}
</style>