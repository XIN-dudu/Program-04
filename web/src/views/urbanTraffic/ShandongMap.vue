<template>
  <div class="shandong-map-container">
    <div class="left-panel">
      <div class="button-group">
        <button 
          @click="showPopulationData" 
          class="action-btn"
          :class="{ active: currentView === 'population' }"
        >
          人口分布
        </button>
        <button 
          @click="showWeekFlow" 
          class="action-btn"
          :class="{ active: currentView === 'weekflow' }"
        >
          周客流量
        </button>
        <button 
          @click="showOccupiedTaxiCount" 
          class="action-btn"
          :class="{ active: currentView === 'occupied-taxi' }"
        >
          载客出租车数量
        </button>
      </div>
      <transition-group name="slide-stack" tag="div" class="stack-group">
        <div v-if="currentView === 'weekflow'" key="analysis" class="analysis-controls">
          <h4>分析类型</h4>
          <div class="radio-group">
            <label class="radio-item">
              <input type="radio" value="both" v-model="analysisType" @change="changeAnalysisType('both')" />
              <span>起点+终点</span>
            </label>
            <label class="radio-item">
              <input type="radio" value="origin" v-model="analysisType" @change="changeAnalysisType('origin')" />
              <span>仅起点</span>
            </label>
            <label class="radio-item">
              <input type="radio" value="destination" v-model="analysisType" @change="changeAnalysisType('destination')" />
              <span>仅终点</span>
            </label>
          </div>
          <div v-if="analysisSummary.total_trips > 0" class="summary-info">
            <h4>统计摘要</h4>
            <div class="summary-item"><span>总行程数：</span><span class="summary-value">{{ analysisSummary.total_trips }}</span></div>
            <div class="summary-item"><span>日均行程：</span><span class="summary-value">{{ analysisSummary.avg_trips_per_day }}</span></div>
            <div class="summary-item"><span>峰值时段：</span><span class="summary-value">{{ analysisSummary.peak_hour }}</span></div>
            <div class="summary-item"><span>峰值日期：</span><span class="summary-value">{{ analysisSummary.peak_day }}</span></div>
          </div>
        </div>
        <div v-if="currentView === 'occupied-taxi'" key="occupied-summary" class="analysis-controls">
          <h4>载客统计摘要</h4>
          <div v-if="occupiedTaxiData.total_occupied !== undefined" class="summary-info">
            <div class="summary-item"><span>总载客车辆：</span><span class="summary-value">{{ occupiedTaxiData.total_occupied }}</span></div>
            <div class="summary-item"><span>平均载客车辆：</span><span class="summary-value">{{ occupiedTaxiData.avg_occupied }}</span></div>
            <div class="summary-item"><span>峰值时段：</span><span class="summary-value">{{ occupiedTaxiData.peak_hour }}</span></div>
            <div class="summary-item"><span>更新时间：</span><span class="summary-value">{{ occupiedTaxiData.current_time }}</span></div>
          </div>
        </div>
        <div class="button-group" key="weather-btn">
          <button 
            @click="showTrafficWeather" 
            class="action-btn"
            :class="{ active: currentView === 'traffic-weather' }"
          >
            客流与天气
          </button>
        </div>
      </transition-group>
    </div>
    <div class="right-panel">
      <div ref="chart" class="map-chart"></div>
      <div v-if="loading && currentView === 'occupied-taxi'" class="loading-overlay">
        <div class="loading-spinner"></div>
        <div class="loading-text">正在加载载客出租车数据...</div>
      </div>
      <div v-if="weekFlowLoading && currentView === 'weekflow'" class="loading-overlay">
        <div class="loading-spinner"></div>
        <div class="loading-text">正在加载周客流量数据...</div>
      </div>
      <div v-if="weatherLoading && currentView === 'traffic-weather'" class="loading-overlay">
        <div class="loading-spinner"></div>
        <div class="loading-text">正在加载天气与客流数据...</div>
      </div>
      <div v-if="currentView === 'population' && showDataSource" class="data-source">
        数据来源：济南市统计局2022年数据
      </div>
      <div v-if="currentView === 'weekflow' && showDataSource" class="data-source-bottom">
        数据来源：济南市出租车GPS轨迹数据统计
      </div>
      <div v-if="currentView === 'occupied-taxi' && showDataSource" class="data-source-bottom">
        数据来源：济南市出租车实时载客状态统计
      </div>
    </div>
  </div>
