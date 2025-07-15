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

CLASS_LABELS = {
    0: "D00",  # 纵向裂纹
    1: "D10",  # 横向裂纹
    2: "D20",  # 龟裂
    3: "D40",  # 坑槽
    4: "repair"  # 修补区域
}

model = YOLO(os.path.join(settings.BASE_DIR, "best.pt"))

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
    # record.length = random.uniform(1, 10)
    # record.area = random.uniform(1, 100)
    record.path = file.name
    # record.disease_type = 1
    record.severity = 1

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
            res = request.build_absolute_uri(task)
            record.length = res['max_length'] * 0.01  # 应用转换系数
            record.area = res['total_area'] * (0.01**2)
            record.save()
            video_url = res['rel_url']
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
                pixel_to_meter = 0.003
                record.length = max_length * pixel_to_meter
                record.area = total_area * (pixel_to_meter**2)

                # 根据标签生成动态响应
                if label == "D00":
                    record.disease_type = 1
                elif label == "D10":
                    record.disease_type = 2
                elif label == "D20":
                    record.disease_type = 3
                elif label == "D40":
                    record.disease_type = 4
                elif label == "repair":
                    record.disease_type = 5
                    record.severity = 0
            else:
                record.length = 0.0
                record.area = 0.0
                record.disease_type = 0
                record.severity = 0
            record.save()
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
    date = request.GET.get('date', '0912')
    start_time = request.GET.get('start_time', '00:00:00')
    end_time = request.GET.get('end_time', '23:59:59')
    # 文件路径
    file_path = os.path.join(settings.BASE_DIR, f'..', 'pandas', 'data_clean_od_pairs', f'jn{date}_od_pairs.csv')
    file_path = os.path.abspath(file_path)
    if not os.path.exists(file_path):
        return Response({'error': '数据文件不存在'}, status=404)
    # 只读取部分数据，防止内存溢出
    df = pd.read_csv(file_path, usecols=['O_LON', 'O_LAT', 'O_TIME'], nrows=500000)  # 可调整nrows
    # 时间筛选
    try:
        df['O_TIME'] = pd.to_datetime(df['O_TIME'])
        start_dt = df['O_TIME'].dt.normalize()[0].strftime('%Y-%m-%d') + ' ' + start_time
        end_dt = df['O_TIME'].dt.normalize()[0].strftime('%Y-%m-%d') + ' ' + end_time
        mask = (df['O_TIME'] >= start_dt) & (df['O_TIME'] < end_dt)
        df = df[mask]
    except Exception as e:
        return Response({'error': f'时间筛选失败: {str(e)}'}, status=400)
    # 组装热力图点
    points = [
        {'lng': row['O_LON'], 'lat': row['O_LAT']} for _, row in df.iterrows()
    ]
    return Response({'points': points})