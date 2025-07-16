import random
import time
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.files.storage import default_storage
from rest_framework import status
import os
from django.conf import settings
import pandas as pd
from datetime import datetime, timedelta
from ultralytics import YOLO
import cv2
from django.db import connection
from sklearn.cluster import DBSCAN
import numpy as np

from .serializers import RoadRecordSerializer

from .models import roadRecord

CLASS_LABELS = {
    0: "D00",  # 纵向裂纹
    1: "D10",  # 横向裂纹
    2: "D20",  # 龟裂
    3: "D40",  # 坑槽
    4: "repair"  # 修补区域
}

types = ['无', '纵向裂纹', '横向裂纹', '龟裂', '坑槽', '修补区域']
risk_type = ['安全', '低', '中', '高']

model = YOLO(os.path.join(settings.BASE_DIR, "best.pt"))

def checkSeverity(length, area, type):
    sum = 0.0
    if type == 0 or type == 1:
        sum += 5
    else:
        sum += type * 5
    sum += length
    sum += area
    if sum <= 10 or type == 0 or type == 5:
        return 0
    elif sum <= 30 and sum > 10:
        return 1
    elif sum > 30 and sum <= 50:
        return 2
    return 3

def getLabel(label):
    type = 0
    if label == "D00":
        type = 1
    elif label == "D10":
        type = 2
    elif label == "D20":
        type = 3
    elif label == "D40":
        type = 4
    elif label == "repair":
        type = 5
    return type

def tostring(length, area):
    return f'裂纹长度:{length:.2f}米\n裂纹面积:{area:.2f}平方米'

def checkChange(length, area, type):

    return True
def calculate_dimensions(boxes):
    """计算检测框的尺寸信息"""
    max_length = 0.0
    total_area = 0.0
    
    for box in boxes:
        x1, y1, x2, y2 = box.xyxy[0].tolist()  # 获取边界框坐标
        width = x2 - x1
        height = y2 - y1
        
        # 计算面积和长度（取最长边）
        area = width * height
        length = max(width, height)
        
        total_area += area
        max_length = max(max_length, length)
    
    return max_length, total_area

def process_video_task(video_path, output_subdir, name):
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError("无法打开视频文件")
        # 创建输出目录
        output_dir = os.path.join(settings.MEDIA_ROOT, output_subdir)
        os.makedirs(output_dir, exist_ok=True)
        # 准备视频写入器
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        output_path = os.path.join(output_dir, name)
        fourcc = cv2.VideoWriter_fourcc(*'avc1')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        max_length = 0.0
        total_area = 0.0
        frame_count = 0
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            frame_count += 1
            if frame_count % 5 == 0 :
                # 调整帧尺寸
                frame = cv2.resize(frame, (width, height))
                if frame_count % 5 == 0:
                    results = model(frame)
                if results and len(results[0].boxes) > 0:
                    current_max, current_area = calculate_dimensions(results[0].boxes)
                    max_length = max(max_length, current_max)
                    total_area += current_area
                # YOLO推理
                results = model(frame)
                annotated_frame = results[0].plot()
                
                # 写入处理后的帧
                out.write(annotated_frame)
        cap.release()
        out.release()
        # 构建访问URL
        rel_url = os.path.join(settings.MEDIA_URL, output_subdir, name)
        return {
            'rel_url': rel_url,
            'max_length': max_length,
            'total_area': total_area
        }
 
    except Exception as e:
        # 记录详细日志
        return {'status': 'error', 'message': '视频处理失败'}


# Create your views here.