</template>

<script>
import * as echarts from 'echarts';

const populationData = {
  '历下区': 620000,
  '市中区': 710000,
  '槐荫区': 670000,
  '天桥区': 620000,
  '历城区': 1160000,
  '长清区': 620000,
  '章丘区': 1100000,
  '济阳区': 340000,
  '莱芜区': 970000,
  '钢城区': 210000,
  '平阴县': 350000,
  '商河县': 590000
};
const colorRange = [
  '#e0f3f8', '#abd9e9', '#74add1', '#4575b4', '#313695'
];

export default {
  name: 'ShandongMap',
  data() {
    return {
      currentView: null,
      showDataSource: false,
      chart: null,
      weekFlowData: {},
      timeSlots: [],
      analysisType: 'both',
      analysisSummary: {},
      weatherFlowChart: null,
      weatherFlowData: [],
      occupiedTaxiData: {},
      loading: false,
      weekFlowLoading: false,
      weatherLoading: false,
    };
  },
  mounted() {
    this.loadGeoJSONAndRender();
  },
  methods: {
    async loadGeoJSONAndRender() {
      const res = await fetch('/static/data/JiNan.json');
      const jinanGeoJSON = await res.json();
      echarts.registerMap('jinan', jinanGeoJSON);
      this.initECharts();
    },
    initECharts() {
      this.chart = echarts.init(this.$refs.chart);
      this.renderBasicMap();
    },
    renderBasicMap() {
      if (this.chart) this.chart.clear();
      const option = {
        tooltip: { trigger: 'item', formatter: params => params.name },
        series: [{
          name: '济南市', type: 'map', map: 'jinan', roam: true,
          label: { show: true, color: '#222', fontSize: 12 },
          itemStyle: { areaColor: '#f5f5f5', borderColor: '#999', borderWidth: 1 },
          emphasis: { itemStyle: { areaColor: '#e0e0e0' } },
          data: []
        }]
      };
      this.chart.setOption(option, true);
    },
    renderPopulationMap() {
      if (this.chart) this.chart.clear();
      const populationDataArr = Object.entries(populationData).map(([name, value]) => ({ name, value }));
      const option = {
        tooltip: {
          trigger: 'item',
          formatter: params => `${params.name}<br/>人口：${params.value ? params.value.toLocaleString() : '无数据'}`
        },
        visualMap: {
          min: 200000, max: 1200000, left: 'left', top: 'bottom', text: ['高','低'],
          inRange: { color: colorRange }, calculable: true
        },
        series: [{
          name: '济南分区', type: 'map', map: 'jinan', roam: true,
          label: { show: true, color: '#222', fontSize: 12 },
          itemStyle: { borderColor: '#333', borderWidth: 1 },
          emphasis: { itemStyle: { areaColor: '#ffd700' } },
          data: populationDataArr
        }]
      };
      this.chart.setOption(option, true);
    },
    async renderWeekFlowChart() {
      if (this.chart) this.chart.clear();
      this.weekFlowLoading = true; // 开始加载
      try {
        const response = await fetch(`/api/od_analysis/?time_slots=12&analysis_type=${this.analysisType}`);
        const data = await response.json();
        if (data.error) {
          console.error('获取数据失败:', data.error);
          this.useSimulatedData();
          return;
        }
        this.timeSlots = data.time_slots;
        this.weekFlowData = data.week_data;
        this.analysisSummary = data.summary;
      } catch (error) {
        console.error('API请求失败:', error);
        this.useSimulatedData();
      } finally {
        this.weekFlowLoading = false; // 结束加载
      }
      const weekDays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'];
      const series = weekDays.map((day, index) => ({
        name: this.weekFlowData[day]?.name || `周${index + 1}`,
        type: 'bar',
        data: this.weekFlowData[day]?.data || [],
        itemStyle: { color: `hsl(${index * 51}, 70%, 60%)` }
      }));
      let title = '济南市周客流量时间分布';
      if (this.analysisType === 'origin') title = '济南市周起点客流量时间分布';
      else if (this.analysisType === 'destination') title = '济南市周终点客流量时间分布';
      const option = {
        title: { text: title, left: 'center', textStyle: { fontSize: 18, fontWeight: 'bold' } },
        tooltip: {
          trigger: 'axis', axisPointer: { type: 'shadow' },
          formatter: function(params) {
            let result = `${params[0].axisValue}<br/>`;
            params.forEach(param => { result += `${param.seriesName}: ${param.value} 次<br/>`; });
            return result;
          }
        },
        legend: { data: series.map(s => s.name), top: 30, left: 'center' },
        grid: { left: '3%', right: '4%', bottom: '15%', top: '15%', containLabel: true },
        xAxis: {
          type: 'category', data: this.timeSlots, name: '时间', nameLocation: 'end', nameGap: 10,
          axisLabel: { rotate: 45 }
        },
        yAxis: {
          type: 'value', name: '打车次数', nameLocation: 'start', nameGap: 10, nameTextStyle: { align: 'left' }
        },
        series: series
      };
      this.chart.setOption(option, true);
    },
         useSimulatedData() {
       this.timeSlots = [
         '00:00-02:00', '02:00-04:00', '04:00-06:00', '06:00-08:00',
         '08:00-10:00', '10:00-12:00', '12:00-14:00', '14:00-16:00',
         '16:00-18:00', '18:00-20:00', '20:00-22:00', '22:00-24:00'
       ];
       const timePattern = [50, 30, 40, 200, 350, 280, 320, 300, 400, 450, 380, 200];
       this.weekFlowData = {
         monday: { name: '周一', data: timePattern.map(v => v + Math.floor(Math.random() * 50) - 25) },
         tuesday: { name: '周二', data: timePattern.map(v => v + Math.floor(Math.random() * 50) - 25) },
         wednesday: { name: '周三', data: timePattern.map(v => v + Math.floor(Math.random() * 50) - 25) },
         thursday: { name: '周四', data: timePattern.map(v => v + Math.floor(Math.random() * 50) - 25) },
         friday: { name: '周五', data: timePattern.map(v => v + Math.floor(Math.random() * 50) - 25 + 50) },
         saturday: { name: '周六', data: timePattern.map(v => v + Math.floor(Math.random() * 50) - 25 + 30) },
         sunday: { name: '周日', data: timePattern.map(v => v + Math.floor(Math.random() * 50) - 25 + 20) }
       };
       const allData = Object.values(this.weekFlowData).flatMap(day => day.data);
       const totalTrips = allData.reduce((sum, val) => sum + val, 0);
       const avgTripsPerDay = Math.round(totalTrips / 7);
       const hourlyTotals = new Array(12).fill(0);
       Object.values(this.weekFlowData).forEach(day => {
         day.data.forEach((val, idx) => { hourlyTotals[idx] += val; });
       });
       const peakHourIdx = hourlyTotals.indexOf(Math.max(...hourlyTotals));
       const dailyTotals = Object.values(this.weekFlowData).map(day => day.data.reduce((sum, val) => sum + val, 0));
       const peakDayIdx = dailyTotals.indexOf(Math.max(...dailyTotals));
       const weekDayNames = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
       this.analysisSummary = {
         total_trips: totalTrips,
         avg_trips_per_day: avgTripsPerDay,
         peak_hour: this.timeSlots[peakHourIdx],
         peak_day: weekDayNames[peakDayIdx],
         analysis_type: this.analysisType
       };
     },
     useSimulatedOccupiedData() {
       const now = new Date();
       const timeSlots = [];
       const occupiedCounts = [];
       
       // 生成过去24小时的12个时间区间
       for (let i = 0; i < 12; i++) {
         const endTime = new Date(now.getTime() - i * 2 * 60 * 60 * 1000); // 每2小时一个区间
         const startTime = new Date(endTime.getTime() - 2 * 60 * 60 * 1000);
         
         if (i === 0) {
           timeSlots.push(`当前-${endTime.getHours().toString().padStart(2, '0')}:${endTime.getMinutes().toString().padStart(2, '0')}`);
         } else {
           timeSlots.push(`${startTime.getHours().toString().padStart(2, '0')}:${startTime.getMinutes().toString().padStart(2, '0')}-${endTime.getHours().toString().padStart(2, '0')}:${endTime.getMinutes().toString().padStart(2, '0')}`);
         }
         
         // 生成模拟的载客车辆数量（基于时间模式）
         let baseCount = 0;
         const hour = endTime.getHours();
         if (hour >= 7 && hour <= 9) baseCount = 180; // 早高峰
         else if (hour >= 17 && hour <= 19) baseCount = 200; // 晚高峰
         else if (hour >= 10 && hour <= 16) baseCount = 120; // 白天
         else if (hour >= 20 && hour <= 22) baseCount = 150; // 晚上
         else baseCount = 50; // 深夜
         
         // 添加随机波动
         const randomVariation = Math.floor(Math.random() * 40) - 20;
         occupiedCounts.push(Math.max(0, baseCount + randomVariation));
       }
       
       const totalOccupied = occupiedCounts.reduce((sum, val) => sum + val, 0);
       const avgOccupied = totalOccupied / occupiedCounts.length;
       const peakHourIdx = occupiedCounts.indexOf(Math.max(...occupiedCounts));
       
       this.occupiedTaxiData = {
         time_slots: timeSlots,
         occupied_counts: occupiedCounts,
         total_occupied: totalOccupied,
         avg_occupied: Math.round(avgOccupied * 100) / 100,
         peak_hour: timeSlots[peakHourIdx],
         current_time: now.toLocaleString('zh-CN')
       };
     },
    showPopulationData() {
      this.currentView = 'population';
      this.showDataSource = true;
      this.loading = false;
      this.weekFlowLoading = false;
      this.weatherLoading = false;
      this.renderPopulationMap();
    },
    showWeekFlow() {
      this.currentView = 'weekflow';
      this.showDataSource = true;
      this.loading = false;
      this.weekFlowLoading = false;
      this.weatherLoading = false;
      this.renderWeekFlowChart();
    },
    async showOccupiedTaxiCount() {
      this.currentView = 'occupied-taxi';
      this.showDataSource = true;
      this.loading = false;
      this.weekFlowLoading = false;
      this.weatherLoading = false;
      await this.renderOccupiedTaxiChart();
    },
         async renderOccupiedTaxiChart() {
       if (this.chart) this.chart.clear();
       this.loading = true; // 开始加载
       try {
         const response = await fetch('/api/occupied_taxi_count/');
         const data = await response.json();
         if (data.error) {
           console.error('获取载客出租车数据失败:', data.error);
           this.useSimulatedOccupiedData();
           return;
         }
         this.occupiedTaxiData = data;
       } catch (error) {
         console.error('API请求失败:', error);
         this.useSimulatedOccupiedData();
       } finally {
         this.loading = false; // 结束加载
       }
       
       if (!this.occupiedTaxiData.time_slots || !this.occupiedTaxiData.occupied_counts) {
         this.useSimulatedOccupiedData();
       }
       
       const option = {
         title: { 
           text: '载客出租车数量分布', 
           left: 'center', 
           textStyle: { fontSize: 18, fontWeight: 'bold' },
           subtext: '2013年9月12日载客车辆统计',
           subtextStyle: { fontSize: 12, color: '#666' }
         },
         tooltip: {
           trigger: 'axis',
           axisPointer: { type: 'shadow' },
           formatter: function(params) {
             let result = `${params[0].axisValue}<br/>`;
             params.forEach(param => { 
               result += `${param.seriesName}: <b>${param.value}</b> 辆<br/>`; 
             });
             return result;
           }
         },
         legend: { 
           data: ['载客车辆数'], 
           top: 40, 
           left: 'center' 
         },
         grid: { 
           left: '5%', 
           right: '5%', 
           bottom: '15%', 
           top: '20%', 
           containLabel: true 
         },
         xAxis: {
           type: 'category',
           data: this.occupiedTaxiData.time_slots,
           name: '时间区间',
           nameLocation: 'end',
           nameGap: 10,
           axisLabel: { 
             rotate: 45,
             fontSize: 10
           },
           axisTick: { alignWithLabel: true }
         },
         yAxis: {
           type: 'value',
           name: '载客车辆数',
           nameLocation: 'start',
           nameGap: 10,
           nameTextStyle: { align: 'left' },
           min: 0,
           splitLine: { show: true }
         },
         series: [{
           name: '载客车辆数',
           type: 'bar',
           data: this.occupiedTaxiData.occupied_counts,
           itemStyle: { 
             color: {
               type: 'linear',
               x: 0, y: 0, x2: 0, y2: 1,
               colorStops: [
                 { offset: 0, color: '#52c41a' },
                 { offset: 1, color: '#389e0d' }
               ]
             },
             borderRadius: [4, 4, 0, 0]
           },
           emphasis: {
             itemStyle: {
               color: {
                 type: 'linear',
                 x: 0, y: 0, x2: 0, y2: 1,
                 colorStops: [
                   { offset: 0, color: '#73d13d' },
                   { offset: 1, color: '#52c41a' }
                 ]
               }
             }
           },
           label: {
             show: true,
             position: 'top',
             fontSize: 10,
             color: '#333'
           }
         }]
       };
       this.chart.setOption(option, true);
     },
    async showTrafficWeather() {
      this.currentView = 'traffic-weather';
      this.showDataSource = false;
      this.loading = false;
      this.weekFlowLoading = false;
      this.weatherLoading = false;
      await this.renderWeatherFlowChart();
    },
    async renderWeatherFlowChart() {
      if (!this.weatherFlowChart) {
        this.weatherFlowChart = echarts.init(this.$refs.chart);
      } else {
        this.weatherFlowChart.clear();
      }
      this.weatherLoading = true; // 开始加载
      try {
        const res = await fetch('/api/weather_flow_analysis/');
        const data = await res.json();
        this.weatherFlowData = data;
      } catch (e) {
        this.weatherFlowData = [];
      } finally {
        this.weatherLoading = false; // 结束加载
      }
      if (!this.weatherFlowData.length) return;
      const times = this.weatherFlowData.map(d => d.time);
      const flows = this.weatherFlowData.map(d => d.flow);
      const temps = this.weatherFlowData.map(d => d.temperature);
      const hums = this.weatherFlowData.map(d => d.humidity);
      const winds = this.weatherFlowData.map(d => d.wind_speed);
      const precs = this.weatherFlowData.map(d => d.precip);
      const option = {
        title: { text: '天气变化与客流量关系', left: 'center', textStyle: { fontSize: 18, fontWeight: 'bold' } },
        tooltip: {
          trigger: 'axis', axisPointer: { type: 'cross' },
          formatter: params => {
            let t = params[0].axisValue;
            let html = `<b>${t}</b><br/>`;
            params.forEach(p => { html += `${p.marker}${p.seriesName}: <b>${p.value}</b><br/>`; });
            return html;
          }
        },
        legend: { data: ['客流量', '温度', '湿度', '风速', '降水量'], top: 40, left: 'center' },
        grid: { left: '5%', right: '8%', bottom: '10%', top: 80, containLabel: true },
        xAxis: { type: 'category', data: times, axisLabel: { rotate: 45 } },
        yAxis: [
          { type: 'value', name: '客流量', position: 'left', min: 0, axisLine: { show: true }, axisLabel: { color: '#1890ff' } },
          { type: 'value', name: '温度(°C)', position: 'right', offset: 0, axisLine: { show: true }, axisLabel: { color: '#faad14' } }
        ],
        dataZoom: [ { type: 'slider', start: 0, end: 100, xAxisIndex: 0 } ],
        series: [
          { name: '客流量', type: 'line', yAxisIndex: 0, data: flows, smooth: true, lineStyle: { color: '#1890ff' }, emphasis: { focus: 'series' } },
          { name: '温度', type: 'line', yAxisIndex: 1, data: temps, smooth: true, lineStyle: { color: '#faad14' }, emphasis: { focus: 'series' } },
          { name: '湿度', type: 'line', yAxisIndex: 1, data: hums, smooth: true, lineStyle: { color: '#52c41a' }, emphasis: { focus: 'series' } },
          { name: '风速', type: 'line', yAxisIndex: 1, data: winds, smooth: true, lineStyle: { color: '#722ed1' }, emphasis: { focus: 'series' } },
          { name: '降水量', type: 'line', yAxisIndex: 1, data: precs, smooth: true, lineStyle: { color: '#13c2c2' }, emphasis: { focus: 'series' } }
        ]
      };
      this.weatherFlowChart.setOption(option, true);
    },
    changeAnalysisType(type) {
      this.analysisType = type;
      if (this.currentView === 'weekflow') {
        this.renderWeekFlowChart();
      }
    },
  }
};
</script>

