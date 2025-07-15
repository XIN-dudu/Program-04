<template>
  <div class="subpage-container">
    <h2>路程与道路数据可视化</h2>
    <div style="display: flex; gap: 40px; flex-wrap: wrap;">
      <div style="flex:1; min-width: 360px;">
        <h3>路程类型占比（2013-09-12）</h3>
        <div ref="pieChart" style="width: 100%; height: 360px;"></div>
      </div>
      <div style="flex:2; min-width: 480px;">
        <h3>一周平均速度变化</h3>
        <div ref="lineChart" style="width: 100%; height: 360px;"></div>
      </div>
    </div>
  </div>
</template>

<script>
import * as echarts from 'echarts'
import axios from 'axios'

export default {
  name: "Road",
  mounted() {
    this.loadPie()
    this.loadLine()
  },
  methods: {
    async loadPie() {
      // 默认取 2013-09-12 的路程类型占比
      const res = await axios.get('/api/road_distance_type/?start=2013-09-12&end=2013-09-12')
      const data = res.data[0] || {short:0, medium:0, long:0}
      const pieChart = echarts.init(this.$refs.pieChart)
      pieChart.setOption({
        title: { text: '短/中/长途订单占比', left: 'center' },
        tooltip: { trigger: 'item' },
        legend: { bottom: 0 },
        series: [{
          name: '订单数',
          type: 'pie',
          radius: '60%',
          data: [
            { value: data.short, name: '短途(≤4km)' },
            { value: data.medium, name: '中途(4~8km)' },
            { value: data.long, name: '长途(>8km)' }
          ],
          label: { formatter: '{b}: {c} ({d}%)' }
        }]
      })
    },
    async loadLine() {
      // 一周平均速度
      const res = await axios.get('/api/road_avg_speed/?start=2013-09-12&end=2013-09-18')
      const data = res.data
      const dates = data.map(item => item.date)
      const speeds = data.map(item => item.avg_speed)
      const lineChart = echarts.init(this.$refs.lineChart)
      lineChart.setOption({
        title: { text: '一周平均速度', left: 'center' },
        tooltip: {},
        xAxis: { type: 'category', data: dates },
        yAxis: { type: 'value', name: '速度(m/s)' },
        series: [{
          data: speeds,
          type: 'line',
          smooth: true
        }]
      })
    }
  }
}
</script>

<style scoped>
.subpage-container {
  padding: 32px;
}
</style> 