# #获取路面图像信息
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_image(request):
    """
    上传路面图像并检测裂缝。

    POST参数：
        - file (file, 必填): 路面图片文件
        - roadId (string, 必填): 道路编号
    返回：
        - title (string): 检测类型
        - description (string): 检测描述
        - severity (string): 严重程度
        - position (string): 位置描述
        - image_url (string): 检测结果图片URL
    示例返回：
        {
            "title": "纵向裂纹",
            "description": "检测到纵向裂缝约2.3米",
            "severity": "中等",
            "position": "翻斗花园123街区",
            "image_url": "http://..."
        }
    """
    file = request.FILES.get('file')
    roadId = request.POST.get('roadId')

    if not roadId:
        return JsonResponse({'status': 'error', 'message': '缺少道路编号'},status=400)
    
    if not file:
        return Response({'message': '没有提供文件'}, status=status.HTTP_400_BAD_REQUEST)
    
    record = roadRecord()
    record.road_id = roadId
    record.detection_time = datetime.now()
    record.path = file.name

    # 保存
    subdir = 'road'
    save_path = os.path.join(subdir, 'upload', file.name)
    if not default_storage.exists(save_path):
        default_storage.save(save_path, file)
    local_path = default_storage.path(save_path)
    print(local_path)
    # 判断是否为视频文件
    if file.content_type.startswith('video/'):
        try:
            record.file_type = 0
            task = process_video_task(local_path, 'road/results', file.name)
            # 构建视频访问URL
            res = request.build_absolute_uri(task)
            record.length = res['max_length'] * 0.001  # 应用转换系数
            record.area = res['total_area'] * (0.001**2)
            record.severity = checkSeverity(record.length, record.area, 1)
            record.save()
            video_url = res['rel_url']
            print(video_url)
            return Response({'title' : types[record.disease_type],
                            'description': tostring(record.length, record.area),
                            'severity': risk_type[record.severity],
                            'position': ('翻斗花园街区' + record.road_id),
                            "media_type": "video",
                            "media_url": video_url},
                            status=200)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    # 判断是否为图片文件
    if file.content_type.startswith('image/'):
        try:
            record.file_type = 1
            results = model(
                local_path,
                save=True,
                conf=0.5,
                project=os.path.join(settings.MEDIA_ROOT, subdir),  # 指定根目录
                name='results',    # 创建results子目录
                exist_ok=True
            )
            record.length = 0.0
            record.area = 0.0
            record.disease_type = 0
            if results and len(results[0].boxes) > 0:
                # 获取检测结果
                boxes = results[0].boxes
                classes = boxes.cls.cpu().numpy()  # 获取类别索引
                confidences = boxes.conf.cpu().numpy()  # 获取置信度
                
                # 找到最高置信度的检测结果
                main_idx = confidences.argmax()
                class_idx = int(classes[main_idx])
                label = CLASS_LABELS.get(class_idx, "unknown")

                # 计算尺寸
                max_length, total_area = calculate_dimensions(boxes)
                
                # 应用物理尺寸转换
                pixel_to_meter = 0.001
                record.length = max_length * pixel_to_meter
                record.area = total_area * (pixel_to_meter**2)
                record.disease_type = getLabel(label)

            # 根据标签生成动态响应
            record.severity = checkSeverity(record.length, record.area, record.disease_type)
            # 获取处理后的图片路径
            processed_dir = os.path.join(settings.MEDIA_ROOT, subdir, 'results')
            #print(processed_dir)
            processed_filename = os.path.splitext(file.name)[0]
            #print(processed_filename)
            processed_path = os.path.join(processed_dir, f"{processed_filename}.jpg")
            print(processed_path)
            # 验证文件是否存在
            if not os.path.exists(processed_path):
                return JsonResponse({'status': 'error', 'message': '处理后的图片未生成'}, status=500)
            # 构建完整的URL
            relative_url = os.path.join(settings.MEDIA_URL, subdir, 'results', f"{processed_filename}.jpg")
            image_url = request.build_absolute_uri(relative_url)
            print(image_url)
            record.description = {
                'title': types[record.disease_type],
                'position': ('翻斗花园街区' + record.road_id),
                'severity': risk_type[record.severity],
                'length': record.length,
                'area': record.area,
                "media_type": "image",
                'media_url': file.name
                }
            record.save()
            return Response({'title' : types[record.disease_type],
                            'description': tostring(record.length, record.area),
                            'severity': risk_type[record.severity],
                            'position': ('翻斗花园街区' + record.road_id),
                            "media_type": "image",
                            'media_url': image_url},
                            status=200)
        
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@api_view(['GET'])
def history_get(request):
    """
    获取历史检测记录。

    GET参数：无
    返回：
        - success (string): 操作结果
    示例返回：
        {"success": "ok"}
    """
    records = roadRecord.objects.all()
    serializer = RoadRecordSerializer(records, many=True)
    print(serializer.data)
    return Response(serializer.data)

@api_view(['DELETE'])
def history_delete(request, diseaseId):
    """
    删除历史检测记录。

    DELETE参数：无
    返回：
        - success (string): 操作结果
    示例返回：
        {"success": "ok"}
    """
    try:
        # 查询需要删除数据库的记录
        records = roadRecord.objects.filter(
            disease_id = diseaseId,
        )
        
        if not records.exists():
            return Response({'error': '记录不存在'}, status=404)
 
        # 删除物理文件
        for record in records:
            if record.path:
                try:
                    file_path = os.path.join(settings.MEDIA_ROOT, 'road/upload', record.path)
                    print(file_path)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    file_path = os.path.join(settings.MEDIA_ROOT, 'road' , 'results', record.path)
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    file_path = os.path.join(settings.MEDIA_ROOT, 'road' , 'results', f'{os.path.splitext(record.path)[0]}.jpg')
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    if record.file_type == 0:
                        print(1)
                except Exception as e:
                    print(f"文件删除失败: {str(e)}")
 
        # 删除数据库记录
        records.delete()
 
        return Response({'success': 'ok'})
 
    except Exception as e:
        return Response({'error': f'服务器错误: {str(e)}'}, status=500)