<style scoped>
.shandong-map-container {
  display: flex;
  height: calc(100vh - 120px);
  background: #f5f5f5;
  margin-bottom: 20px;
}
.left-panel {
  width: 300px;
  background: white;
  padding: 20px;
  box-shadow: 2px 0 10px rgba(0,0,0,0.1);
  margin-bottom: 20px;
}
.right-panel {
  flex: 1;
  position: relative;
  margin-bottom: 20px;
}
.map-chart {
  width: 100%;
  height: 100%;
}
.button-group {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-bottom: 15px;
}
.action-btn {
  padding: 15px 20px;
  border: none;
  border-radius: 8px;
  background: #f0f0f0;
  color: #333;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
  text-align: left;
}
.action-btn:hover {
  background: #e0e0e0;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}
.action-btn.active {
  background: #1890ff;
  color: white;
}
.data-source {
  position: absolute;
  bottom: 20px;
  right: 20px;
  background: rgba(0,0,0,0.7);
  color: white;
  padding: 10px 15px;
  border-radius: 5px;
  font-size: 12px;
  z-index: 1000;
}
.data-source-bottom {
  position: absolute;
  bottom: 20px;
  right: 20px;
  background: rgba(0,0,0,0.7);
  color: white;
  padding: 10px 15px;
  border-radius: 5px;
  font-size: 12px;
  z-index: 1000;
}
.stack-group {
  display: flex;
  flex-direction: column;
  gap: 15px;
}
.slide-stack-enter-active, .slide-stack-leave-active {
  transition: all 0.4s cubic-bezier(.55,0,.1,1);
}
.slide-stack-enter-from, .slide-stack-leave-to {
  opacity: 0;
  transform: translateY(-30px);
}
.slide-stack-move {
  transition: all 0.4s cubic-bezier(.55,0,.1,1);
}
.analysis-controls {
  margin-top: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}
.analysis-controls h4 {
  margin: 0 0 10px 0;
  color: #333;
  font-size: 14px;
  font-weight: 600;
}
.radio-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.radio-item {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 13px;
  color: #555;
}
.radio-item input[type="radio"] {
  margin: 0;
  cursor: pointer;
}
.radio-item span {
  cursor: pointer;
}
.summary-info {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #e9ecef;
}
.summary-info h4 {
  margin: 0 0 10px 0;
  color: #333;
  font-size: 14px;
  font-weight: 600;
}
.summary-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
  font-size: 12px;
  color: #666;
}
.summary-value {
  font-weight: 600;
  color: #1890ff;
}
.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  backdrop-filter: blur(2px);
}
.loading-spinner {
  border: 3px solid #f3f3f3;
  border-top: 3px solid #1890ff;
  border-radius: 50%;
  width: 50px;
  height: 50px;
  animation: spin 1s linear infinite;
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.3);
}
.loading-text {
  margin-top: 15px;
  font-size: 16px;
  color: #333;
  font-weight: 500;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style> 