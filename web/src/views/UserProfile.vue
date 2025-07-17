<template>
  <div class="profile-bg-light">
    <div class="profile-card-light">
      <div class="profile-header-light">
        <div class="profile-banner-light"></div>
        <div class="profile-avatar-block">
          <img :src="avatarUrl" class="avatar-light" @click="onAvatarClick" />
          <input type="file" ref="avatarInput" style="display:none" @change="onAvatarChange" />
        </div>
      </div>
      <div class="profile-info-card-light">
        <h2 class="profile-title">个人信息</h2>
        <div class="info-row-light"><span class="info-label-light">用户名</span><span class="info-value-center">{{ user.username }}</span><button class="edit-btn-light fixed-btn" disabled>固定</button></div>
        <div class="info-row-light"><span class="info-label-light">电子邮箱</span><span class="info-value-center">{{ user.email }}</span><button class="edit-btn-light" @click="onEditEmail">编辑</button></div>
        <div class="info-row-light">
          <span class="info-label-light">手机号</span>
          <span class="info-value-center">{{ user.phone }}</span>
          <button class="edit-btn-light" @click="openPhoneEdit">编辑</button>
        </div>
        <!-- 手机号编辑弹窗 -->
        <div v-if="showPhoneEdit" class="modal-mask-light">
          <div class="modal-content-light">
            <h3>修改手机号</h3>
            <div class="form-row-modal-light">
              <label>新手机号：</label>
              <input v-model="editPhone" maxlength="20" />
            </div>
            <div style="text-align:right;margin-top:18px;">
              <button class="btn-light cancel" @click="showPhoneEdit = false">取消</button>
              <button class="btn-light" @click="submitPhoneEdit">保存</button>
            </div>
          </div>
        </div>
        <div class="info-row-light permission-row-fix"><span class="info-label-light">权限</span><span class="info-value-center permission-value">{{ permissionText }}</span><button class="edit-btn-light fixed-btn" disabled>固定</button></div>
        <div class="info-row-light no-border info-row-password-btn"><button class="edit-btn-light left-btn" @click="onEditAll">修改密码</button></div>
      </div>
    </div>
    <!-- 编辑邮箱弹窗 -->
    <div v-if="showEditEmail" class="modal-mask-light">
      <div class="modal-content-light">
        <h3>修改邮箱</h3>
        <div class="form-row-modal-light">
          <label>新邮箱：</label>
          <input v-model="editEmail" type="email" />
          <button class="btn-light" @click="sendEmailCode">发送验证码</button>
        </div>
        <div class="form-row-modal-light">
          <label>验证码：</label>
          <input v-model="emailCode" />
        </div>
        <div style="text-align:right;margin-top:18px;">
          <button class="btn-light cancel" @click="showEditEmail = false">取消</button>
          <button class="btn-light" @click="updateEmail">保存</button>
        </div>
      </div>
    </div>
    <!-- 编辑用户名弹窗 -->
    <div v-if="showEditNick" class="modal-mask-light">
      <div class="modal-content-light">
        <h3>修改用户名</h3>
        <div class="form-row-modal-light">
          <label>新用户名：</label>
          <input v-model="editNick" />
        </div>
        <div style="text-align:right;margin-top:18px;">
          <button class="btn-light cancel" @click="showEditNick = false">取消</button>
          <button class="btn-light" @click="updateNick">保存</button>
        </div>
      </div>
    </div>
    <!-- 修改密码弹窗 -->
    <div v-if="showEditAll" class="modal-mask-light">
      <div class="modal-content-light">
        <h3>修改密码</h3>
        <div class="form-row-modal-light">
          <label>新密码：</label>
          <input type="password" v-model="newPassword" />
        </div>
        <div class="form-row-modal-light">
          <label>确认新密码：</label>
          <input type="password" v-model="confirmPassword" />
        </div>
        <div style="text-align:right;margin-top:18px;">
          <button class="btn-light cancel" @click="showEditAll = false">取消</button>
          <button class="btn-light" @click="updatePassword">修改密码</button>
        </div>
      </div>
    </div>
    <!-- 活体检测弹窗 -->
    <LivenessDetection
      v-if="showLivenessDialog"
      :dialogMode="true"
      :source="livenessSource"
      @success="onLivenessSuccess"
      @close="showLivenessDialog = false"
    />
  </div>
</template>

