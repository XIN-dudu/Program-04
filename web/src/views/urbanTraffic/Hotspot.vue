<template>
  <div class="subpage-container">
    <h2>上客热点区域</h2>
    <div style="margin-bottom:16px;">
      <label>时间区间：</label>
      <input type="time" v-model="startTime" step="1"> -
      <input type="time" v-model="endTime" step="1">
      <button @click="fetchHeatmap">刷新热力图</button>
    </div>
    <div ref="chart" style="width: 100%; height: 600px;"></div>
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
      startTime: '08:00:00',
      endTime: '08:15:00',
      chart: null,
      points: [],
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
    fetchHeatmap() {
      axios.get('http://localhost:8000/heatmap/', {
        params: {
          date: '0912',
          start_time: this.startTime,
          end_time: this.endTime
        }
      }).then(res => {
        this.points = res.data.points;
        this.updateChart();
      }).catch(() => {
        // 数据请求失败时也要渲染一个默认option，防止visualMap丢失
        this.points = [];
        this.updateChart();
      });
    },
    updateChart() {
      if (!this.chart) return;
      // 只在有数据时才渲染热力图，否则渲染一个空的series
      const data = Array.isArray(this.points) && this.points.length > 0
        ? this.points.map(p => [p.lng, p.lat, 1])
        : [[117.0, 36.65, 1]]; // 给一个默认点，防止空数组
      const option = {
        title: { text: '济南0912上客热力图', left: 'center' },
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
      this.chart.clear(); // 先清空，防止option合并出错
      this.chart.setOption(option, true);
    }
  }
};
</script>

<style scoped>
.subpage-container {
  padding: 32px;
}
</style> 