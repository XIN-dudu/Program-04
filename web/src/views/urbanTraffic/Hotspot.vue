<template>
  <div class="hotspot-bg">
    <div class="hotspot-card">
      <h2 class="hotspot-title">上客热点区域</h2>
      <div class="hotspot-form-row">
        <label>日期：</label>
        <input type="date" v-model="selectedDate" :min="minDate" :max="maxDate" @change="onDateChange" class="hotspot-input" />
        <label>时间区间：</label>
        <input type="time" v-model="startTime" step="1" @change="onTimeInputChange" class="hotspot-input"> -
        <input type="time" v-model="endTime" step="1" @change="onTimeInputChange" class="hotspot-input">
        <button @click="fetchHeatmap" class="hotspot-btn">刷新热力图</button>
        <div v-if="sliderMax >= 0" class="hotspot-slider-row">
          <input type="range" :min="0" :max="sliderMax" :step="1" v-model="sliderValue" @input="onSliderChange" class="hotspot-slider">
        </div>
      </div>
      <div ref="chart" class="hotspot-map-card">
        <div class="hotspot-chart" ref="chartInner"></div>
      </div>
    </div>
    <transition name="fade">
      <div v-if="showNoDataDialog" class="hotspot-dialog-overlay">
        <div class="hotspot-dialog-box">
          <p>暂时没有数据</p>
          <button @click="showNoDataDialog = false" class="hotspot-btn">关闭</button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import * as echarts from 'echarts';
import 'echarts/extension/bmap/bmap';
import axios from 'axios';

export default {
  name: "Hotspot",
  data() {
    return {
      minDate: '2013-09-12',
      maxDate: '2013-09-18',
      selectedDate: '2013-09-12',
      startTime: '08:00:00',
      endTime: '10:00:00', // 默认结束时间改为10:00:00
      sliderValue: 0, // 当前窗口索引
      sliderMax: 23, // 最大窗口索引，动态计算
      windowMinutes: 5, // 窗口长度5分钟
      tempWindowStart: '', // 临时窗口start
      tempWindowEnd: '',   // 临时窗口end
      baseStartTime: '08:00:00', // 进度条区间起点
      chart: null,
      points: [],
      showNoDataDialog: false,
      option: {
        title: { text: '济南0912上客热力图', left: 'center' },
        bmap: {
          center: [117.0, 36.65],
          zoom: 13, // ← 这里就是初始缩放比例
          roam: true,
          mapStyle: {
            styleJson: []
          }
        },
        visualMap: {
          show: true,
          min: 0,
          max: 10,
          left: 'left',
          top: 'bottom',
          text: ['高','低'],
          calculable: true,
          inRange: {
            color: ['blue', 'green', 'yellow', 'red']
          }
        },
        series: [{
          type: 'heatmap',
          coordinateSystem: 'bmap',
          data: []
        }]
      }
    };
  },
  mounted() {
    this.initChart();
    this.updateSliderRange();
    this.fetchHeatmap();
  },
  methods: {
    initChart() {
      this.chart = echarts.init(this.$refs.chartInner);
      this.chart.setOption(this.option);
    },
    getDateParam() {
      // 只允许2013-09-12到2013-09-18
      const allowed = ["2013-09-12","2013-09-13","2013-09-14","2013-09-15","2013-09-16","2013-09-17","2013-09-18"];
      if (!allowed.includes(this.selectedDate)) {
        return null;
      }
      return this.selectedDate.slice(5,7) + this.selectedDate.slice(8,10); // 0912, 0913 ...
    },
    onDateChange() {
      if (!this.getDateParam()) {
        this.showNoDataDialog = true;
        return;
      }
      this.fetchHeatmap();
    },
    fetchHeatmap() {
      const dateParam = this.getDateParam();
      if (!dateParam) {
        this.showNoDataDialog = true;
        return;
      }
      // 用临时窗口start/end请求
      const start = this.tempWindowStart || this.startTime;
      const end = this.tempWindowEnd || this.endTime;
      axios.get('http://localhost:8000/heatmap/', {
        params: {
          date: dateParam,
          start_time: start,
          end_time: end
        }
      }).then(res => {
        this.points = res.data.points;
        this.updateChart();
      }).catch(() => {
        this.points = [];
        this.updateChart();
      });
    },
    updateChart() {
      if (!this.chart) return;
      const data = Array.isArray(this.points) && this.points.length > 0
        ? this.points.map(p => [p.lng, p.lat, 1])
        : [[117.0, 36.65, 1]];
      // 动态设置标题
      const dateParam = this.getDateParam() || '0912';
      const option = {
        title: { text: `济南${dateParam}上客热力图`, left: 'center' },
        bmap: {
          center: [117.0, 36.65],
          zoom: 13,
          roam: true,
          mapStyle: { styleJson: [] }
        },
        visualMap: {
          show: true,
          min: 0,
          max: Math.max(10, data.length / 100),
          left: 'left',
          top: 'bottom',
          text: ['高','低'],
          calculable: true,
          inRange: {
            color: ['blue', 'green', 'yellow', 'red']
          }
        },
        series: [{
          type: 'heatmap',
          coordinateSystem: 'bmap',
          data: data
        }]
      };
      this.chart.clear();
      this.chart.setOption(option, true);
    },
    // 计算时间字符串转秒
    toSec(t) {
      const [h, m, s] = t.split(":").map(Number);
      return h * 3600 + m * 60 + (s || 0);
    },
    // 计算秒转时间字符串
    secToTime(sec) {
      const h = String(Math.floor(sec / 3600)).padStart(2, '0');
      const m = String(Math.floor((sec % 3600) / 60)).padStart(2, '0');
      const s = String(sec % 60).padStart(2, '0');
      return `${h}:${m}:${s}`;
    },
    // 更新进度条区间和最大值
    updateSliderRange() {
      // 根据当前区间动态计算最大窗口数
      const s1 = this.toSec(this.startTime);
      const s2 = this.toSec(this.endTime);
      const total = s2 - s1;
      this.sliderMax = Math.max(0, Math.floor(total / (this.windowMinutes * 60)) - 1);
      this.sliderValue = 0;
      this.updateTempWindow();
    },
    updateTempWindow() {
      // 计算当前进度条对应的5分钟窗口
      const s1 = this.toSec(this.startTime);
      const startSec = s1 + this.sliderValue * this.windowMinutes * 60;
      const endSec = startSec + this.windowMinutes * 60;
      this.tempWindowStart = this.secToTime(startSec);
      this.tempWindowEnd = this.secToTime(endSec);
    },
    onSliderChange(e) {
      this.sliderValue = Number(e.target.value);
      this.updateTempWindow();
      this.fetchHeatmap();
    },
    // 当手动修改时间区间时，进度条自动适配新区间
    onTimeInputChange() {
      this.updateSliderRange();
      this.fetchHeatmap();
    }
  }
};
</script>