<script>
import axios from 'axios';
import LivenessDetection from './LivenessDetection.vue';
export default {
  components: { LivenessDetection },
  data() {
    return {
      user: {},
      avatarUrl: '',
      email: '',
      emailCode: '',
      editEmail: '',
      showEditEmail: false,
      showEditNick: false,
      showEditAll: false,
      editNick: '',
      newPassword: '',
      confirmPassword: '',
      showPhoneEdit: false,
      editPhone: '',
      showLivenessDialog: false,
      pendingAction: null,
      livenessSource: '',
    }
  },
  computed: {
    permissionText() {
      if (this.user.permission == 2 || this.user.permission === '2') return '管理员';
      if (this.user.permission == 1 || this.user.permission === '1') return '维修工';
      return '普通用户';
    }
  },
  created() {
    const API_BASE = process.env.VUE_APP_API_BASE || 'http://localhost:8000';
    axios.get(API_BASE + '/api/user/profile/', { withCredentials: true })
      .then(res => {
        this.user = res.data;
        // 头像url直接用 /api/avatar/用户名/，如果没有则用默认头像
        this.avatarUrl = this.user.username
          ? (API_BASE + '/api/avatar/' + this.user.username + '/')
          : require('@/assets/default-avatar.png');
        // 同步localStorage
        localStorage.setItem('user', JSON.stringify(this.user));
        this.email = this.user.email;
        this.editNick = this.user.username;
      })
      .catch(() => {
        // 兜底：localStorage
        let user = localStorage.getItem('user');
        if (user) {
          this.user = JSON.parse(user);
          this.avatarUrl = this.user.username
            ? (API_BASE + '/api/avatar/' + this.user.username + '/')
            : require('@/assets/default-avatar.png');
          this.email = this.user.email;
          this.editNick = this.user.username;
        }
      });
  },
  methods: {
    onAvatarClick() {
      this.$refs.avatarInput.click();
    },
    onAvatarChange(e) {
      const file = e.target.files[0];
      this.avatarUrl = URL.createObjectURL(file); // 本地预览
      // 上传到后端
      const formData = new FormData();
      formData.append('username', this.user.username);
      formData.append('avatar', file);
      axios.post((process.env.VUE_APP_API_BASE || 'http://localhost:8000') + '/api/upload_avatar/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      }).then(res => {
        alert(res.data.msg);
        if (res.data.avatar_url) {
          // 上传成功后，直接用 /api/avatar/用户名/ 作为头像url
          const API_BASE = process.env.VUE_APP_API_BASE || '';
          this.avatarUrl = API_BASE + '/api/avatar/' + this.user.username + '/';
          // 更新localStorage中的头像字段，保证刷新/登录后头像不丢失
          let user = localStorage.getItem('user') ? JSON.parse(localStorage.getItem('user')) : {};
          user.avatar = '/api/avatar/' + this.user.username + '/';
          localStorage.setItem('user', JSON.stringify(user));
        }
      });
    },
    sendEmailCode() {
      axios.post('http://localhost:8000/api/check_email_available/', {
        email: this.editEmail
      }).then(res => {
        if (!res.data.available) {
          alert('该邮箱已被注册');
        } else {
          axios.post('http://localhost:8000/api/send_email_code/', { email: this.editEmail }).then(res2 => {
            alert(res2.data.msg);
          });
        }
      });
    },
    updateEmail() {
      axios.post('http://localhost:8000/api/update_profile/', {
        username: this.user.username,
        email: this.editEmail,
        email_code: this.emailCode
      }).then(res => {
        alert(res.data.msg);
        this.user.email = this.editEmail;
        this.showEditEmail = false;
      });
    },
    updateNick() {
      // 调用后端接口修改用户名并校验唯一性
      axios.post('http://localhost:8000/api/update_profile/', {
        username: this.user.username,
        new_username: this.editNick
      }).then(res => {
        alert(res.data.msg);
        // 更新localStorage和页面显示
        this.user.username = this.editNick;
        let user = localStorage.getItem('user') ? JSON.parse(localStorage.getItem('user')) : {};
        user.username = this.editNick;
        localStorage.setItem('user', JSON.stringify(user));
        this.showEditNick = false;
        window.location.reload();
      });
    },
    updatePassword() {
      if (this.newPassword !== this.confirmPassword) {
        alert('两次输入密码不一致');
        return;
      }
      axios.post('http://localhost:8000/api/update_profile/', {
        username: this.user.username,
        password: this.newPassword
      }).then(res => {
        alert(res.data.msg);
        this.showEditAll = false;
      });
    },
    submitPhoneEdit() {
      if (!this.editPhone) {
        alert('请输入新手机号');
        return;
      }
      axios.post('http://localhost:8000/api/update_profile/', {
        username: this.user.username,
        phone: this.editPhone
      }).then(res => {
        alert(res.data.msg);
        this.user.phone = this.editPhone;
        this.showPhoneEdit = false;
      });
    },
    // 拦截邮箱编辑
    onEditEmail() {
      this.pendingAction = 'editEmail';
      this.livenessSource = '个人信息-修改邮箱';
      this.showLivenessDialog = true;
    },
    // 拦截手机号编辑
    openPhoneEdit() {
      this.pendingAction = 'editPhone';
      this.livenessSource = '个人信息-修改手机号';
      this.showLivenessDialog = true;
    },
    // 拦截修改密码
    onEditAll() {
      this.pendingAction = 'editAll';
      this.livenessSource = '个人信息-修改密码';
      this.showLivenessDialog = true;
    },
    // 活体认证通过后执行原操作
    onLivenessSuccess() {
      this.showLivenessDialog = false;
      if (this.pendingAction === 'editEmail') {
        this.showEditEmail = true;
      } else if (this.pendingAction === 'editPhone') {
        this.showPhoneEdit = true;
      } else if (this.pendingAction === 'editAll') {
        this.showEditAll = true;
      }
      this.pendingAction = null;
    }
  }
}
</script>

