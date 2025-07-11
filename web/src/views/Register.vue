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
            <input type="file" id="faceImages" multiple accept="image/*" @change="onFileChange" />
            <button type="button" @click="openCamera" style="margin-left:10px;">打开摄像头拍照</button>
            <div v-if="faceImages.length" style="margin-top:8px;">
              <span v-for="(img, idx) in faceImages" :key="idx" style="display:inline-block;margin:2px;position:relative;">
                <img :src="img.preview" style="width:60px;height:60px;object-fit:cover;border:1px solid #ccc;" />
                <span @click="removeImage(idx)" style="position:absolute;top:0;right:0;background:#fff;color:#e74c3c;cursor:pointer;font-size:16px;">×</span>
              </span>
            </div>
            <!-- 摄像头弹窗 -->
            <div v-if="showCamera" class="camera-modal">
              <video ref="video" autoplay style="width:240px;height:180px;"></video>
              <br />
              <button type="button" @click="takePhoto">拍照</button>
              <button type="button" @click="closeCamera">关闭</button>
            </div>
          </div>
          <button type="submit" class="submit-btn" :disabled="loading">{{ loading ? '注册中...' : '注册' }}</button>
        </form>
        <div v-if="errorMsg" class="error">{{ errorMsg }}</div>
        <div v-if="successMsg" class="success">{{ successMsg }}</div>
        <!-- 注册按钮下方加跳转登录按钮 -->
        <button type="button" class="switch-btn" @click="$router.push('/login')">已有账号？去登录</button>
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
  overflow-y: auto; /* 增加垂直滚动条 */
  z-index: 0;
  background: url('@/assets/login-bg.gif') center center / cover no-repeat;
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
  max-width: 380px;
  background: rgba(255,255,255,0.85);
  border-radius: 24px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.18);
  padding: 20px 16px 24px 16px;
}
.form-title {
  text-align: center;
  margin-bottom: 18px;
  color: #222;
  font-size: 1.5rem;
  font-weight: bold;
  letter-spacing: 2px;
}
.form-group {
  margin-bottom: 14px;
}
.form-group label {
  display: block;
  margin-bottom: 5px;
  color: #666;
}
.form-group input, .form-group select {
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 1rem;
  background: rgba(255,255,255,0.9);
}
.form-group input:focus, .form-group select:focus {
  border-color: #00a1d6;
  outline: none;
}
.submit-btn, .switch-btn {
  width: 100%;
  background: #00a1d6;
  color: white;
  padding: 12px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: bold;
  transition: background 0.2s;
  margin: 14px 0 0 0;
  display: block;
}
.switch-btn {
  background: #fff;
  color: #00a1d6;
  border: 1px solid #00a1d6;
  margin: 12px 0 0 0;
}
.switch-btn:hover {
  background: #e6f7ff;
  color: #00a1d6;
}
.submit-btn:hover {
  background: #00b5e5;
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
.auth-box form {
  display: flex;
  flex-direction: column;
  align-items: center;
}
.auth-box .form-group {
  width: 100%;
}
</style>