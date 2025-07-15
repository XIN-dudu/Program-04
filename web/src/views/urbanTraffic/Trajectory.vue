<template>
  <div class="trajectory-flex">
    <div class="left-panel">
      <div class="card query-form">
        <h3>按时间查询 <span>⏰</span></h3>
        <div class="form-row">
          <label>起始时间：</label>
          <input v-model="timeStart" type="datetime-local" />
        </div>
        <div class="form-row">
          <label>终止时间：</label>
          <input v-model="timeEnd" type="datetime-local" />
        </div>
        <div class="form-row">
          <label>最大点数：</label>
          <input v-model="timeLimit" type="number" min="1" max="10000" placeholder="请输入最大点数" />
        </div>
        <button @click="queryByTime" class="long-btn">查询</button>
      </div>
      <div class="card query-form" style="margin-top: 24px;">
        <h3>按车辆查询 <span>🚗</span></h3>
        <div class="form-row">
          <label>起始时间：</label>
          <input v-model="carStart" type="datetime-local" />
        </div>
        <div class="form-row">
          <label>终止时间：</label>
          <input v-model="carEnd" type="datetime-local" />
        </div>
        <div class="form-row">
          <label>车牌标识：</label>
          <input v-model="carId" placeholder="请输入车牌号" />
        </div>
        <div style="position:relative;">
          <button
            @click="queryByCar"
            class="long-btn"
            :disabled="!carId"
            @mouseenter="showCarIdTip = !carId"
            @mouseleave="showCarIdTip = false"
            ref="carBtn"
          >查询</button>
          <div v-if="showCarIdTip" class="btn-tooltip">请输入车牌号</div>
        </div>
      </div>
    </div>
    <div class="right-panel">
      <div id="trajectoryMap" class="map-chart"></div>
    </div>
  </div>
</template>

<script>
// 若未引入Element UI，可用window.alert替代
let showMsg = (msg) => { window.alert(msg); };
try {
  // 尝试Element UI
  if (window.ELEMENT && window.ELEMENT.Message) {
    showMsg = (msg) => window.ELEMENT.Message({ message: msg, type: 'warning' });
  }
} catch(e) {}

