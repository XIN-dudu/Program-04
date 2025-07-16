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
            <div class="custom-multiselect" @click="toggleDropdown(task)" :tabindex="0" @blur="closeDropdown(task)">
              <div class="selected-tags">
                <span v-for="id in task.assigned_person_ids" :key="id" class="tag">
                  {{ getUsernameById(id) }}
                  <span class="remove-tag" @click.stop="removeWorker(task, id)">&times;</span>
                </span>
                <span v-if="!task.assigned_person_ids.length" class="placeholder">请选择维修工</span>
              </div>
              <div class="dropdown" v-show="task.dropdownOpen">
                <div v-for="user in repairUsers" :key="user.id" class="dropdown-item" @click.stop="toggleWorker(task, user.id)">
                  <input type="checkbox" :checked="task.assigned_person_ids.includes(user.id)" />
                  <span>{{ user.username }}</span>
                </div>
                <div class="dropdown-actions">
                  <button type="button" @click.stop="clearAll(task)">清除</button>
                  <button type="button" @click.stop="closeDropdown(task)">关闭</button>
                </div>
              </div>
            </div>
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
    // 多选分配，assigned_person_ids为数组
    tasks.value = res.data.map(item => ({
      ...item,
      assigned_person_ids: [],
      dropdownOpen: false // 新增属性，控制下拉框的显示
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
  if (!task.assigned_person_ids || task.assigned_person_ids.length === 0) {
    errorMsg.value = '请选择至少一位维修工'
    return
  }
  assignLoading[task.id] = true
  try {
    await axios.post(`/api/tasks/${task.id}/assign/`, {
      assigned_person_ids: task.assigned_person_ids
    }, { withCredentials: true })
    successMsg.value = `任务 ${task.id} 分配成功`
  } catch (error) {
    errorMsg.value = `任务 ${task.id} 分配失败`
  } finally {
    assignLoading[task.id] = false
  }
}

function getUsernameById(id) {
  const user = repairUsers.value.find(u => u.id === id)
  return user ? user.username : id
}
function toggleDropdown(task) {
  tasks.value.forEach(t => t.dropdownOpen = false)
  task.dropdownOpen = !task.dropdownOpen
}
function closeDropdown(task) {
  setTimeout(() => { task.dropdownOpen = false }, 100)
}
function toggleWorker(task, id) {
  const idx = task.assigned_person_ids.indexOf(id)
  if (idx === -1) {
    task.assigned_person_ids.push(id)
  } else {
    task.assigned_person_ids.splice(idx, 1)
  }
}
function removeWorker(task, id) {
  const idx = task.assigned_person_ids.indexOf(id)
  if (idx !== -1) {
    task.assigned_person_ids.splice(idx, 1)
  }
}
function clearAll(task) {
  task.assigned_person_ids = []
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

.custom-multiselect {
  position: relative;
  min-width: 180px;
  border: 1.5px solid #ccc;
  border-radius: 6px;
  background: #fff;
  padding: 4px 8px;
  cursor: pointer;
  user-select: none;
}
.selected-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  min-height: 28px;
  align-items: center;
}
.tag {
  background: #e6f0ff;
  color: #007bff;
  border-radius: 12px;
  padding: 2px 10px 2px 8px;
  font-size: 13px;
  display: flex;
  align-items: center;
  margin-right: 2px;
}
.remove-tag {
  margin-left: 4px;
  color: #888;
  cursor: pointer;
  font-size: 15px;
}
.placeholder {
  color: #bbb;
  font-size: 13px;
}
.dropdown {
  position: absolute;
  left: 0;
  top: 100%;
  z-index: 10;
  background: #fff;
  border: 1.5px solid #007bff;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  min-width: 180px;
  margin-top: 2px;
  padding: 6px 0 0 0;
}
.dropdown-item {
  padding: 4px 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
}
.dropdown-item:hover {
  background: #f0f8ff;
}
.dropdown-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 6px 12px 6px 0;
}
.dropdown-actions button {
  background: #eee;
  border: none;
  border-radius: 6px;
  padding: 2px 10px;
  font-size: 13px;
  cursor: pointer;
}
.dropdown-actions button:hover {
  background: #e6f0ff;
}
</style>