@api_view(['GET'])
def heatmap_data(request):
    """
    获取热力图数据。

    GET参数：
        - start_time (string, 可选): 起始时间，格式如 '08:00:00'，默认00:00:00
        - end_time (string, 可选): 结束时间，格式如 '08:15:00'，默认23:59:59
        - date (string, 可选): 日期，格式如 '0912'，默认0912
    返回：
        - points (list): 热力图点列表，每个点含 lng(经度), lat(纬度)
    示例返回：
        {"points": [{"lng": 117.1, "lat": 36.6}, ...]}
    """
    import pymysql
    date = request.GET.get('date', '0912')
    start_time = request.GET.get('start_time', '00:00:00')
    end_time = request.GET.get('end_time', '23:59:59')
    table_name = f'jn{date}_od_pairs'

    # 正确拼接日期字符串
    month = date[:2]
    day = date[2:]
    date_str = f"2013-{month}-{day}"
    start_dt = f"{date_str} {start_time}"
    end_dt = f"{date_str} {end_time}"

    try:
        conn = pymysql.connect(
            host='122.9.42.250',
            user='root',
            password='Xin123456',
            database='program-04',
            charset='utf8'
        )
        cursor = conn.cursor()
        sql = f"""
            SELECT o_lon, o_lat, o_time
            FROM {table_name}
            WHERE o_time >= %s AND o_time < %s
            LIMIT 500000
        """
        cursor.execute(sql, (start_dt, end_dt))
        rows = cursor.fetchall()
        points = [
            {'lng': float(row[0]), 'lat': float(row[1])}
            for row in rows if row[0] is not None and row[1] is not None
        ]
        cursor.close()
        conn.close()
        return Response({'points': points})
    except Exception as e:
        import traceback
        return Response({'error': str(e), 'trace': traceback.format_exc()}, status=500)

@api_view(['GET'])
def heatmap_clustered(request):
    """
    获取聚类后的热力图数据。
    GET参数：
        - start_time (string, 可选): 起始时间，格式如 '08:00:00'，默认00:00:00
        - end_time (string, 可选): 结束时间，格式如 '08:15:00'，默认23:59:59
        - date (string, 可选): 日期，格式如 '0912'，默认0912
        - eps (float, 可选): DBSCAN聚类半径，单位为经纬度，默认0.002
        - min_samples (int, 可选): DBSCAN最小聚类点数，默认10
    返回：
        - points (list): 热力图点列表，每个点含 lng(经度), lat(纬度), weight(聚类点数)
    """
    import pymysql
    date = request.GET.get('date', '0912')
    start_time = request.GET.get('start_time', '00:00:00')
    end_time = request.GET.get('end_time', '23:59:59')
    eps = float(request.GET.get('eps', 0.002))  # 约200米
    min_samples = int(request.GET.get('min_samples', 10))
    table_name = f'jn{date}_od_pairs'

    # 拼接日期字符串
    month = date[:2]
    day = date[2:]
    date_str = f"2013-{month}-{day}"
    start_dt = f"{date_str} {start_time}"
    end_dt = f"{date_str} {end_time}"

    try:
        conn = pymysql.connect(
            host='122.9.42.250',
            user='root',
            password='Xin123456',
            database='program-04',
            charset='utf8'
        )
        cursor = conn.cursor()
        sql = f"""
            SELECT o_lon, o_lat
            FROM {table_name}
            WHERE o_time >= %s AND o_time < %s
            LIMIT 500000
        """
        cursor.execute(sql, (start_dt, end_dt))
        rows = cursor.fetchall()
        points = [
            [float(row[0]), float(row[1])]
            for row in rows if row[0] is not None and row[1] is not None
        ]
        cursor.close()
        conn.close()

        if not points:
            return Response({'points': []})

        # DBSCAN聚类
        X = np.array(points)
        db = DBSCAN(eps=eps, min_samples=min_samples).fit(X)
        labels = db.labels_

        clusters = []
        for label in set(labels):
            if label == -1:
                continue  # 忽略噪声点
            cluster_points = X[labels == label]
            center = cluster_points.mean(axis=0)
            weight = len(cluster_points)
            clusters.append({
                "lng": float(center[0]),
                "lat": float(center[1]),
                "weight": weight
            })

        return Response({'points': clusters})
    except Exception as e:
        import traceback
        return Response({'error': str(e), 'trace': traceback.format_exc()}, status=500)

