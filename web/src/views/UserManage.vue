<template>
  <div class="user-manage-bg">
    <div class="user-manage-container">
      <h2 class="user-manage-title">用户管理</h2>
      <table class="user-table">
        <thead>
          <tr>
            <th>用户名</th>
            <th>邮箱</th>
            <th>权限</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in users" :key="user.id">
            <td>{{ user.username }}</td>
            <td>{{ user.email }}</td>
            <td>
              <select v-model="user.permission" @change="updatePermission(user)">
                <option value="0">普通用户</option>
                <option value="1">维修工</option>
                <option value="2">管理员</option>
              </select>
            </td>
            <td>
              <button class="delete-btn" @click="deleteUser(user)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const users = ref([])

const fetchUsers = async () => {
  const res = await axios.get('http://localhost:8000/api/user_list/', { withCredentials: true })
  users.value = res.data.users
}

const updatePermission = async (user) => {
  await axios.post('http://localhost:8000/api/update_permission/', {
    user_id: user.id,
    permission: user.permission
  }, { withCredentials: true })
  fetchUsers()
}

const deleteUser = async (user) => {
  if (!confirm(`确定要删除用户 ${user.username} 吗？此操作不可恢复！`)) return
  // 1. 删除用户及人脸记录
  await axios.post('http://localhost:8000/api/delete_user/', { user_id: user.id }, { withCredentials: true })
  fetchUsers()
}

onMounted(fetchUsers)
</script>

<style scoped>
.user-manage-bg {
  min-height: 100vh;
  background: #f4f4f4;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding-top: 60px;
}
.user-manage-container {
  background: rgba(255,255,255,0.95);
  border-radius: 18px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.10);
  padding: 32px 28px;
  min-width: 600px;
}
.user-manage-title {
  text-align: center;
  font-size: 1.6rem;
  font-weight: bold;
  margin-bottom: 24px;
}
.user-table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
}
.user-table th, .user-table td {
  border: 1px solid #e0e0e0;
  padding: 10px 8px;
  text-align: center;
}
.user-table th {
  background: #f7f7f7;
}
.delete-btn {
  background: #ff6b6b;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 6px 16px;
  cursor: pointer;
  font-size: 1rem;
  transition: background 0.2s;
}
.delete-btn:hover {
  background: #ff5252;
}
</style> 