<!-- 注册 -->
<template>
  <div class="register-container">
    <h1>注册账号</h1>
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
      <button type="submit">注册</button>
    </form>
    <div v-if="errorMsg" class="error">{{ errorMsg }}</div>
    <div v-if="successMsg" class="success">{{ successMsg }}</div>
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
        phone: ''
      },
      faceImages: [], // 存储图片文件
      errorMsg: '',
      successMsg: '',
      showCamera: false,
      videoStream: null
    };
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
      this.router = useRouter();
      try {
        const formData = new FormData();
        formData.append('username', this.form.username);
        formData.append('password', this.form.password);
        formData.append('email', this.form.email);
        formData.append('phone', this.form.phone);
        this.faceImages.forEach((file, idx) => {
          formData.append('face_images', file);
        });
        const res = await axios.post('http://localhost:8000/register', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        this.successMsg = res.data.msg || '注册成功';
        this.$router.push('/login');
      } catch (err) {
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
.register-container {
  max-width: 400px;
  margin: 40px auto;
  padding: 24px;
  border: 1px solid #eee;
  border-radius: 8px;
  background: #fafbfc;
}
.form-group {
  margin-bottom: 18px;
}
label {
  display: block;
  margin-bottom: 6px;
  font-weight: bold;
}
input {
  width: 100%;
  padding: 8px;
  box-sizing: border-box;
  border: 1px solid #ccc;
  border-radius: 4px;
}
button {
  width: 100%;
  padding: 10px;
  background: #409eff;
  color: #fff;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  cursor: pointer;
}
button:hover {
  background: #66b1ff;
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
</style>