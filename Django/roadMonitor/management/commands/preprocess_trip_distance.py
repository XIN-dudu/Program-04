from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
import pymysql
import pandas as pd
import os
from django.conf import settings
from roadMonitor.models import TripDistanceStat
import math


class Command(BaseCommand):
    help = '预处理路程分析数据，计算每天短途/中途/长途的统计信息'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='要处理的日期 (YYYY-MM-DD)',
            default='2013-09-12'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制重新处理，覆盖现有数据'
        )

    def handle(self, *args, **options):
        target_date = options['date']
        force = options['force']
        
        self.stdout.write(f"开始预处理路程分析数据，日期: {target_date}")
        
        if force:
            # 删除现有数据
            TripDistanceStat.objects.filter(date=target_date).delete()
            self.stdout.write("已删除现有数据，开始重新处理...")
        
        self.preprocess_trip_distance_data(target_date)
        
        self.stdout.write(self.style.SUCCESS('路程分析数据预处理完成！'))

    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """计算两点间的距离（公里）"""
        # 使用Haversine公式计算球面距离
        R = 6371  # 地球半径（公里）
        
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        distance = R * c
        
        return distance

    def classify_trip_distance(self, distance):
        """根据距离分类行程"""
        if distance < 4:
            return 'short'
        elif distance <= 8:
            return 'medium'
        else:
            return 'long'

    def preprocess_trip_distance_data(self, target_date):
        """预处理路程分析数据"""
        self.stdout.write("正在预处理路程分析数据...")
        
        try:
            target_datetime = datetime.strptime(target_date, '%Y-%m-%d')
            
            # 连接数据库
            conn = pymysql.connect(
                host='122.9.42.250',
                user='root',
                password='Xin123456',
                database='program-04',
                charset='utf8'
            )
            cursor = conn.cursor()
            
            # 获取指定日期的所有载客轨迹数据
            sql = """
                SELECT 
                    COMMADDR,
                    UTC,
                    LAT,
                    LON,
                    status
                FROM jn0912_baidu_coords 
                WHERE DATE(UTC) = %s 
                ORDER BY COMMADDR, UTC
            """
            cursor.execute(sql, (target_date,))
            rows = cursor.fetchall()
            
            if not rows:
                self.stdout.write(self.style.WARNING(f"未找到 {target_date} 的数据"))
                return
            
            # 按车牌分组处理轨迹
            trips_by_car = {}
            current_car = None
            current_trip = []
            
            for row in rows:
                car_id, utc, lat, lon, status = row
                
                if current_car != car_id:
                    # 处理上一辆车的轨迹
                    if current_trip:
                        self.process_car_trips(current_car, current_trip, trips_by_car)
                    current_car = car_id
                    current_trip = []
                
                current_trip.append({
                    'utc': utc,
                    'lat': float(lat),
                    'lon': float(lon),
                    'status': status
                })
            
            # 处理最后一辆车的轨迹
            if current_trip:
                self.process_car_trips(current_car, current_trip, trips_by_car)
            
            # 统计每天的距离分布
            daily_stats = {
                'short_count': 0,
                'medium_count': 0,
                'long_count': 0,
                'short_distances': [],
                'medium_distances': [],
                'long_distances': [],
                'all_distances': []
            }
            
            # 处理所有行程
            for car_id, trips in trips_by_car.items():
                for trip in trips:
                    if len(trip) >= 2:  # 至少需要起点和终点
                        start_point = trip[0]
                        end_point = trip[-1]
                        
                        distance = self.calculate_distance(
                            start_point['lat'], start_point['lon'],
                            end_point['lat'], end_point['lon']
                        )
                        
                        trip_type = self.classify_trip_distance(distance)
                        daily_stats[f'{trip_type}_count'] += 1
                        daily_stats[f'{trip_type}_distances'].append(distance)
                        daily_stats['all_distances'].append(distance)
            
            # 计算平均距离
            avg_short = sum(daily_stats['short_distances']) / len(daily_stats['short_distances']) if daily_stats['short_distances'] else 0
            avg_medium = sum(daily_stats['medium_distances']) / len(daily_stats['medium_distances']) if daily_stats['medium_distances'] else 0
            avg_long = sum(daily_stats['long_distances']) / len(daily_stats['long_distances']) if daily_stats['long_distances'] else 0
            avg_total = sum(daily_stats['all_distances']) / len(daily_stats['all_distances']) if daily_stats['all_distances'] else 0
            
            # 保存到数据库
            TripDistanceStat.objects.update_or_create(
                date=target_datetime.date(),
                defaults={
                    'short_count': daily_stats['short_count'],
                    'medium_count': daily_stats['medium_count'],
                    'long_count': daily_stats['long_count'],
                    'avg_short_distance': round(avg_short, 2),
                    'avg_medium_distance': round(avg_medium, 2),
                    'avg_long_distance': round(avg_long, 2),
                    'avg_total_distance': round(avg_total, 2),
                }
            )
            
            cursor.close()
            conn.close()
            
            total_trips = daily_stats['short_count'] + daily_stats['medium_count'] + daily_stats['long_count']
            self.stdout.write(f"路程分析数据预处理完成:")
            self.stdout.write(f"  - 总行程数: {total_trips}")
            self.stdout.write(f"  - 短途(<4km): {daily_stats['short_count']} 次")
            self.stdout.write(f"  - 中途(4-8km): {daily_stats['medium_count']} 次")
            self.stdout.write(f"  - 长途(>8km): {daily_stats['long_count']} 次")
            self.stdout.write(f"  - 平均距离: {avg_total:.2f} km")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"路程分析数据预处理失败: {str(e)}"))

    def process_car_trips(self, car_id, trajectory, trips_by_car):
        """处理单辆车的轨迹，提取载客行程"""
        if car_id not in trips_by_car:
            trips_by_car[car_id] = []
        
        # 按载客状态分组
        current_trip = []
        for point in trajectory:
            if point['status'] == 1:  # 载客状态
                current_trip.append(point)
            else:  # 空车状态
                if current_trip:  # 结束当前行程
                    trips_by_car[car_id].append(current_trip)
                    current_trip = []
        
        # 处理最后一个行程
        if current_trip:
            trips_by_car[car_id].append(current_trip) 