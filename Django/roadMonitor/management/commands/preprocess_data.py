from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
import pymysql
import pandas as pd
import os
from django.conf import settings
from roadMonitor.models import PreprocessedData


class Command(BaseCommand):
    help = '预处理数据并存储到preprocessed_data表中'

    def add_arguments(self, parser):
        parser.add_argument(
            '--data-type',
            type=str,
            choices=['weather_flow', 'occupied_taxi', 'weekly_flow', 'all'],
            default='all',
            help='要预处理的数据类型'
        )
        parser.add_argument(
            '--date',
            type=str,
            help='要处理的日期 (YYYY-MM-DD)',
            default='2013-09-12'
        )

    def handle(self, *args, **options):
        data_type = options['data_type']
        target_date = options['date']
        
        self.stdout.write(f"开始预处理数据: {data_type}, 日期: {target_date}")
        
        if data_type in ['weather_flow', 'all']:
            self.preprocess_weather_flow_data(target_date)
        
        if data_type in ['occupied_taxi', 'all']:
            self.preprocess_occupied_taxi_data(target_date)
        
        if data_type in ['weekly_flow', 'all']:
            self.preprocess_weekly_flow_data(target_date)
        
        self.stdout.write(self.style.SUCCESS('数据预处理完成！'))

    def preprocess_weather_flow_data(self, target_date):
        """预处理天气客流数据"""
        self.stdout.write("正在预处理天气客流数据...")
        
        try:
            # 读取天气数据
            weather_path = os.path.abspath(os.path.join(settings.BASE_DIR, '..', 'web', 'public', 'static', 'data', 'jn_weather_c.csv'))
            weather_df = pd.read_csv(weather_path)
            weather_df['Time_new'] = pd.to_datetime(weather_df['Time_new'])
            weather_df.set_index('Time_new', inplace=True)
            
            # 过滤目标日期的数据
            target_datetime = datetime.strptime(target_date, '%Y-%m-%d')
            weather_data = weather_df[weather_df.index.date == target_datetime.date()]
            
            # 连接数据库获取客流量数据
            conn = pymysql.connect(
                host='122.9.42.250',
                user='root',
                password='Xin123456',
                database='program-04',
                charset='utf8'
            )
            cursor = conn.cursor()
            
            # 获取所有OD表名
            cursor.execute("SHOW TABLES LIKE '%_od_pairs'")
            od_tables = [row[0] for row in cursor.fetchall()]
            
            # 统计每小时客流量
            flow_dict = {}
            if od_tables:
                union_queries = []
                for table_name in od_tables:
                    union_queries.append(f"SELECT o_time FROM {table_name}")
                
                union_sql = " UNION ALL ".join(union_queries)
                cursor.execute(union_sql)
                
                for row in cursor.fetchall():
                    if row[0] is not None:
                        t = pd.to_datetime(row[0])
                        if t.date() == target_datetime.date():
                            hour = t.hour
                            if hour not in flow_dict:
                                flow_dict[hour] = 0
                            flow_dict[hour] += 1
            
            cursor.close()
            conn.close()
            
            # 保存到数据库
            for hour in range(24):
                weather_row = weather_data[weather_data.index.hour == hour]
                if not weather_row.empty:
                    w = weather_row.iloc[0]
                    passenger_flow = flow_dict.get(hour, 0)
                    
                    PreprocessedData.objects.update_or_create(
                        data_type='weather_flow',
                        date=target_datetime.date(),
                        hour=hour,
                        defaults={
                            'temperature': float(w['Temperature']),
                            'humidity': float(w['Humidity']),
                            'wind_speed': float(w['Wind_Speed']),
                            'precip': float(w['Precip']),
                            'passenger_flow': passenger_flow,
                        }
                    )
            
            self.stdout.write(f"天气客流数据预处理完成，共处理 {len(weather_data)} 条记录")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"天气客流数据预处理失败: {str(e)}"))

    def preprocess_occupied_taxi_data(self, target_date):
        """预处理载客出租车数据"""
        self.stdout.write("正在预处理载客出租车数据...")
        
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
            
            # 动态拼接表名
            table_name = f"jn{target_datetime.month:02d}{target_datetime.day:02d}_baidu_coords"
            # 统计每小时载客出租车数量
            sql = f"""
                SELECT 
                    HOUR(UTC) as hour,
                    COUNT(DISTINCT COMMADDR) as occupied_count
                FROM {table_name}
                WHERE DATE(UTC) = %s AND status = 1
                GROUP BY HOUR(UTC)
                ORDER BY hour
            """
            cursor.execute(sql, (target_date,))
            hourly_data = {row[0]: row[1] for row in cursor.fetchall()}
            
            cursor.close()
            conn.close()
            
            # 保存到数据库
            for hour in range(24):
                occupied_count = hourly_data.get(hour, 0)
                
                PreprocessedData.objects.update_or_create(
                    data_type='occupied_taxi',
                    date=target_datetime.date(),
                    hour=hour,
                    defaults={
                        'occupied_taxi_count': occupied_count,
                    }
                )
            
            self.stdout.write(f"载客出租车数据预处理完成，共处理 24 小时数据")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"载客出租车数据预处理失败: {str(e)}"))

    def preprocess_weekly_flow_data(self, target_date):
        """预处理周客流量数据"""
        self.stdout.write("正在预处理周客流量数据...")
        
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
            
            # 获取所有OD表名
            cursor.execute("SHOW TABLES LIKE '%_od_pairs'")
            od_tables = [row[0] for row in cursor.fetchall()]
            
            # 统计每周各天的客流量
            week_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            week_day_names = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
            
            for table_name in od_tables:
                # 统计每个表的客流量
                sql = """
                    SELECT 
                        DAYOFWEEK(o_time) as day_of_week,
                        HOUR(o_time) as hour,
                        COUNT(*) as trip_count
                    FROM {}
                    WHERE o_time IS NOT NULL
                    GROUP BY DAYOFWEEK(o_time), HOUR(o_time)
                """.format(table_name)
                
                cursor.execute(sql)
                results = cursor.fetchall()
                
                for day_of_week, hour, trip_count in results:
                    # 转换MySQL的DAYOFWEEK (1=Sunday) 到我们的格式 (0=Monday)
                    day_idx = (day_of_week - 2) % 7  # 转换为周一=0的格式
                    day_name = week_day_names[day_idx]
                    
                    PreprocessedData.objects.update_or_create(
                        data_type='weekly_flow',
                        date=target_datetime.date(),
                        hour=hour,
                        time_slot=day_name,
                        defaults={
                            'passenger_flow': trip_count,
                            'total_trips': trip_count,
                        }
                    )
            
            cursor.close()
            conn.close()
            
            self.stdout.write(f"周客流量数据预处理完成")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"周客流量数据预处理失败: {str(e)}")) 