<template>
  <div class="subpage-container">
    <h2>上客热点区域</h2>
    <div style="margin-bottom:16px; display: flex; align-items: center; gap: 16px;">
      <label>日期：</label>
      <input type="date" v-model="selectedDate" :min="minDate" :max="maxDate" @change="onDateChange" />
      <label>时间区间：</label>
      <input type="time" v-model="startTime" step="1" @change="onTimeInputChange"> -
      <input type="time" v-model="endTime" step="1" @change="onTimeInputChange">
      <button @click="fetchHeatmap">刷新热力图</button>
      <!-- 新增进度条 -->
      <div v-if="sliderMax >= 0" style="display:flex;align-items:center;gap:8px;min-width:220px;">
        <input type="range" :min="0" :max="sliderMax" :step="1" v-model="sliderValue" @input="onSliderChange">
        <!-- 删除窗口时间段显示 -->
      </div>
    </div>
    <div ref="chart" style="width: 100%; height: 600px;"></div>
    <div v-if="showNoDataDialog" class="dialog-overlay">
      <div class="dialog-box">
        <p>暂时没有数据</p>
        <button @click="showNoDataDialog = false">关闭</button>
      </div>
    </div>
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
      this.chart = echarts.init(this.$refs.chart);
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
.subpage-container {
  padding: 32px;
}
.dialog-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.dialog-box {
  background: #fff;
  padding: 32px 48px;
  border-radius: 12px;
  box-shadow: 0 2px 16px rgba(0,0,0,0.15);
  font-size: 20px;
  text-align: center;
}
</style> 