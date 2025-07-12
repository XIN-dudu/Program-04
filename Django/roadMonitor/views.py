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
from django.conf import settings
from ultralytics import YOLO
import cv2
import os

model = YOLO(os.path.join(settings.BASE_DIR, "best.pt"))
# Create your views here.

# #获取路面图像信息
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_image(request):
    file = request.FILES.get('file')
    roadId = request.POST.get('roadId')

    if not roadId:
        return JsonResponse({'status': 'error', 'message': '缺少道路编号'},status=400)
    
    # allowed_types = ['video/webm', 'video/mp4']
    # if file.content_type not in allowed_types:
    #     return JsonResponse({'status': 'error', 'message': '不支持的视频格式'}, status=400)
    
    if not file:
        return Response({'message': '没有提供文件'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # 创建子目录路径
        subdir = 'road'
        save_path = os.path.join(subdir, file.name)
        # 保存文件
        filename = default_storage.save(save_path, file)
        print(filename)
        local_path = default_storage.path(filename)
        print(local_path)
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
        processed_filename = os.path.basename(file.name)
        processed_path = os.path.join(processed_dir, processed_filename)
        print(processed_path)
        # 验证文件是否存在
        if not os.path.exists(processed_path):
            return JsonResponse({'status': 'error', 'message': '处理后的图片未生成'}, status=500)
        # 构建完整的URL
        relative_url = os.path.join(settings.MEDIA_URL, subdir, 'results', processed_filename)
        image_url = request.build_absolute_uri(relative_url)
        print(image_url)
        return Response({'title' : '纵向裂纹', 'description': '检测到纵向裂缝约2.3米', 'severity': '中等', 'position': '翻斗花园123街区', 'image_url': image_url}, status=200)
    
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@api_view(['GET'])
def history_get(request):

    return Response({'success'})

@api_view(['GET'])
def history_video(request):

    return Response({'success'})


@api_view(['DELETE'])
def history_delete(request):

    return Response({'success'})

@api_view(['GET'])
def heatmap_data(request):
    """
    参数:
        start_time: 形如 '08:00:00'（可选，默认00:00:00）
        end_time:   形如 '08:15:00'（可选，默认23:59:59）
        date:       形如 '0912'（可选，默认0912）
    返回:
        [{"lng": 经度, "lat": 纬度} ...]
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