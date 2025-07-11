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
        <div class="info-row-light"><span class="info-label-light">用户名</span><span class="info-value-center">{{ user.username }}</span><button class="edit-btn-light fixed-btn" disabled>固定</button></div>
        <div class="info-row-light"><span class="info-label-light">电子邮箱</span><span class="info-value-center">{{ user.email }}</span><button class="edit-btn-light" @click="showEditEmail = true">编辑</button></div>
        <div class="info-row-light permission-row-fix"><span class="info-label-light">权限</span><span class="info-value-center permission-value">{{ permissionText }}</span><button class="edit-btn-light fixed-btn" disabled>固定</button></div>
        <div class="info-row-light no-border info-row-password-btn"><button class="edit-btn-light left-btn" @click="showEditAll = true">修改密码</button></div>
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
  </div>
</template>

<script>
import axios from 'axios';
export default {
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
      confirmPassword: ''
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
        this.avatarUrl = res.data.avatar_url
          ? (res.data.avatar_url.startsWith('http') ? res.data.avatar_url : (API_BASE + res.data.avatar_url))
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
          this.avatarUrl = this.user.avatar
            ? (this.user.avatar.startsWith('http') ? this.user.avatar : (API_BASE + this.user.avatar))
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
      this.avatarUrl = URL.createObjectURL(file);
      // 上传到后端
      const formData = new FormData();
      formData.append('username', this.user.username);
      formData.append('avatar', file);
      axios.post((process.env.VUE_APP_API_BASE || 'http://localhost:8000') + '/api/upload_avatar/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      }).then(res => {
        alert(res.data.msg);
        if (res.data.avatar_url) {
          // 自动拼接API_BASE，适配本地和生产
          const API_BASE = process.env.VUE_APP_API_BASE || '';
          this.avatarUrl = res.data.avatar_url.startsWith('http') ? res.data.avatar_url : (API_BASE + res.data.avatar_url);
          // 更新localStorage中的头像字段，保证刷新/登录后头像不丢失
          let user = localStorage.getItem('user') ? JSON.parse(localStorage.getItem('user')) : {};
          user.avatar = res.data.avatar_url;
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
    }
  }
}
</script>

<style scoped>
.profile-bg-light {
  min-height: 100vh;
  background: linear-gradient(120deg, #e0eafc 0%, #cfdef3 100%);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 40px;
}
.profile-card-light {
  background: rgba(255,255,255,0.82);
  border-radius: 18px;
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.10);
  width: 480px;
  margin-bottom: 40px;
  overflow: hidden;
}
.profile-header-light {
  position: relative;
  background: #f7b267;
  height: 120px;
  display: flex;
  align-items: flex-end;
  padding: 0 0 0 32px;
}
.profile-banner-light {
  position: absolute;
  left: 0; top: 0; right: 0; height: 120px;
  background: #f7b267;
  z-index: 0;
}
.profile-avatar-block {
  position: relative;
  z-index: 1;
  margin-bottom: -44px;
}
.avatar-light {
  width: 88px;
  height: 88px;
  border-radius: 50%;
  border: 5px solid #fff;
  background: #f4f4f4;
  object-fit: cover;
  box-shadow: 0 2px 8px rgba(0,0,0,0.10);
  cursor: pointer;
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
  background: #1890ff;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 5px 18px;
  font-size: 1em;
  margin-left: 12px;
  cursor: pointer;
  transition: background 0.2s;
}
.edit-btn-light:hover {
  background: #40a9ff;
}
.profile-info-card-light {
  background: rgba(255,255,255,0.92);
  border-radius: 12px;
  margin: 32px 24px 24px 24px;
  padding: 24px 18px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
.info-row-light {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 0;
  border-bottom: 1px solid #e0eafc;
}
.info-row-light:last-child {
  border-bottom: none;
}
.info-label-light {
  color: #888;
  width: 90px;
  font-size: 1em;
}
.permission-row-fix {
  display: flex;
  align-items: center;
}
.permission-value {
  font-size: 1em;
  font-weight: 500;
  color: #333;
  margin-left: 0;
  margin-right: 12px;
}
.fixed-btn {
  opacity: 1;
  background: #1890ff;
  color: #fff;
  cursor: not-allowed;
  height: 36px;
  padding: 5px 18px;
  border-radius: 8px;
  font-size: 1em;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
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
  left: 0; top: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.18);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
}
.modal-content-light {
  background: #fff;
  border-radius: 12px;
  padding: 32px 28px 24px 28px;
  min-width: 340px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.10);
}
.form-row-modal-light {
  display: flex;
  align-items: center;
  margin-bottom: 18px;
}
.form-row-modal-light label {
  color: #888;
  width: 80px;
}
input[type="text"], input[type="password"], input[type="email"] {
  padding: 7px 12px;
  border: 1.5px solid #e0eafc;
  border-radius: 7px;
  width: 180px;
  font-size: 1em;
  margin-right: 10px;
  background: #f8fafc;
  color: #333;
  transition: border 0.2s;
}
input[type="text"]:focus, input[type="password"]:focus, input[type="email"]:focus {
  border: 1.5px solid #1890ff;
  outline: none;
}
.btn-light {
  background: #1890ff;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 6px 18px;
  font-size: 1em;
  cursor: pointer;
  margin-left: 8px;
  transition: background 0.2s;
}
.btn-light:hover {
  background: #40a9ff;
}
.btn-light.cancel {
  background: #bbb;
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
  margin-left: 0;
  margin-right: auto;
  display: block;
}
.info-value-center {
  flex: 1;
  text-align: center;
  font-size: 1.1em;
  color: #222;
}
</style> 