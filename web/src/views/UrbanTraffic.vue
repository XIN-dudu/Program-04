<!-- 城市交通可视化 -->
<template>
  <div id="mapContainer" style="width: 100%; height: 600px;"></div>
</template>

<script>
export default {
  name: "UrbanTraffic",
  mounted() {
    this.initMap();
  },
  methods: {
    initMap() {
      console.log('initMap called');
      if (!window.BMap) {
        console.error('BMap is not loaded!');
        return;
      }
      const map = new window.BMap.Map("mapContainer");
      const point = new window.BMap.Point(116.404, 39.915);
      map.centerAndZoom(point, 12);
      map.enableScrollWheelZoom(true);
    }
  }
};
</script>

<style scoped>
#mapContainer {
  border: 1px solid #ccc;
}
</style>