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
        subdir = 'road/'
        save_path = os.path.join(subdir, file.name)
        # 保存文件
        filename = default_storage.save(save_path, file)
        # 生成完整URL
        file_url = request.build_absolute_uri(default_storage.url(filename))
        return Response({'message': '上传成功', 'url': file_url})
    
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