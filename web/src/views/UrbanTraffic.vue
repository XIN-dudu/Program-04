<!-- 城市交通可视化 -->
<template>
  <div class="urban-traffic-home">
    <div v-if="$route.path === '/urbanTraffic'">
      <div class="main-title">城市交通大数据服务平台</div>
      <div class="feature-list">
        <div class="feature-card" @click="goTo('trajectory')">
          <div class="feature-title">车辆轨迹可视化</div>
          <div class="feature-desc">可视化展示车辆的历史轨迹数据</div>
        </div>
        <div class="feature-card" @click="goTo('hotspot')">
          <div class="feature-title">上客热点区域</div>
          <div class="feature-desc">分析并展示上客热点区域分布</div>
        </div>
        <div class="feature-card" @click="goTo('stat')">
          <div class="feature-title">城市交通数据统计分析</div>
          <div class="feature-desc">可视化展示多维度交通统计数据</div>
        </div>

      </div>
    </div>
    <router-view v-else />
  </div>
</template>

<script>
export default {
  name: 'UrbanTraffic',
  methods: {
    goTo(type) {
      if (type === 'trajectory') {
        this.$router.push('/urbanTraffic/trajectory');
      } else if (type === 'hotspot') {
        this.$router.push('/urbanTraffic/hotspot');
      } else if (type === 'stat') {
        this.$router.push('/urbanTraffic/shandongmap');
      }
    }
  }
}
</script>

<style scoped>
.urban-traffic-home {
  padding: 32px;
}
.main-title {
  color: #0288d1;
  font-size: 32px;
  font-weight: bold;
  letter-spacing: 2px;
  margin-bottom: 32px;
  text-align: center;
}
.feature-list {
  display: flex;
  flex-wrap: wrap;
  gap: 24px;
  justify-content: center;
}
.feature-card {
  width: 260px;
  height: 140px;
  background: #f5faff;
  border-radius: 18px;
  box-shadow: 0 2px 12px rgba(2,136,209,0.08);
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  padding: 24px;
  cursor: pointer;
  transition: box-shadow 0.25s, background 0.2s;
  border: 1.5px solid #b3e5fc;
}
.feature-card:hover {
  background: #e0f7fa;
  box-shadow: 0 6px 24px rgba(2,136,209,0.16);
}
.feature-title {
  font-size: 1.18rem;
  font-weight: 600;
  color: #0288d1;
  margin-bottom: 10px;
}
.feature-desc {
  font-size: 1rem;
  color: #666;
  text-align: left;
}
</style>