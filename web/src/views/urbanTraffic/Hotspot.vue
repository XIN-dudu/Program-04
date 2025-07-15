<template>
  <div class="subpage-container">
    <h2>上客热点区域</h2>
    <div style="margin-bottom:16px; display: flex; align-items: center; gap: 16px;">
      <label>日期：</label>
      <input type="date" v-model="selectedDate" :min="minDate" :max="maxDate" @change="onDateChange" />
      <label>时间区间：</label>
      <input type="time" v-model="startTime" step="1"> -
      <input type="time" v-model="endTime" step="1">
      <button @click="fetchHeatmap">刷新热力图</button>
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
      endTime: '08:15:00',
      chart: null,
      points: [],
      showNoDataDialog: false,
      option: {
        title: { text: '济南0912上客热力图', left: 'center' },
        bmap: {
          center: [117.0, 36.65],
          zoom: 12,
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
      axios.get('http://localhost:8000/heatmap/', {
        params: {
          date: dateParam,
          start_time: this.startTime,
          end_time: this.endTime
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
          zoom: 12,
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