export default {
  name: "Trajectory",
  data() {
    return {
      // 按时间查询
      timeStart: '',
      timeEnd: '',
      timeLimit: 200,
      // 按车辆查询
      carStart: '',
      carEnd: '',
      carId: '',
      // 地图相关
      map: null,
      polyline: null,
      startMarker: null,
      endMarker: null,
      arrowMarkers: [],
      infoMarkers: [],
      showCarIdTip: false,
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
    async queryByTime() {
      if (!this.map) return;
      let params = [];
      if (this.timeStart) params.push(`start=${encodeURIComponent(this.formatTime(this.timeStart))}`);
      if (this.timeEnd) params.push(`end=${encodeURIComponent(this.formatTime(this.timeEnd))}`);
      if (this.timeLimit) params.push(`limit=${this.timeLimit}`);
      const url = `/api/points/?${params.join('&')}`;
      const found = await this.renderPoints(url, false);
      if (found === false) {
        showMsg('指定日期范围内没有记录！');
      }
    },
    async queryByCar() {
      if (!this.map) return;
      if (!this.carId) return;
      // 先查车牌号是否存在
      let carExist = false;
      try {
        // 假设有/api/cars/接口返回所有车牌号列表（如无请替换为实际接口）
        const res = await fetch('/api/cars/');
        const carList = await res.json();
        carExist = Array.isArray(carList) && carList.includes(this.carId);
      } catch(e) {
        // 如果接口失败，默认允许查（不拦截）
        carExist = true;
      }
      if (!carExist) {
        showMsg('找不到指定车牌号！');
        return;
      }
      let params = [];
      if (this.carStart) params.push(`start=${encodeURIComponent(this.formatTime(this.carStart))}`);
      if (this.carEnd) params.push(`end=${encodeURIComponent(this.formatTime(this.carEnd))}`);
      if (this.carId) params.push(`car=${encodeURIComponent(this.carId)}`);
      const url = `/api/points/?${params.join('&')}`;
      const found = await this.renderPoints(url, true);
      if (found === false) {
        showMsg('该车牌号在指定日期范围内没有记录！');
      }
    },
    async renderPoints(url, isCarMode) {
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
          speed: item.SPEED !== undefined ? item.SPEED : item.speed
        }));
        if (!points.length) {
          return false;
        }
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
        if (isCarMode && points.length > 0) {
          // 轨迹模式
          this.polyline = new window.BMap.Polyline(points.map(p => p.point), {strokeColor:"#0288d1", strokeWeight:5, strokeOpacity:0.8});
          this.map.addOverlay(this.polyline);
          this.map.setViewport(points.map(p => p.point));
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
        } else if (!isCarMode && points.length > 0) {
          // 散点模式
          this.map.setViewport(points.map(p => p.point));
          this.infoMarkers = [];
          points.forEach(p => {
            const marker = new window.BMap.Marker(p.point);
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
            let timeStr = p.time;
            if (typeof timeStr === 'string') {
              timeStr = timeStr.replace('T', ' ');
            }
            let speedStr = '';
            if (p.speed !== undefined && p.speed !== null && !isNaN(Number(p.speed))) {
              const v = Number(p.speed) / 100;
              speedStr = v.toFixed(2) + ' m/s';
            } else {
              speedStr = '0.00 m/s';
            }
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
        return true;
      } catch (e) {
        console.error('轨迹查询失败', e);
        showMsg('查询失败，请检查网络或稍后重试！');
        return false;
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
  background: #f7fafc;
}
.left-panel {
  width: 300px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 24px;
}
.right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  height: 100%;
}
.card.query-form {
  background: #ffffff;
  border-radius: 14px;
  box-shadow: 0 2px 8px rgba(2,136,209,0.07);
  padding: 22px 18px;
  color: #333;
  width: 100%;
  border: 1px solid #e3f2fd;
}
.card h3 {
  color: #0288d1;
  margin-bottom: 12px;
  font-weight: 600;
  font-size: 19px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.form-row {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}
.form-row label {
  width: 88px;
  color: #0288d1;
  font-weight: 500;
}
.card input {
  flex: 1;
  padding: 7px 10px;
  border-radius: 5px;
  border: 1px solid #b3e5fc;
  background: #fafdff;
  margin-left: 8px;
  font-size: 15px;
}
.card button {
  background: linear-gradient(90deg, #b3e5fc 0%, #81d4fa 100%);
  color: #0288d1;
  border: none;
  border-radius: 5px;
  padding: 7px 0;
  margin-top: 10px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 600;
  transition: background 0.2s;
}
.card button:hover {
  background: linear-gradient(90deg, #81d4fa 0%, #b3e5fc 100%);
}
.card button.long-btn {
  width: 100%;
  min-width: 120px;
  max-width: 100%;
  display: block;
}
.card button:disabled {
  background: #e0e0e0;
  color: #bdbdbd;
  cursor: not-allowed;
}
.map-chart {
  width: 100%;
  height: 90%;
  min-height: 480px;
  border-radius: 14px;
  box-shadow: 0 2px 12px rgba(2,136,209,0.08);
  background: #fff;
  border: 1px solid #e3f2fd;
  margin-bottom: 12px;
}
.btn-tooltip {
  position: absolute;
  left: 50%;
  top: 100%;
  transform: translateX(-50%);
  background: #fffbe6;
  color: #d48806;
  border: 1px solid #ffe58f;
  border-radius: 4px;
  padding: 6px 14px;
  font-size: 14px;
  white-space: nowrap;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  margin-top: 6px;
  z-index: 10;
}
</style> 