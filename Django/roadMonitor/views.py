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

from .serializers import RoadRecordSerializer

from .models import roadRecord


model = YOLO(os.path.join(settings.BASE_DIR, "best.pt"))

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
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # 调整帧尺寸
            frame = cv2.resize(frame, (width, height))
            
            # YOLO推理
            results = model(frame)
            annotated_frame = results[0].plot()
            
            # 写入处理后的帧
            out.write(annotated_frame)
        cap.release()
        out.release()
        # 构建访问URL
        rel_url = os.path.join(settings.MEDIA_URL, output_subdir, name)
        return rel_url
 
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
    record.length = random.uniform(1, 10)
    record.area = random.uniform(1, 100)
    record.path = file.name

    record.disease_type = 1
    record.severity = 1
    record.save()

    # 视频保存
    subdir = 'road'
    save_path = os.path.join(subdir, file.name)
    filename = default_storage.save(save_path, file)
    local_path = default_storage.path(filename)
    # 判断是否为视频文件
    if file.content_type.startswith('video/'):
        try:
            task = process_video_task(local_path, 'road/results', file.name)
            # 构建视频访问URL
            video_url = request.build_absolute_uri(task)
            print(video_url)
            return Response({'title' : '纵向裂纹', 'description': '检测到纵向裂缝约2.3米', 'severity': '中等', 'position': '翻斗花园123街区', "media_type": "video", "media_url": video_url}, status=200)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
 
    # 判断是否为图片文件
    if file.content_type.startswith('image/'):
        try:
            results = model(
                local_path,
                save=True,
                conf=0.5,
                project=os.path.join(settings.MEDIA_ROOT, subdir),  # 指定根目录
                name='results',    # 创建results子目录
                exist_ok=True
            )
            # 获取处理后的图片路径
            processed_dir = os.path.join(settings.MEDIA_ROOT, subdir, 'results')
            print(processed_dir)
            processed_filename = os.path.basename(file.name)
            print(processed_filename)
            processed_path = os.path.join(processed_dir, processed_filename)
            # print(processed_path)
            # 验证文件是否存在
            if not os.path.exists(processed_path):
                return JsonResponse({'status': 'error', 'message': '处理后的图片未生成'}, status=500)
            # 构建完整的URL
            relative_url = os.path.join(settings.MEDIA_URL, subdir, 'results', processed_filename)
            image_url = request.build_absolute_uri(relative_url)
            print(image_url)
            return Response({'title' : '纵向裂纹', 'description': '检测到纵向裂缝约2.3米', 'severity': '中等', 'position': '翻斗花园123街区', "media_type": "image", 'media_url': image_url}, status=200)
        
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

@api_view(['GET'])
def history_video(request):
    """
    获取历史检测视频记录。

    GET参数：无
    返回：
        - success (string): 操作结果
    示例返回：
        {"success": "ok"}
    """
    return Response({'success'})


@api_view(['DELETE'])
def history_delete(request):
    """
    删除历史检测记录。

    DELETE参数：无
    返回：
        - success (string): 操作结果
    示例返回：
        {"success": "ok"}
    """
    return Response({'success'})

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