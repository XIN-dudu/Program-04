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
        <button 
          @click="showTripDistanceAnalysis" 
          class="action-btn"
          :class="{ active: currentView === 'trip-distance' }"
        >
          路程分析
        </button>
        <button 
          @click="showRoadSpeed" 
          class="action-btn"
          :class="{ active: currentView === 'road-speed' }"
        >
          道路速度
        </button>
      </div>
      <transition-group name="slide-stack" tag="div" class="stack-group">
        <div v-if="currentView === 'weekflow'" key="analysis" class="analysis-controls">
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
        <div v-if="currentView === 'trip-distance'" key="trip-distance-summary" class="analysis-controls">
          <h4>路程分析摘要</h4>
          <div v-if="tripDistanceData.summary" class="summary-info">
            <div class="summary-item"><span>总行程数：</span><span class="summary-value">{{ tripDistanceData.summary.total_count }}</span></div>
            <div class="summary-item"><span>短途占比：</span><span class="summary-value">{{ tripDistanceData.summary.short_ratio }}%</span></div>
            <div class="summary-item"><span>中途占比：</span><span class="summary-value">{{ tripDistanceData.summary.medium_ratio }}%</span></div>
            <div class="summary-item"><span>长途占比：</span><span class="summary-value">{{ tripDistanceData.summary.long_ratio }}%</span></div>
            <div class="summary-item"><span>平均距离：</span><span class="summary-value">{{ tripDistanceData.summary.avg_total_distance }} km</span></div>
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
      <!-- 仅在载客出租车数量视图显示日期选择器 -->
      <div v-if="currentView === 'occupied-taxi'" style="margin-bottom: 16px;">
        <label>选择日期：</label>
        <input type="date" v-model="occupiedDate" min="2013-09-12" max="2013-09-18" @change="fetchOccupiedTaxiData" />
      </div>
      <div v-show="currentView !== 'road-speed'" ref="chart" class="map-chart"></div>
      <div v-show="currentView === 'road-speed'">
        <div ref="roadSpeedChart" style="width: 100%; height: 500px;"></div>
        <!-- 速度说明小圆点已删除 -->
      </div>
      <div v-if="loading && currentView === 'occupied-taxi'" class="loading-overlay">
        <div class="loading-spinner"></div>
        <div class="loading-text">正在加载载客出租车数据...</div>
      </div>
      <div v-if="weekFlowLoading && currentView === 'weekflow'" class="loading-overlay">
        <div class="loading-spinner"></div>
        <div class="loading-text">正在加载周客流量数据...</div>
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
      <div v-if="currentView === 'trip-distance' && showDataSource" class="data-source-bottom">
        数据来源：济南市出租车轨迹距离分析统计
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
      analysisType: 'both', // 默认起点+终点
      analysisSummary: {},
      weatherFlowChart: null,
      weatherFlowData: [],
      occupiedTaxiData: {},
      loading: false,
      weekFlowLoading: false,
      weatherLoading: false,
      tripDistanceData: {},
      tripDistanceLoading: false,
      roadSpeedChart: null, // 新增：道路速度图表实例
      occupiedDate: '2013-09-12', // 载客出租车数量当前选中日期
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
      this.loading = true;
      this.weekFlowLoading = false;
      this.weatherLoading = false;
      await this.fetchOccupiedTaxiData();
    },
         async renderOccupiedTaxiChart() {
       if (this.chart) this.chart.clear();
       // 只渲染，不再请求API，数据由fetchOccupiedTaxiData负责
       if (!this.occupiedTaxiData.time_slots || !this.occupiedTaxiData.occupied_counts) {
         return;
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
    async showTripDistanceAnalysis() {
      this.currentView = 'trip-distance';
      this.showDataSource = true;
      this.loading = false;
      this.weekFlowLoading = false;
      this.weatherLoading = false;
      this.tripDistanceLoading = false;
      await this.renderTripDistanceChart();
    },
    async renderTripDistanceChart() {
      if (this.chart) this.chart.clear();
      this.tripDistanceLoading = true;
      try {
        const response = await fetch('/api/trip_distance_analysis/?start_date=2013-09-12&end_date=2013-09-12');
        const data = await response.json();
        if (data.error) {
          console.error('获取路程分析数据失败:', data.error);
          this.useSimulatedTripDistanceData();
          return;
        }
        this.tripDistanceData = data;
      } catch (error) {
        console.error('API请求失败:', error);
        this.useSimulatedTripDistanceData();
      } finally {
        this.tripDistanceLoading = false;
      }
      if (!this.tripDistanceData.summary) {
        this.useSimulatedTripDistanceData();
      }
      // 饼状图数据
      const summary = this.tripDistanceData.summary;
      const pieData = [
        { value: summary.short_ratio, name: '短途(<4km)' },
        { value: summary.medium_ratio, name: '中途(4-8km)' },
        { value: summary.long_ratio, name: '长途(>8km)' }
      ];
      const option = {
        title: {
          text: '路程分析 - 距离占比',
          left: 'center',
          textStyle: { fontSize: 18, fontWeight: 'bold' },
          subtext: '2013年9月12日行程距离占比',
          subtextStyle: { fontSize: 12, color: '#666' }
        },
        tooltip: {
          trigger: 'item',
          formatter: '{b}: {d}% ({c})'
        },
        legend: {
          orient: 'vertical',
          left: 'left',
          data: ['短途(<4km)', '中途(4-8km)', '长途(>8km)']
        },
        series: [
          {
            name: '路程类型',
            type: 'pie',
            radius: '60%',
            center: ['50%', '60%'],
            data: pieData,
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowColor: 'rgba(0, 0, 0, 0.5)'
              }
            },
            label: {
              formatter: '{b}: {d}% ({c})'
            }
          }
        ]
      };
      this.chart.setOption(option, true);
    },
    useSimulatedTripDistanceData() {
      this.tripDistanceData = {
        summary: {
          total_count: 240,
          short_ratio: 40.5,
          medium_ratio: 35.2,
          long_ratio: 24.3,
          avg_total_distance: 5.6
        },
        daily_data: [
          { date: '2013-09-12', short_count: 100, medium_count: 80, long_count: 60 },
          { date: '2013-09-13', short_count: 110, medium_count: 70, long_count: 60 },
          { date: '2013-09-14', short_count: 90, medium_count: 85, long_count: 65 }
        ]
      };
    },
    async renderWeatherFlowChart() {
      if (!this.weatherFlowChart) {
        this.weatherFlowChart = echarts.init(this.$refs.chart);
      } else {
        this.weatherFlowChart.clear();
      }
      this.weatherLoading = true; // 开始加载
      try {
        // 使用预处理数据的API接口
        const res = await fetch('/api/weather_flow_analysis_preprocessed/');
        const data = await res.json();
        this.weatherFlowData = data;
      } catch (e) {
        console.error('天气客流数据获取失败:', e);
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
      const option = {
        title: { text: '天气变化与客流量关系', left: 'center', textStyle: { fontSize: 18, fontWeight: 'bold' } },
        tooltip: {
          trigger: 'axis', axisPointer: { type: 'cross' },
          formatter: params => {
            let t = params[0].axisValue;
            let html = `<b>${t}</b><br/>`;
            params.forEach(p => { html += `${p.marker}${p.seriesName}: <b>${p.value}</b> ${p.seriesName==='温度'?'°C':p.seriesName==='湿度'?'%':p.seriesName==='风速'?'m/s':''}<br/>`; });
            return html;
          }
        },
        legend: { data: ['客流量', '温度', '湿度', '风速'], top: 40, left: 'center' },
        grid: { left: '5%', right: '12%', bottom: '10%', top: 80, containLabel: true },
        xAxis: { type: 'category', data: times, axisLabel: { rotate: 45 } },
        yAxis: [
          { type: 'value', name: '客流量', position: 'left', min: 0, axisLine: { show: true }, axisLabel: { color: '#1890ff' } },
          { type: 'value', name: '温度(°C)', position: 'right', offset: 0, axisLine: { show: true }, axisLabel: { color: '#faad14' } },
          { type: 'value', name: '湿度(%)', position: 'right', offset: 60, axisLine: { show: true }, axisLabel: { color: '#52c41a' } },
          { type: 'value', name: '风速(m/s)', position: 'right', offset: 120, axisLine: { show: true }, axisLabel: { color: '#722ed1' } }
        ],
        series: [
          { name: '客流量', type: 'line', yAxisIndex: 0, data: flows, smooth: true, lineStyle: { color: '#1890ff' }, emphasis: { focus: 'series' } },
          { name: '温度', type: 'line', yAxisIndex: 1, data: temps, smooth: true, lineStyle: { color: '#faad14' }, emphasis: { focus: 'series' } },
          { name: '湿度', type: 'line', yAxisIndex: 2, data: hums, smooth: true, lineStyle: { color: '#52c41a' }, emphasis: { focus: 'series' } },
          { name: '风速', type: 'line', yAxisIndex: 3, data: winds, smooth: true, lineStyle: { color: '#722ed1' }, emphasis: { focus: 'series' } }
        ]
      };
      this.weatherFlowChart.setOption(option, true);
    },
    async showRoadSpeed() {
      this.currentView = 'road-speed';
      this.showDataSource = false;
      this.loading = true;
      this.$nextTick(async () => {
        let speedData = [];
        try {
          // 只请求后端接口
          const res = await fetch('/api/road_speed_hourly/');
          speedData = await res.json();
        } catch (e) {
          speedData = [];
        }
        this.loading = false;
        this.renderRoadSpeedHourLineChart(speedData);
      });
    },
    renderRoadSpeedHourLineChart(speedData) {
      if (!this.roadSpeedChart) {
        this.roadSpeedChart = echarts.init(this.$refs.roadSpeedChart);
      } else {
        this.roadSpeedChart.clear();
      }
      if (!Array.isArray(speedData) || speedData.length === 0) {
        this.roadSpeedChart.setOption({
          title: { text: '一天内不同时间段道路平均速度', left: 'center', textStyle: { fontSize: 18, fontWeight: 'bold' } },
          xAxis: { type: 'category', data: [] },
          yAxis: { type: 'value', name: '平均速度(km/h)' },
          series: []
        });
        return;
      }
      const hours = speedData.map(d => `${d.hour}:00`);
      const speeds = speedData.map(d => d.avg_speed);
      const option = {
        title: { text: '一天内不同时间段道路平均速度', left: 'center', textStyle: { fontSize: 18, fontWeight: 'bold' } },
        tooltip: {
          trigger: 'axis', axisPointer: { type: 'cross' },
          formatter: params => {
            let t = params[0].axisValue;
            let html = `<b>${t}</b><br/>`;
            params.forEach(p => { html += `${p.marker}${p.seriesName}: <b>${p.value} km/h</b><br/>`; });
            return html;
          }
        },
        grid: { left: '5%', right: '8%', bottom: '28%', top: '22%', containLabel: true },
        xAxis: { type: 'category', data: hours, axisLabel: { rotate: 0 } },
        yAxis: [{
          type: 'value', name: '平均速度(km/h)', position: 'left', min: 0, axisLine: { show: true }, axisLabel: { color: '#1890ff' }
        }],
        series: [
          { name: '平均速度', type: 'line', yAxisIndex: 0, data: speeds, smooth: true, lineStyle: { color: '#1890ff', width: 3 }, emphasis: { focus: 'series' }, symbol: 'none' }
        ],
        markLine: {
          symbol: 'none',
          data: [
            { yAxis: 20, name: '拥堵阈值' }
          ],
          lineStyle: { color: 'red', type: 'dashed' },
          label: { formatter: '拥堵阈值 20km/h', color: 'red', fontWeight: 'bold' }
        }
      };
      this.roadSpeedChart.setOption(option, true);
    },
    async fetchOccupiedTaxiData() {
      if (this.currentView !== 'occupied-taxi') return;
      this.loading = true;
      try {
        const res = await fetch(`/api/occupied_taxi_count_preprocessed/?date=${this.occupiedDate}`);
        const data = await res.json();
        this.occupiedTaxiData = data;
        this.renderOccupiedTaxiChart();
      } catch (e) {
        this.occupiedTaxiData = {};
      } finally {
        this.loading = false;
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