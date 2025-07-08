from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import parser_classes

from web.serializers import UserSerializer
from .models import UserProfile, UserFaceImage
import random
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import os
import base64
import json
import requests

# 简单内存验证码存储（生产建议用redis等）
email_code_cache = {}

# 百度人脸识别API配置
# 下面的值需要替换为你的百度云API信息
BAIDU_API_KEY = "NypddVrKw1QSvISLwoEtmUfT" 
BAIDU_SECRET_KEY = "VTfOhjLs9Bq0taXoJKoWdfLlJZ4NUkeR"
BAIDU_APP_ID = "119454489"
# 获取百度云token
def get_baidu_token():
    url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={BAIDU_API_KEY}&client_secret={BAIDU_SECRET_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('access_token')
    return None

# 百度人脸库管理
def add_face_to_baidu(image_path, user_id, user_info=None):
    """添加人脸到百度人脸库"""
    token = get_baidu_token()
    if not token:
        return None
    
    url = f"https://aip.baidubce.com/rest/2.0/face/v3/faceset/user/add?access_token={token}"
    
    with open(image_path, 'rb') as f:
        image_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    data = {
        "image": image_base64,
        "image_type": "BASE64",
        "group_id": "user_faces",
        "user_id": str(user_id),
        "user_info": user_info or ""
    }
    
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(data), headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('error_code') == 0:
            return result.get('result', {}).get('face_token')
    return None

# Create your views here.

@api_view(['GET', 'POST'])
def get_data(request):
    if request.method == 'GET':
        user = User.objects.all()
        serializer = UserSerializer(user, many=True)
        return Response(serializer.data)
    if request.method == 'POST':
        print("fdawhdjiwajdawj")
        serializer = UserSerializer(data = request.data)
        print(serializer)
        return Response(status=status.HTTP_200_OK)

@api_view(['GET', 'PUT', 'DELETE'])
def user_detail(request, id):
    try:
        user = User.objects.get(id = id)
    except User.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
    if request.method == 'GET':
        serializer = UserSerializer(user)
        return Response(serializer.data)
    if request.method == 'PUT':
        serializer = UserSerializer(user, data=request.data)
        if serializer.is_valid:
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    if request.method == 'DELETE':
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# 注册接口
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def register(request):
    # 获取基本用户信息
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email')
    phone = request.data.get('phone')
    
    # 检查必填字段
    if not all([username, password, email, phone]):
        return Response({'msg': '用户名、密码、邮箱和手机号不能为空'}, status=status.HTTP_400_BAD_REQUEST)
    
    # 检查唯一性
    if UserProfile.objects.filter(username=username).exists():
        return Response({'msg': '用户名已存在'}, status=status.HTTP_400_BAD_REQUEST)
    if UserProfile.objects.filter(email=email).exists():
        return Response({'msg': '邮箱已存在'}, status=status.HTTP_400_BAD_REQUEST)
    if UserProfile.objects.filter(phone=phone).exists():
        return Response({'msg': '手机号已存在'}, status=status.HTTP_400_BAD_REQUEST)
    
    # 获取人脸图片列表
    face_images = request.FILES.getlist('face_images')
    if len(face_images) < 3:
        return Response({'msg': '请上传至少三张人脸图片'}, status=status.HTTP_400_BAD_REQUEST)
    
    # 创建用户
    user = UserProfile(
        username=username,
        password=password,
        email=email,
        phone=phone,
        face_image=face_images[0]  # 使用第一张图片作为主头像
    )
    user.save()
    
    # 保存所有人脸图片
    for image in face_images:
        user_face = UserFaceImage(user=user, image=image)
        user_face.save()
        
        # 获取保存后的图片路径
        image_path = user_face.image.path
        
        # 上传到百度人脸库（如果配置了百度API）
        if all([BAIDU_API_KEY, BAIDU_SECRET_KEY, BAIDU_APP_ID]) and BAIDU_API_KEY != "你的百度云API Key":
            try:
                face_token = add_face_to_baidu(
                    image_path, 
                    user.id, 
                    f"{{'username': '{username}', 'email': '{email}'}}"
                )
                if face_token:
                    user_face.face_token = face_token
                    user_face.save()
            except Exception as e:
                print(f"上传到百度人脸库失败: {e}")
    
    return Response({'msg': '注册成功'}, status=status.HTTP_201_CREATED)

# 登录接口
@api_view(['POST'])
def login(request):
    username = request.data.get('username') or request.data.get('name')
    password = request.data.get('password')
    print('收到登录请求:', username, password)
    if not username or not password:
        print('用户名或密码为空')
        return Response({'msg': '用户名和密码不能为空'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user = UserProfile.objects.get(username=username)
        if user.password == password:
            print('登录成功:', username)
            return Response({'msg': '登录成功'}, status=status.HTTP_200_OK)
        else:
            print('密码错误:', username)
            return Response({'msg': '密码错误'}, status=status.HTTP_400_BAD_REQUEST)
    except UserProfile.DoesNotExist:
        print('用户不存在:', username)
        return Response({'msg': '用户不存在'}, status=status.HTTP_400_BAD_REQUEST)

# 发送邮箱验证码接口
@api_view(['POST'])
def send_email_code(request):
    email = request.data.get('email')
    if not email:
        return Response({'msg': '邮箱不能为空'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user = UserProfile.objects.get(email=email)
    except UserProfile.DoesNotExist:
        return Response({'msg': '该邮箱未注册'}, status=status.HTTP_400_BAD_REQUEST)
    # 生成6位验证码
    code = str(random.randint(100000, 999999))
    # 发送邮件
    try:
        to_addr = email
        smtp_server = 'smtp.qq.com'
        msg = MIMEText(f'您的登录验证码是：{code}，5分钟内有效。', 'plain', 'utf-8')
        from email.utils import formataddr
        msg['From'] = formataddr(("验证码登录", from_addr))
        msg['To'] = Header(to_addr, 'utf-8')
        msg['Subject'] = Header("登录验证码", 'utf-8')
        server = smtplib.SMTP_SSL(smtp_server, 465)
        server.login(from_addr, password)
        server.sendmail(from_addr, [to_addr], msg.as_string())
        server.quit()
    except Exception as e:
        return Response({'msg': f'邮件发送失败: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    # 存储验证码
    email_code_cache[email] = code
    return Response({'msg': '验证码已发送'})

# 邮箱验证码登录接口
@api_view(['POST'])
def email_login(request):
    email = request.data.get('email')
    code = request.data.get('code')
    if not email or not code:
        return Response({'msg': '邮箱和验证码不能为空'}, status=status.HTTP_400_BAD_REQUEST)
    real_code = email_code_cache.get(email)
    if not real_code:
        return Response({'msg': '请先获取验证码'}, status=status.HTTP_400_BAD_REQUEST)
    if code != real_code:
        return Response({'msg': '验证码错误'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user = UserProfile.objects.get(email=email)
        # 登录成功后可做session/token等处理
        return Response({'msg': '登录成功'}, status=status.HTTP_200_OK)
    except UserProfile.DoesNotExist:
        return Response({'msg': '用户不存在'}, status=status.HTTP_400_BAD_REQUEST)
    
# 人脸识别接口
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def face_recognition(request):
    """人脸识别接口，通过上传图片识别用户"""
    if 'image' not in request.FILES:
        return Response({'msg': '请上传图片'}, status=status.HTTP_400_BAD_REQUEST)
    
    image = request.FILES['image']
    
    # 保存上传的图片到临时目录
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp:
        temp_path = temp.name
        for chunk in image.chunks():
            temp.write(chunk)
    
    # 调用百度人脸识别API搜索人脸
    token = get_baidu_token()
    if not token:
        os.unlink(temp_path)  # 删除临时文件
        return Response({'msg': '人脸识别服务暂不可用'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    url = f"https://aip.baidubce.com/rest/2.0/face/v3/search?access_token={token}"
    
    with open(temp_path, 'rb') as f:
        image_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    data = {
        "image": image_base64,
        "image_type": "BASE64",
        "group_id_list": "user_faces",
        "max_face_num": 1
    }
    
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(url, data=json.dumps(data), headers=headers)
        os.unlink(temp_path)  # 删除临时文件
        
        if response.status_code == 200:
            result = response.json()
            if result.get('error_code') == 0:
                user_list = result.get('result', {}).get('user_list', [])
                if user_list and len(user_list) > 0:
                    # 获取置信度最高的结果
                    top_user = user_list[0]
                    user_id = top_user.get('user_id')
                    score = top_user.get('score')
                    
                    # 阈值验证，小于80分不可信
                    if score < 80:
                        return Response({'msg': '无法确认身份，请靠近摄像头重试'}, status=status.HTTP_400_BAD_REQUEST)
                    
                    try:
                        user = UserProfile.objects.get(id=user_id)
                        return Response({
                            'msg': '识别成功',
                            'user': {
                                'id': user.id,
                                'username': user.username,
                                'email': user.email,
                                'score': score
                            }
                        })
                    except UserProfile.DoesNotExist:
                        return Response({'msg': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)
                else:
                    return Response({'msg': '未识别到已知用户'}, status=status.HTTP_404_NOT_FOUND)
            else:
                return Response({'msg': f"识别失败: {result.get('error_msg')}"}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'msg': f'识别过程出错: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({'msg': '未知错误'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
