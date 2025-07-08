<!-- 城市交通可视化 -->
<template>
  <div class="urban-traffic-platform">
    <div class="sidebar">
      <div class="card time-query">
        <h3>UTC时间查询</h3>
        <div class="time">{{ nowTime }}</div>
        <button @click="getNowTime">点击进行UTC时间查询</button>
      </div>
      <div class="card time-range-query">
        <h3>按时间查询</h3>
        <input v-model="startTime" placeholder="请输入起始时间戳" />
        <input v-model="endTime" placeholder="请输入终止时间戳" />
        <button @click="queryByTime">提交</button>
      </div>
      <div class="card car-query">
        <h3>按车辆查询</h3>
        <input v-model="carStartTime" placeholder="请输入起始时间戳" />
        <input v-model="carEndTime" placeholder="请输入终止时间戳" />
        <input v-model="carId" placeholder="请输入车牌标识" />
        <button @click="queryByCar">提交</button>
      </div>
      <div class="card analysis-result">
        <h3>数据分析结果</h3>
        <div>周客流量：{{ weekFlow }}</div>
        <div>路程分布：{{ roadStat }}</div>
      </div>
    </div>
    <div class="main-content">
      <div class="header">城市交通大数据服务平台</div>
      <div ref="mapChart" class="map-chart"></div>
    </div>
  </div>
</template>

<script>
import * as echarts from 'echarts';
import { ref, onMounted } from 'vue';

export default {
  name: 'UrbanTraffic',
  setup() {
    const nowTime = ref('');
    const getNowTime = () => {
      nowTime.value = new Date().toLocaleString();
    };
    const startTime = ref('');
    const endTime = ref('');
    const carStartTime = ref('');
    const carEndTime = ref('');
    const carId = ref('');
    const weekFlow = ref('示例：12000人');
    const roadStat = ref('示例：主干道占比60%');
    const mapChart = ref(null);

    // 示例点数据（可随意增减）
    const points = [
      { name: '北京', value: [116.4074, 39.9042, 100] },
      { name: '上海', value: [121.4737, 31.2304, 80] },
      { name: '广州', value: [113.2644, 23.1291, 60] },
      { name: '济南', value: [117.0009, 36.6758, 120] }
    ];

    const queryByTime = () => {
      alert(`查询时间段：${startTime.value} - ${endTime.value}`);
    };
    const queryByCar = () => {
      alert(`查询车辆：${carId.value}，时间段：${carStartTime.value} - ${carEndTime.value}`);
    };

    onMounted(async () => {
      try {
        getNowTime();
        // 1. 加载本地 geojson
        const geoJson = await fetch('/china.json').then(res => res.json());
        echarts.registerMap('china', geoJson);
        // 2. 初始化地图
        const myChart = echarts.init(mapChart.value);
        myChart.setOption({
          backgroundColor: '#f7faff',
          title: {
            text: '中国主要城市出租车热点分布（示例）',
            left: 'center',
            textStyle: { color: '#333', fontSize: 20 }
          },
          geo: {
            map: 'china',
            roam: true,
            label: { show: true, color: '#666' },
            itemStyle: {
              areaColor: '#e6f2ff',
              borderColor: '#a0cfff'
            },
            emphasis: {
              itemStyle: {
                areaColor: '#b3e5fc'
              }
            }
          },
          tooltip: {
            trigger: 'item',
            formatter: params => params.name + (params.value ? `<br/>热度: ${params.value[2]}` : '')
          },
          visualMap: {
            min: 0,
            max: 120,
            left: 'left',
            top: 'bottom',
            text: ['高', '低'],
            inRange: { color: ['#b3e5fc', '#0288d1'] },
            calculable: true
          },
          series: [
            {
              name: '热点',
              type: 'scatter',
              coordinateSystem: 'geo',
              data: points,
              symbolSize: val => Math.max(val[2] / 5, 10),
              label: {
                show: false
              },
              itemStyle: {
                color: '#0288d1'
              }
            },
            {
              name: '热力',
              type: 'heatmap',
              coordinateSystem: 'geo',
              data: points
            }
          ]
        });
      } catch (err) {
        console.error('地图加载或渲染出错:', err);
        alert('地图加载或渲染出错: ' + (err && err.message ? err.message : err));
      }
    });

    return {
      nowTime,
      getNowTime,
      startTime,
      endTime,
      carStartTime,
      carEndTime,
      carId,
      weekFlow,
      roadStat,
      queryByTime,
      queryByCar,
      mapChart
    };
  }
};
</script>

<style scoped>
.urban-traffic-platform { display: flex; height: 100vh; background: #f7faff; }
.sidebar { width: 320px; background: #fff; padding: 24px 12px; display: flex; flex-direction: column; gap: 18px; border-right: 1px solid #e0e0e0; }
.card { background: #f5faff; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); padding: 18px 14px; color: #333; margin-bottom: 8px; }
.card h3 { color: #0288d1; margin-bottom: 10px; }
.card input { width: 90%; margin: 6px 0; padding: 6px 8px; border-radius: 4px; border: 1px solid #b3e5fc; background: #fff; }
.card button { background: #0288d1; color: #fff; border: none; border-radius: 4px; padding: 6px 16px; margin-top: 8px; cursor: pointer; }
.card button:hover { background: #0277bd; }
.main-content { flex: 1; display: flex; flex-direction: column; background: #f7faff; }
.header { color: #0288d1; font-size: 28px; font-weight: bold; text-align: center; padding: 18px 0 8px 0; letter-spacing: 2px; }
.map-chart { flex: 1; min-height: 600px; margin: 0 18px 18px 0; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.08); background: #fff; }
.time { font-size: 18px; margin-bottom: 10px; }
</style>