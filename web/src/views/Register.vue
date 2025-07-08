<!-- 注册 -->
<template>
  <div class="register-container">
    <h1>注册账号</h1>
    <form @submit.prevent="onSubmit">
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
      errorMsg: '',
      successMsg: ''
    };
  },
  methods: {
    async onSubmit() {
      if (this.form.password !== this.form.confirmPassword) {
        this.errorMsg = '两次输入的密码不一致！';
        this.successMsg = '';
        alert(this.errorMsg);
        return;
      }
      this.errorMsg = '';
      this.successMsg = '';
      this.router = useRouter();
      try {
        const res = await axios.post('http://localhost:8000/register', {
          username: this.form.username,
          password: this.form.password,
          email: this.form.email,
          phone: this.form.phone
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
</style>