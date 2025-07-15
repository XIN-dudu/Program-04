<template>
  <div class="subpage-container">
    <h2>周客流量分布</h2>
    <div ref="chart" style="width: 100%; height: 400px;"></div>
  </div>
</template>

<script>
import * as echarts from 'echarts'
import axios from 'axios'

export default {
  name: "Weekflow",
  mounted() {
    this.loadData()
  },
  methods: {
    async loadData() {
      // 默认统计 2013-09-12 到 2013-09-18
      const res = await axios.get('/api/week_flow/?start=2013-09-12&end=2013-09-18')
      const data = res.data
      const dates = data.map(item => item.date)
      const counts = data.map(item => item.count)
      this.drawChart(dates, counts)
    },
    drawChart(dates, counts) {
      const chart = echarts.init(this.$refs.chart)
      chart.setOption({
        title: { text: '一周客流量统计' },
        tooltip: {},
        xAxis: { type: 'category', data: dates },
        yAxis: { type: 'value' },
        series: [{
          data: counts,
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