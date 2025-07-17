<template>
  <div class="maintain-bg">
    <div class="maintain-container">
      <h2 class="maintain-title">维修任务分配</h2>
      <table class="maintain-table">
        <thead>
          <tr>
            <th>道路编号</th>
            <th>病害类型</th>
            <th>严重程度</th>
            <th>图片</th>
            <th>维修工</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="task in tasks" :key="task.disease_id">
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
              {{ getTaskStatus(task) }}
            </td>
            <td>
              <button
                v-if="getTaskStatus(task) === '已完成'"
                class="assign-btn"
                @click="showCompletionImages(task)"
              >查看</button>
              <button
                v-else
                class="assign-btn"
                @click="assignTask(task)"
                :disabled="assignLoading[task.disease_id]"
              >{{ assignLoading[task.disease_id] ? '分配中...' : '分配' }}</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="successMsg" class="message success">{{ successMsg }}</div>
      <div v-if="errorMsg" class="message error">{{ errorMsg }}</div>
    </div>
    <!-- 新增：查看弹窗 -->
    <div v-if="viewDialog" class="view-dialog-mask" @click.self="viewDialog = false">
      <div class="view-dialog-box">
        <div class="view-dialog-title">维修工上传图片 <span class="view-dialog-close" @click="viewDialog = false">×</span></div>
        <div v-if="viewImages.length === 0" style="padding: 24px 0; text-align: center; color: #888;">暂无上传图片</div>
        <div v-for="item in viewImages" :key="item.username" class="view-img-item">
          <div class="view-img-username">{{ item.username }}</div>
          <img :src="item.image" alt="认证图片" class="view-img-pic" />
        </div>
      </div>
    </div>
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

// 新增：查看弹窗相关
const viewDialog = ref(false)
const viewImages = ref([]) // [{username, image}]

// 加载病害任务
async function loadTasks() {
  try {
    // 不加 unfinished_only 参数，显示所有任务
    const res = await axios.get('http://localhost:8000/history/list')
    // 多选分配，assigned_person_ids为数组
    tasks.value = res.data.map(item => ({
      ...item,
      assigned_person_ids: item.assigned_person_ids || [],
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
  if (assignLoading[task.disease_id]) return // 防止重复点击
  assignLoading[task.disease_id] = true
  try {
    await axios.post(`/api/tasks/${task.disease_id}/assign/`, {
      assigned_person_ids: task.assigned_person_ids
    }, { withCredentials: true })
    successMsg.value = `任务 ${task.disease_id} 分配成功`
    await loadTasks() // 分配成功后刷新
  } catch (error) {
    errorMsg.value = `任务 ${task.disease_id} 分配失败`
  } finally {
    assignLoading[task.disease_id] = false
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

// 新增：查看图片方法
function showCompletionImages(task) {
  if (!task.assignments) {
    viewImages.value = []
  } else {
    viewImages.value = task.assignments
      .filter(a => a.completion_image)
      .map(a => ({
        username: a.worker_username || getUsernameById(a.worker_id),
        image: a.completion_image.startsWith('http') ? a.completion_image : `http://localhost:8000${a.completion_image}`
      }))
  }
  viewDialog.value = true
}

function getTaskStatus(task) {
  console.log('Task data:', task); // 调试信息
  
  // 优先用后端 assignment_status 字段（针对当前用户或管理员）
  if (task.assignment_status === 'finished') return '已完成';
  // 检查 assignments 数组中的状态
  if (task.assignments && task.assignments.length > 0) {
    // 检查是否所有维修工都完成了
    const allFinished = task.assignments.every(a => a.status === 'finished');
    if (allFinished) return '已完成';
  }
  
  // 没有分配维修工
  if (!task.assigned_person_ids || task.assigned_person_ids.length === 0) return '未分配';
  // 没有 assignments 字段，无法判断完成情况，默认已分配
  if (!task.assignments || !task.assignments.length) return '已分配';
  // 只要有一个不是finished就已分配
  if (task.assignments.some(a => a.status !== 'finished')) return '已分配';
  // 全部 finished
  return '已完成';
}

onMounted(() => {
  loadTasks()
  loadRepairUsers()
})
</script>

<style scoped>
.maintain-bg {
  min-height: 100vh;
  background: #f7f8fa;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 40px;
}
.maintain-container {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  padding: 28px 28px 18px 28px;
  min-width: 900px;
  max-width: 1200px;
  margin: 0 auto;
}
.maintain-title {
  text-align: left;
  font-size: 22px;
  color: #222;
  font-weight: 600;
  margin-bottom: 18px;
  letter-spacing: 1px;
}
.maintain-table {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
  border-radius: 6px;
  box-shadow: none;
}
.maintain-table th, .maintain-table td {
  padding: 10px 8px;
  text-align: center;
  border-bottom: 1px solid #ececec;
  font-size: 15px;
  overflow: visible; /* 允许内容溢出 */
}
.maintain-table th {
  background: #f5f7fa;
  color: #3a5a8c;
  font-weight: 600;
  letter-spacing: 0.5px;
}
.maintain-table tr:last-child td {
  border-bottom: none;
}
.maintain-table th:nth-child(5), .maintain-table td:nth-child(5) {
  width: 260px;
  min-width: 220px;
  max-width: 320px;
}
.assign-btn {
  background: #fff;
  color: #2476e8;
  border: 1px solid #2476e8;
  border-radius: 4px;
  padding: 5px 14px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
  box-shadow: none;
}
.assign-btn:hover {
  background: #2476e8;
  color: #fff;
}
/* 新增：美化查看图片链接 */
td a {
  color: #2476e8;
  text-decoration: none;
  font-weight: 500;
  transition: text-decoration 0.2s;
}
td a:hover {
  text-decoration: underline;
  color: #0056b3;
}
/* 保持原有多选下拉样式不变 */
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
  width: max-content;
  max-width: 300px;
  max-height: 260px;
  overflow-y: auto;
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

.view-dialog-mask {
  position: fixed;
  left: 0; top: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.18);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
}
.view-dialog-box {
  background: #fff;
  border-radius: 10px;
  min-width: 320px;
  max-width: 90vw;
  max-height: 80vh;
  padding: 24px 32px 18px 32px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.13);
  overflow-y: auto;
  position: relative;
}
.view-dialog-title {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 18px;
  color: #222;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.view-dialog-close {
  font-size: 22px;
  color: #888;
  cursor: pointer;
  margin-left: 16px;
}
.view-img-item {
  margin-bottom: 18px;
}
.view-img-username {
  font-weight: bold;
  margin-bottom: 6px;
  color: #2476e8;
}
.view-img-pic {
  max-width: 320px;
  max-height: 220px;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  background: #f7f7f7;
}
</style>