<style scoped>
.hotspot-bg {
  min-height: 100vh;
  background: linear-gradient(120deg, #e0f7fa 0%, #f5fafd 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
}
.hotspot-card {
  background: rgba(255,255,255,0.98);
  border-radius: 24px;
  box-shadow: 0 8px 32px rgba(2,136,209,0.10);
  padding: 38px 38px 32px 38px;
  min-width: 700px;
  max-width: 900px;
  width: 100%;
  margin: 0 auto;
  position: relative;
}
.hotspot-title {
  text-align: center;
  font-size: 2.2rem;
  font-weight: 800;
  color: #0288d1;
  margin-bottom: 32px;
  letter-spacing: 2px;
  text-shadow: 0 2px 12px rgba(2,136,209,0.08);
}
.hotspot-form-row {
  display: flex;
  align-items: center;
  gap: 18px;
  margin-bottom: 24px;
  flex-wrap: wrap;
  justify-content: center;
}
.hotspot-form-row label {
  color: #0288d1;
  font-weight: 600;
  font-size: 1.08rem;
}
.hotspot-input {
  padding: 10px 14px;
  border: 1.5px solid #b3e5fc;
  border-radius: 10px;
  font-size: 1.08rem;
  background: #fafdff;
  box-shadow: 0 2px 8px rgba(2,136,209,0.04);
  transition: border 0.2s, box-shadow 0.2s;
}
.hotspot-input:focus {
  border-color: #0288d1;
  outline: none;
  box-shadow: 0 0 0 2px #b3e5fc;
}
.hotspot-btn {
  background: linear-gradient(90deg,#00a1d6 0%,#00c6fb 100%);
  color: white;
  padding: 10px 28px;
  border: none;
  border-radius: 14px;
  cursor: pointer;
  font-size: 1.08rem;
  font-weight: bold;
  transition: background 0.2s, box-shadow 0.2s;
  box-shadow: 0 4px 16px rgba(0,161,214,0.10);
  letter-spacing: 1px;
}
.hotspot-btn:hover {
  background: linear-gradient(90deg,#00b5e5 0%,#00a1d6 100%);
  box-shadow: 0 6px 24px rgba(0,161,214,0.18);
}
.hotspot-slider-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 220px;
}
.hotspot-slider {
  width: 180px;
  accent-color: #00a1d6;
  height: 4px;
  border-radius: 4px;
  background: linear-gradient(90deg,#b3e5fc 0%,#00a1d6 100%);
}
.hotspot-map-card {
  width: 100%;
  height: 600px;
  background: #fff;
  border-radius: 18px;
  box-shadow: 0 4px 24px rgba(2,136,209,0.10);
  border: 2.5px solid #b3e5fc;
  overflow: hidden;
  display: flex;
  align-items: stretch;
  justify-content: stretch;
  margin-top: 8px;
  position: relative;
}
.hotspot-map-card ::v-deep .BMap_mask,
.hotspot-map-card ::v-deep .BMap_bmap,
.hotspot-map-card ::v-deep .BMap_bmap div,
.hotspot-map-card ::v-deep .BMap_bmap > div {
  position: static !important;
  max-width: 100% !important;
  max-height: 100% !important;
  width: 100% !important;
  height: 100% !important;
  left: 0 !important;
  top: 0 !important;
  border-radius: 18px !important;
  overflow: hidden !important;
}
.hotspot-chart {
  width: 100%;
  height: 100%;
  border-radius: 0;
  border: none;
  box-shadow: none;
  background: transparent;
}
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
.hotspot-dialog-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.18);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.hotspot-dialog-box {
  background: #fff;
  padding: 38px 60px;
  border-radius: 18px;
  box-shadow: 0 4px 32px rgba(2,136,209,0.15);
  font-size: 22px;
  text-align: center;
  min-width: 260px;
}
.hotspot-dialog-box p {
  margin-bottom: 18px;
  color: #0288d1;
  font-weight: 600;
  font-size: 1.18em;
}
</style> 