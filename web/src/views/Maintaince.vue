<template>
  <div class="container">
    <h2>病害任务分配给维修工</h2>

    <table>
      <thead>
        <tr>
          <th>道路编号</th>
          <th>病害类型</th>
          <th>严重程度</th>
          <th>图片</th>
          <th>维修工</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="task in tasks" :key="task.id">
          <td>{{ task.road_id }}</td>
          <td>{{ task.disease_type }}</td>
          <td>{{ task.severity }}</td>
          <td><a :href="task.url" target="_blank">查看</a></td>

          <td>
            <select v-model="task.assigned_person_id">
              <option value="">请选择维修工</option>
              <option v-for="user in repairUsers" :key="user.id" :value="user.id">
                {{ user.username }}
              </option>
            </select>
          </td>

          <td>
            <button @click="assignTask(task)" :disabled="assignLoading[task.id]">
              {{ assignLoading[task.id] ? '分配中...' : '分配' }}
            </button>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-if="successMsg" class="message success">{{ successMsg }}</div>
    <div v-if="errorMsg" class="message error">{{ errorMsg }}</div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'

const tasks = ref([])
const repairUsers = ref([])
const assignLoading = reactive({})

const successMsg = ref('')
const errorMsg = ref('')

// 加载病害任务
async function loadTasks() {
  try {
    const res = await axios.get('http://localhost:8000/history/list')
    // 只添加 assigned_person_id 字段用于选择维修工
    tasks.value = res.data.map(item => ({
      ...item,
      assigned_person_id: ''
    }))
  } catch (error) {
    errorMsg.value = '加载病害任务失败'
  }
}

// 加载维修工用户
async function loadRepairUsers() {
  try {
    const res = await axios.get('http://localhost:8000/api/user_list', {
      params: { username: localStorage.getItem('name') },
      withCredentials: true
    })
    repairUsers.value = res.data.users.filter(user => user.permission === 1)
  } catch (error) {
    errorMsg.value = '加载维修工用户失败'
  }
}

// 分配任务
async function assignTask(task) {
  successMsg.value = ''
  errorMsg.value = ''

  if (!task.assigned_person_id) {
    errorMsg.value = '请选择维修工'
    return
  }

  assignLoading[task.id] = true
  try {
    // 根据后端接口调整请求体
    await axios.post(`/api/tasks/${task.id}/assign/`, {
      assigned_person_id: task.assigned_person_id
    }, { withCredentials: true })

    successMsg.value = `任务 ${task.id} 分配成功`
  } catch (error) {
    errorMsg.value = `任务 ${task.id} 分配失败`
  } finally {
    assignLoading[task.id] = false
  }
}

onMounted(() => {
  loadTasks()
  loadRepairUsers()
})
</script>

<style scoped>
.container {
  max-width: 1200px;
  margin: 30px auto;
  padding: 20px;
  background: #fefefe;
  border-radius: 10px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

h2 {
  text-align: center;
  margin-bottom: 20px;
}

table {
  width: 100%;
  border-collapse: collapse;
  background: white;
}

th, td {
  border: 1px solid #ddd;
  padding: 10px;
  text-align: center;
}

th {
  background-color: #f0f0f0;
}

select {
  padding: 6px;
  border-radius: 4px;
  border: 1px solid #ccc;
  width: 160px;
}

button {
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  background-color: #007bff;
  color: white;
  cursor: pointer;
  font-size: 14px;
}

button:disabled {
  background-color: #999;
  cursor: not-allowed;
}

.message {
  margin-top: 20px;
  font-weight: 600;
  text-align: center;
}

.success {
  color: green;
}

.error {
  color: red;
}
</style>
