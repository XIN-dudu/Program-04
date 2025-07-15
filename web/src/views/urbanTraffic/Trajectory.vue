<template>
  <div class="trajectory-flex">
    <div class="left-panel">
      <div class="card query-form">
        <h3>车辆轨迹查询</h3>
        <div class="form-row">
          <label>起始时间：</label>
          <input v-model="startTime" type="datetime-local" />
        </div>
        <div class="form-row">
          <label>终止时间：</label>
          <input v-model="endTime" type="datetime-local" />
        </div>
        <div class="form-row">
          <label>车牌标识：</label>
          <input v-model="carId" placeholder="请输入车牌号（可选）" />
        </div>
        <button @click="queryTrajectory">查询轨迹</button>
      </div>
    </div>
    <div class="right-panel">
      <div id="trajectoryMap" class="map-chart"></div>
    </div>
  </div>
</template>

<script>
export default {
  name: "Trajectory",
  data() {
    return {
      startTime: '',
      endTime: '',
      carId: '',
      map: null,
      polyline: null,
      arrowMarkers: [] // 新增：用于存储箭头marker
    };
  },
  mounted() {
    this.initMap();
  },
  methods: {
    initMap() {
      if (!window.BMap) {
        console.error('BMap is not loaded!');
        return;
      }
      this.map = new window.BMap.Map("trajectoryMap");
      const point = new window.BMap.Point(117.0009, 36.6758);
      this.map.centerAndZoom(point, 12);
      this.map.enableScrollWheelZoom(true);
    },
    formatTime(dt) {
      if (!dt) return '';
      const d = new Date(dt);
      return `${d.getFullYear()}/${d.getMonth()+1}/${d.getDate()} ${d.getHours()}:${d.getMinutes()}`;
    },
    async queryTrajectory() {
      if (!this.map) return;
      if (this.polyline) {
        this.map.removeOverlay(this.polyline);
        this.polyline = null;
      }
      // 清除旧的箭头
      if (this.arrowMarkers && this.arrowMarkers.length > 0) {
        this.arrowMarkers.forEach(m => this.map.removeOverlay(m));
        this.arrowMarkers = [];
      }
      let params = [];
      if (this.startTime) params.push(`start=${encodeURIComponent(this.formatTime(this.startTime))}`);
      if (this.endTime) params.push(`end=${encodeURIComponent(this.formatTime(this.endTime))}`);
      if (this.carId) params.push(`car=${encodeURIComponent(this.carId)}`);
      params.push('limit=200');
      const url = `/api/points/?${params.join('&')}`;
      try {
        const res = await fetch(url);
        const data = await res.json();
        const points = data.filter(item => item.lat && item.lon).map(item => ({
          point: new window.BMap.Point(item.lon, item.lat),
          head: item.head // 方向角度
        }));
        if (points.length > 0) {
          // 轨迹线为绿色
          this.polyline = new window.BMap.Polyline(points.map(p => p.point), {
            strokeColor: "#43a047", // 好看的绿色
            strokeWeight: 7,
            strokeOpacity: 0.85
          });
          this.map.addOverlay(this.polyline);
          this.map.setViewport(points.map(p => p.point));

          // 沿轨迹每隔一定距离密集分布小箭头marker，方向与轨迹一致
          const arrowStep = 5; // 每隔5个点画一个箭头
          for (let i = 0; i < points.length - 1; i += arrowStep) {
            const p = points[i];
            const next = points[i + 1] || points[i];
            // 计算方向角
            const dx = next.point.lng - p.point.lng;
            const dy = next.point.lat - p.point.lat;
            const angle = Math.atan2(dy, dx) * 180 / Math.PI;
            // 画自定义小箭头
            const arrow = new window.BMap.Marker(
              p.point,
              {
                icon: new window.BMap.Symbol("M0,0 L10,0 L5,10 Z", {
                  scale: 1.2,
                  strokeColor: "#fff",
                  strokeWeight: 2,
                  rotation: angle,
                  fillColor: "#fff",
                  fillOpacity: 1
                })
              }
            );
            this.map.addOverlay(arrow);
            this.arrowMarkers.push(arrow);
          }
        }
      } catch (e) {
        console.error('轨迹查询失败', e);
      }
    }
  }
};
</script>

<style scoped>
.trajectory-flex {
  display: flex;
  flex-direction: row;
  align-items: flex-start;
  padding: 32px;
  gap: 48px;
  height: 90vh;
  box-sizing: border-box;
}
.left-panel {
  width: 260px;
  flex-shrink: 0;
}
.right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  height: 100%;
}
.card.query-form {
  background: #f5faff;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  padding: 18px 14px;
  color: #333;
  width: 100%;
}
.card h3 {
  color: #0288d1;
  margin-bottom: 10px;
}
.form-row {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}
.form-row label {
  width: 80px;
  color: #0288d1;
}
.card input {
  flex: 1;
  padding: 6px 8px;
  border-radius: 4px;
  border: 1px solid #b3e5fc;
  background: #fff;
  margin-left: 8px;
}
.card button {
  background: #0288d1;
  color: #fff;
  border: none;
  border-radius: 4px;
  padding: 6px 16px;
  margin-top: 8px;
  cursor: pointer;
}
.card button:hover {
  background: #0277bd;
}
.map-chart {
  width: 100%;
  height: 100%;
  min-height: 600px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
  background: #fff;
  border: 1px solid #ccc;
}
</style> 