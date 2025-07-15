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
        <div class="form-row">
          <label>limit：</label>
          <input v-model="limit" type="number" min="1" max="10000" placeholder="最大点数" />
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
      limit: 200, // 默认limit
      map: null,
      polyline: null,
      startMarker: null,
      endMarker: null,
      arrowMarkers: [], // 新增：用于存储箭头marker
      infoMarkers: [], // 新增：用于存储散点marker
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
      let params = [];
      if (this.startTime) params.push(`start=${encodeURIComponent(this.formatTime(this.startTime))}`);
      if (this.endTime) params.push(`end=${encodeURIComponent(this.formatTime(this.endTime))}`);
      if (this.carId) params.push(`car=${encodeURIComponent(this.carId)}`);
      if (this.limit) params.push(`limit=${this.limit}`);
      const url = `/api/points/?${params.join('&')}`;
      try {
        const res = await fetch(url);
        const data = await res.json();
        const points = data.filter(item => item.lat && item.lon).map(item => ({
          point: new window.BMap.Point(item.lon, item.lat),
          head: item.head,
          car: item.car,
          time: item.time,
          tflag: item.tflag,
          status: item.status,
          speed: item.SPEED !== undefined ? item.SPEED : item.speed // 兼容大小写
        }));
        // 清除旧的marker
        if (this.polyline) {
          this.map.removeOverlay(this.polyline);
          this.polyline = null;
        }
        if (this.arrowMarkers && this.arrowMarkers.length > 0) {
          this.arrowMarkers.forEach(m => this.map.removeOverlay(m));
          this.arrowMarkers = [];
        }
        if (this.infoMarkers && this.infoMarkers.length > 0) {
          this.infoMarkers.forEach(m => this.map.removeOverlay(m));
          this.infoMarkers = [];
        }
        // 判断模式
        if (this.carId && points.length > 0) {
          // 轨迹模式（原有）
          this.polyline = new window.BMap.Polyline(points.map(p => p.point), {strokeColor:"#0288d1", strokeWeight:5, strokeOpacity:0.8});
          this.map.addOverlay(this.polyline);
          this.map.setViewport(points.map(p => p.point));
          // 只在尾部画一个箭头
          if (points.length > 1) {
            const tail = points[points.length - 1];
            const arrow = new window.BMap.Marker(
              tail.point,
              {
                icon: new window.BMap.Symbol("M0,-10 L6,10 L0,5 L-6,10 Z", {
                  scale: 1.2,
                  strokeColor: "#0288d1",
                  strokeWeight: 2,
                  rotation: tail.head || 0,
                  fillColor: "#0288d1",
                  fillOpacity: 0.9
                })
              }
            );
            this.map.addOverlay(arrow);
            this.arrowMarkers.push(arrow);
          }
        } else if (!this.carId && points.length > 0) {
          // 散点模式
          this.map.setViewport(points.map(p => p.point));
          this.infoMarkers = [];
          points.forEach(p => {
            const marker = new window.BMap.Marker(p.point);
            // 信息内容
            let headText = '';
            let headRaw = '';
            if (typeof p.head === 'number') {
              const dirs = ['正北','东北','正东','东南','正南','西南','正西','西北','正北'];
              const idx = Math.round(((p.head % 360) / 45));
              const baseDir = dirs[idx];
              let offset = Math.round((p.head % 45));
              if (offset < 0) offset += 45;
              headText = `${baseDir}`;
              if (offset > 0) headText += `偏${offset}度`;
              headRaw = `${p.head}度`;
            }
            // 时间格式化
            let timeStr = p.time;
            if (typeof timeStr === 'string') {
              timeStr = timeStr.replace('T', ' ');
            }
            // 速度（SPEED字段，cm/s转m/s，始终显示）
            let speedStr = '';
            if (p.speed !== undefined && p.speed !== null && !isNaN(Number(p.speed))) {
              const v = Number(p.speed) / 100;
              speedStr = v.toFixed(2) + ' m/s';
            } else {
              speedStr = '0.00 m/s';
            }
            // 状态（status字段）
            let stateStr = '';
            if (p.status === 1 || p.status === '1') {
              stateStr = '载客';
            } else if (p.status === 0 || p.status === '0') {
              stateStr = '空载';
            } else {
              stateStr = p.status || '';
            }
            const info = `<div style='min-width:180px;font-size:13px;line-height:1.6;'>
              <b>车牌号：</b>${p.car}<br/>
              <b>时间：</b>${timeStr}<br/>
              <b>经度：</b>${p.point.lng.toFixed(6)}<br/>
              <b>纬度：</b>${p.point.lat.toFixed(6)}<br/>
              <b>方向：</b>${headText}${headRaw ? '（' + headRaw + '）' : ''}<br/>
              <b>速度：</b>${speedStr}<br/>
              <b>状态：</b>${stateStr}
            </div>`;
            marker.addEventListener('mouseover', function() {
              const infoWin = new window.BMap.InfoWindow(info, {offset: new window.BMap.Size(0, -10)});
              marker.openInfoWindow(infoWin);
            });
            marker.addEventListener('mouseout', function() {
              marker.closeInfoWindow();
            });
            this.map.addOverlay(marker);
            this.infoMarkers.push(marker);
          });
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