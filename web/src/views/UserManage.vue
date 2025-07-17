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
              <select v-model="user.permission" @change="updatePermission(user)" class="perm-select">
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
    <LivenessDetection
      v-if="showLivenessDialog"
      :dialog-mode="true"
      @success="handleLivenessSuccess"
      @close="handleLivenessClose"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import LivenessDetection from './LivenessDetection.vue'

const users = ref([])
const showLivenessDialog = ref(false)
const pendingAction = ref(null)

const fetchUsers = async () => {
  const res = await axios.get('/api/user_list/', {
    params: { username: localStorage.getItem('name') },
    withCredentials: true
  })
  users.value = res.data.users
}

const actuallyUpdatePermission = async (user) => {
  await axios.post('/api/update_permission/', {
    username: localStorage.getItem('name'),
    user_id: user.id,
    permission: user.permission
  }, { withCredentials: true })
  fetchUsers()
}

const actuallyDeleteUser = async (user) => {
  if (!confirm(`确定要删除用户 ${user.username} 吗？此操作不可恢复！`)) return
  await axios.post('/api/delete_user/', {
    username: localStorage.getItem('name'),
    user_id: user.id
  }, { withCredentials: true })
  fetchUsers()
}

const updatePermission = (user) => {
  pendingAction.value = () => actuallyUpdatePermission(user)
  showLivenessDialog.value = true
}

const deleteUser = (user) => {
  pendingAction.value = () => actuallyDeleteUser(user)
  showLivenessDialog.value = true
}

function handleLivenessSuccess() {
  showLivenessDialog.value = false
  if (pendingAction.value) pendingAction.value()
  pendingAction.value = null
}
function handleLivenessClose() {
  showLivenessDialog.value = false
  pendingAction.value = null
}

onMounted(fetchUsers)
</script>

<style scoped>
.user-manage-bg {
  min-height: 100vh;
  background: #f7f8fa;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 40px;
}
.user-manage-container {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  padding: 28px 28px 18px 28px;
  min-width: 900px;
  max-width: 1200px;
  margin: 0 auto;
}
.user-manage-title {
  text-align: left;
  font-size: 22px;
  color: #222;
  font-weight: 600;
  margin-bottom: 18px;
  letter-spacing: 1px;
}
.user-table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: none;
}
.user-table th, .user-table td {
  padding: 10px 8px;
  text-align: center;
  border-bottom: 1px solid #ececec;
  font-size: 15px;
}
.user-table th {
  background: #f5f7fa;
  color: #3a5a8c;
  font-weight: 600;
  letter-spacing: 0.5px;
}
.user-table tr:last-child td {
  border-bottom: none;
}
.perm-select {
  padding: 4px 10px;
  border-radius: 4px;
  border: 1px solid #d0d7e2;
  background: #fff;
  font-size: 14px;
  outline: none;
  transition: border 0.2s;
}
.perm-select:focus {
  border: 1.5px solid #3a5a8c;
}
.delete-btn {
  background: #fff;
  color: #e74c3c;
  border: 1px solid #e74c3c;
  border-radius: 4px;
  padding: 5px 14px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
  box-shadow: none;
}
.delete-btn:hover {
  background: #e74c3c;
  color: #fff;
}
</style> 