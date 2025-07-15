<template>
  <div class="shandong-map-container">
    <h2>山东省地图与人口分布（百度地图）</h2>
    <div ref="mapContainer" class="map-chart"></div>
  </div>
</template>

<script>
// 山东省各地市经纬度及人口数据（示例）
const cityData = [
  { name: '济南市', lng: 117.0009, lat: 36.6758, value: 920 },
  { name: '青岛市', lng: 120.3826, lat: 36.0671, value: 950 },
  { name: '烟台市', lng: 121.4479, lat: 37.4638, value: 700 },
  { name: '潍坊市', lng: 119.1618, lat: 36.7069, value: 650 },
  { name: '临沂市', lng: 118.3408, lat: 35.0724, value: 800 },
  { name: '淄博市', lng: 118.0549, lat: 36.8131, value: 600 },
  { name: '济宁市', lng: 116.5872, lat: 35.4146, value: 750 },
  { name: '泰安市', lng: 117.0876, lat: 36.2009, value: 500 },
  { name: '威海市', lng: 122.1204, lat: 37.5131, value: 400 },
  { name: '日照市', lng: 119.5269, lat: 35.4164, value: 350 },
  { name: '德州市', lng: 116.3646, lat: 37.4413, value: 420 },
  { name: '聊城市', lng: 115.9854, lat: 36.4570, value: 410 },
  { name: '滨州市', lng: 117.9774, lat: 37.3882, value: 390 },
  { name: '菏泽市', lng: 115.4807, lat: 35.2336, value: 600 },
  { name: '枣庄市', lng: 117.3237, lat: 34.8105, value: 380 }
];

export default {
  name: 'ShandongMap',
  mounted() {
    this.initBMap();
  },
  methods: {
    initBMap() {
      // eslint-disable-next-line
      const map = new window.BMap.Map(this.$refs.mapContainer);
      map.centerAndZoom(new window.BMap.Point(118.0009, 36.6758), 8);
      map.enableScrollWheelZoom(true);
      cityData.forEach(city => {
        const point = new window.BMap.Point(city.lng, city.lat);
        // marker
        const marker = new window.BMap.Marker(point);
        map.addOverlay(marker);
        // 气泡圆，半径与人口相关
        const circle = new window.BMap.Circle(point, city.value * 200, {
          strokeColor: '#0288d1',
          strokeWeight: 2,
          strokeOpacity: 0.6,
          fillColor: '#0288d1',
          fillOpacity: 0.18
        });
        map.addOverlay(circle);
        // 信息窗口
        const info = `<b>${city.name}</b><br/>人口：${city.value} 万人`;
        marker.addEventListener('mouseover', function() {
          const infoWin = new window.BMap.InfoWindow(info);
          marker.openInfoWindow(infoWin);
        });
        marker.addEventListener('mouseout', function() {
          marker.closeInfoWindow();
        });
      });
    }
  }
};
</script>

<style scoped>
.shandong-map-container {
  padding: 32px;
}
.map-chart {
  width: 100%;
  height: 700px;
  min-height: 500px;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(2,136,209,0.08);
  background: #fff;
  border: 1px solid #ccc;
  margin-top: 24px;
}
</style> 