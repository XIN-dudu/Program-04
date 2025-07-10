<!-- 城市交通可视化 -->
<template>
  <div class="urban-traffic-home">
    <template v-if="$route.path === '/urbanTraffic'">
      <div class="header">城市交通大数据服务平台</div>
      <div class="feature-list">
        <div class="feature-card" @click="goTo('trajectory')">
          <h3>车辆轨迹可视化</h3>
          <p>可视化展示车辆的历史轨迹数据</p>
        </div>
        <div class="feature-card" @click="goTo('hotspot')">
          <h3>上客热点区域</h3>
          <p>分析并展示上客热点区域分布</p>
        </div>
        <div class="feature-card" @click="goTo('weekflow')">
          <h3>周客流量分布</h3>
          <p>展示一周内的客流量变化趋势</p>
        </div>
        <div class="feature-card" @click="goTo('road')">
          <h3>路程与道路数据可视化</h3>
          <p>分析路程类型与道路速度等数据</p>
        </div>
      </div>
    </template>
    <router-view v-else />
  </div>
</template>

<script>
export default {
  name: "UrbanTrafficHome",
  methods: {
    goTo(feature) {
      this.$router.push(`/urbanTraffic/${feature}`);
    }
  }
};
</script>

<style scoped>
.urban-traffic-home {
  padding: 32px;
}
.header {
  color: #0288d1;
  font-size: 32px;
  font-weight: bold;
  text-align: center;
  margin-bottom: 32px;
  letter-spacing: 2px;
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
  transition: box-shadow 0.2s, background 0.2s;
  border: 1.5px solid #b3e5fc;
}
.feature-card:hover {
  background: #e0f7fa;
  box-shadow: 0 6px 24px rgba(2,136,209,0.16);
  border-color: #0288d1;
}
.feature-card h3 {
  margin: 0 0 8px 0;
  color: #0288d1;
  font-size: 22px;
}
.feature-card p {
  margin: 0;
  color: #555;
  font-size: 15px;
}
</style>