@api_view(['GET'])
def week_flow(request):
    """
    统计一周内每天的客流量（订单数）。
    GET参数：
        - start (string, 可选): 起始日期，格式如 '2013-09-12'
        - end (string, 可选): 结束日期，格式如 '2013-09-18'
    返回：
        - [{date: '2013-09-12', count: 123}, ...]
    """
    start_date = request.GET.get('start', '2013-09-12')
    end_date = request.GET.get('end', '2013-09-18')
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT DATE(o_time) as day, COUNT(*) as count
            FROM jn0912_od_pairs
            WHERE o_time BETWEEN %s AND %s
            GROUP BY day
            ORDER BY day
        """, [start_date, end_date])
        rows = cursor.fetchall()
    from datetime import datetime, timedelta
    result = []
    d1 = datetime.strptime(start_date, "%Y-%m-%d")
    d2 = datetime.strptime(end_date, "%Y-%m-%d")
    day_map = {row[0].strftime("%Y-%m-%d"): row[1] for row in rows}
    for i in range((d2 - d1).days + 1):
        day = (d1 + timedelta(days=i)).strftime("%Y-%m-%d")
        result.append({"date": day, "count": day_map.get(day, 0)})
    return JsonResponse(result, safe=False)

@api_view(['GET'])
def road_distance_type(request):
    """
    统计每天短途（<=4km）、中途（4~8km）、长途（>8km）订单数量。
    GET参数：
        - start (string, 可选): 起始日期，格式如 '2013-09-12'
        - end (string, 可选): 结束日期，格式如 '2013-09-18'
    返回：
        - [{date, short, medium, long}]
    """
    start_date = request.GET.get('start', '2013-09-12')
    end_date = request.GET.get('end', '2013-09-18')
    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT DATE(o_time) as day,
                SUM(CASE WHEN distance IS NOT NULL AND distance <= 4000 THEN 1 ELSE 0 END) as short,
                SUM(CASE WHEN distance IS NOT NULL AND distance > 4000 AND distance <= 8000 THEN 1 ELSE 0 END) as medium,
                SUM(CASE WHEN distance IS NOT NULL AND distance > 8000 THEN 1 ELSE 0 END) as `long_trip`
            FROM jn0912_od_pairs
            WHERE o_time BETWEEN %s AND %s
            GROUP BY day
            ORDER BY day
        ''', [start_date, end_date])
        rows = cursor.fetchall()
    from datetime import datetime, timedelta
    result = []
    d1 = datetime.strptime(start_date, "%Y-%m-%d")
    d2 = datetime.strptime(end_date, "%Y-%m-%d")
    day_map = {row[0].strftime("%Y-%m-%d"): {'short': row[1] or 0, 'medium': row[2] or 0, 'long': row[3] or 0} for row in rows}
    for i in range((d2 - d1).days + 1):
        day = (d1 + timedelta(days=i)).strftime("%Y-%m-%d")
        v = day_map.get(day, {'short': 0, 'medium': 0, 'long': 0})
        result.append({"date": day, **v})
    return JsonResponse(result, safe=False)

@api_view(['GET'])
def road_avg_speed(request):
    """
    统计每天所有订单的平均速度（单位：m/s）。
    GET参数：
        - start (string, 可选): 起始日期，格式如 '2013-09-12'
        - end (string, 可选): 结束日期，格式如 '2013-09-18'
    返回：
        - [{date, avg_speed}]
    """
    start_date = request.GET.get('start', '2013-09-12')
    end_date = request.GET.get('end', '2013-09-18')
    with connection.cursor() as cursor:
        cursor.execute('''
            SELECT DATE(o_time) as day, AVG(speed) as avg_speed
            FROM jn0912_od_pairs
            WHERE o_time BETWEEN %s AND %s
            GROUP BY day
            ORDER BY day
        ''', [start_date, end_date])
        rows = cursor.fetchall()
    from datetime import datetime, timedelta
    result = []
    d1 = datetime.strptime(start_date, "%Y-%m-%d")
    d2 = datetime.strptime(end_date, "%Y-%m-%d")
    day_map = {row[0].strftime("%Y-%m-%d"): (row[1] if row[1] is not None else 0) for row in rows}
    for i in range((d2 - d1).days + 1):
        day = (d1 + timedelta(days=i)).strftime("%Y-%m-%d")
        avg = day_map.get(day, 0)
        result.append({"date": day, "avg_speed": round(avg, 2) if avg else 0})
    return JsonResponse(result, safe=False)