<style scoped>
.profile-bg-light {
  min-height: 100vh;
  background: #f4f4f4;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 48px;
}
.profile-card-light {
  background: linear-gradient(135deg, #fff 80%, #f6faff 100%);
  border-radius: 28px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.10);
  padding: 0 0 36px 0;
  width: 420px;
  margin-top: 0;
  position: relative;
}
.profile-header-light {
  background: linear-gradient(90deg, #ffb86c 60%, #ffe0b2 100%);
  border-radius: 28px 28px 0 0;
  height: 90px;
  position: relative;
}
.profile-banner-light {
  position: absolute;
  left: 0; top: 0; right: 0; height: 120px;
  background: #f7b267;
  z-index: 0;
}
.profile-avatar-block {
  position: absolute;
  left: 50%;
  top: 60px;
  transform: translateX(-50%);
  z-index: 2;
}
.avatar-light {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  border: 5px solid #fff;
  box-shadow: 0 4px 16px rgba(0,0,0,0.10);
  background: #fff;
  object-fit: cover;
}
.profile-nick-block-row {
  margin-left: 24px;
  margin-bottom: 18px;
  z-index: 1;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: flex-start;
  height: 88px;
  margin-top: 44px; /* 向下移，与头像垂直居中 */
}
.nickname-light {
  font-size: 1.5em;
  font-weight: bold;
  color: #333;
  margin-bottom: 0;
  margin-right: 18px;
  line-height: 88px;
  display: flex;
  align-items: center;
}
.edit-btn-light {
  background: linear-gradient(90deg,#7ed6ff,#b2f0ff);
  color: #007aff;
  border: none;
  border-radius: 10px;
  padding: 4px 18px;
  font-size: 1rem;
  font-weight: 500;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
  margin-left: 8px;
}
.edit-btn-light:hover {
  background: linear-gradient(90deg,#4fc3f7,#81ecec);
  color: #0051a8;
}
.edit-btn-light.fixed-btn {
  background: #f5f6fa;
  color: #bbb;
  cursor: not-allowed;
  box-shadow: none;
}
.profile-info-card-light {
  margin-top: 60px;
  padding: 32px 32px 0 32px;
  background: rgba(255,255,255,0.98);
  border-radius: 20px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}
.profile-title {
  font-size: 2rem;
  font-weight: 700;
  color: #222;
  margin-bottom: 28px;
  text-align: center;
  letter-spacing: 1px;
}
.info-row-light {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 0 12px 0;
  font-size: 1.08rem;
  border-bottom: 1px solid #f0f0f0;
}
.info-row-light.no-border {
  border-bottom: none;
}
.info-label-light {
  color: #888;
  min-width: 80px;
  font-weight: 500;
}
.permission-row-fix .permission-value {
  color: #007aff;
  font-weight: 600;
}
.modify-btn {
  margin-left: 0;
  margin-top: 0;
  align-self: center;
  height: 40px;
  display: flex;
  align-items: center;
}
.modal-mask-light {
  position: fixed;
  z-index: 9999;
  left: 0; top: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.12);
  display: flex;
  align-items: center;
  justify-content: center;
}
.modal-content-light {
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
.form-row-modal-light {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  margin-bottom: 18px;
  gap: 10px;
}
input[type="email"], input[type="password"], input[type="text"] {
  border: 1.5px solid #e0e0e0;
  border-radius: 8px;
  padding: 6px 12px;
  font-size: 1rem;
  outline: none;
  transition: border 0.2s;
  width: 60%;
}
input[type="email"]:focus, input[type="password"]:focus, input[type="text"]:focus {
  border: 1.5px solid #007aff;
}
.btn-light {
  background: #f5f6fa;
  color: #007aff;
  border: none;
  border-radius: 8px;
  padding: 6px 18px;
  font-size: 1rem;
  font-weight: 500;
  margin-left: 8px;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}
.btn-light.cancel {
  background: #f8d7da;
  color: #c0392b;
}
.btn-light:hover {
  background: #eaf3ff;
  color: #0051a8;
}
.lower-nick-block {
  margin-top: 38px; /* 让用户名和按钮整体下移，贴近header底部 */
}
.info-row-password-btn {
  justify-content: flex-start;
  border-bottom: none;
  margin-top: 10px;
}
.left-btn {
  width: 100%;
  margin: 0;
  padding: 10px 0;
  font-size: 1.1rem;
  background: linear-gradient(90deg,#007aff,#7ed6ff);
  color: #fff;
  font-weight: 600;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  transition: background 0.2s;
}
.left-btn:hover {
  background: linear-gradient(90deg,#0051a8,#4fc3f7);
}
.no-border {
  border-bottom: none !important;
}
.info-value-center {
  color: #222;
  font-weight: 600;
  margin: 0 8px;
}
</style> 