from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import parser_classes
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from rest_framework.pagination import PageNumberPagination

import datetime
from web.serializers import UserSerializer,LogSerializer
from .models import UserProfile, UserFaceImage, aes_decrypt_image, AES_KEY, SystemLog, AlertEvent, UserAvatar, aes_encrypt_text, aes_decrypt_text, TrajectoryPoint
import random
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import os
import base64
import json
import requests
import time
import io
from PIL import Image, ImageDraw, ImageFont
from django.http import JsonResponse
import string
import pandas as pd
import numpy as np  # 在文件顶部加上
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework import serializers
from django.db import connection
import subprocess

# 简单内存验证码存储（生产建议用redis等）
email_code_cache = {}

# 百度人脸识别API配置
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
        print("获取百度token失败")
        return None
    
    url = f"https://aip.baidubce.com/rest/2.0/face/v3/faceset/user/add?access_token={token}"
    
    # 尝试通过UserFaceImage模型的image字段自动解密读取
    user_face = UserFaceImage.objects.filter(image=image_path).first()
    if user_face:
        file_obj = user_face.image.open()
        decrypted_data = file_obj.read()
        file_obj.close()
    else:
        with open(image_path, 'rb') as f:
            encrypted_data = f.read()
        decrypted_data = aes_decrypt_image(encrypted_data, AES_KEY)
    image_base64 = base64.b64encode(decrypted_data).decode('utf-8')
    
    data = {
        "image": image_base64,
        "image_type": "BASE64",
        "group_id": "user_faces",
        "user_id": str(user_id),
        "user_info": user_info or ""
    }
    
    headers = {'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(data), headers=headers)
    print("百度人脸注册返回：", response.text)  # 新增日志打印
    
    if response.status_code == 200:
        result = response.json()
        if result.get('error_code') == 0:
            return result.get('result', {}).get('face_token')
    return None

# Create your views here.

@api_view(['GET', 'POST'])
def get_data(request):
    """
    获取所有用户数据或新增用户数据。

    GET:
        - 无参数
        - 返回：所有用户信息列表（UserSerializer）
        - 示例返回：
            [
                {
                    "id": 1,
                    "username": "user1",
                    "email": "user1@example.com",
                    ...
                },
                ...
            ]
    POST:
        - 参数：
            - username (string, 必填): 用户名
            - password (string, 必填): 密码
            - email (string, 必填): 邮箱
            - phone (string, 必填): 手机号
            - permission (int, 可选): 权限（0-普通用户，1-维修工）
            - face_images (file[], 必填): 多张人脸图片
        - 返回：状态码 200，或校验失败信息
    """
    if request.method == 'GET':
        user = UserProfile.objects.all()
        serializer = UserSerializer(user, many=True)
        return Response(serializer.data)
    if request.method == 'POST':
        # print("fdawhdjiwajdawj")
        serializer = UserSerializer(data = request.data)
        print(serializer)
        return Response(status=status.HTTP_200_OK)

@api_view(['GET', 'PUT', 'DELETE'])
def user_detail(request, id):
    """
    用户详情接口。

    GET:
        - 参数：id (int, 路径参数, 必填): 用户ID
        - 返回：指定id用户信息（UserSerializer）
    PUT:
        - 参数：同UserSerializer
        - 返回：更新后的用户信息
    DELETE:
        - 参数：id (int, 路径参数, 必填): 用户ID
        - 返回：204，无内容
    """
    try:
        user = UserProfile.objects.get(id = id)
    except UserProfile.DoesNotExist:
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
class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(help_text="用户名")
    password = serializers.CharField(help_text="密码")
    email = serializers.EmailField(help_text="邮箱")
    phone = serializers.CharField(help_text="手机号")
    permission = serializers.IntegerField(required=False, help_text="权限（0-普通用户，1-维修工）")
    face_images = serializers.ListField(child=serializers.ImageField(), help_text="多张人脸图片，至少3张")

@swagger_auto_schema(
    method='post',
    manual_parameters=[
        openapi.Parameter('username', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description='用户名'),
        openapi.Parameter('password', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description='密码'),
        openapi.Parameter('email', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description='邮箱'),
        openapi.Parameter('phone', openapi.IN_FORM, type=openapi.TYPE_STRING, required=True, description='手机号'),
        openapi.Parameter('permission', openapi.IN_FORM, type=openapi.TYPE_INTEGER, required=False, description='权限（0-普通用户，1-维修工）'),
        openapi.Parameter('face_images', openapi.IN_FORM, type=openapi.TYPE_FILE, required=True, description='多张人脸图片，至少3张', multiple=True),
    ],
    responses={201: openapi.Response(
        description="注册成功",
        examples={
            "application/json": {"msg": "注册成功"}
        }
    )}
)
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def register(request):
    """
    用户注册接口。

    POST参数：
        - username (string, 必填): 用户名
        - password (string, 必填): 密码
        - email (string, 必填): 邮箱
        - phone (string, 必填): 手机号
        - permission (int, 可选): 权限（0-普通用户，1-维修工）
        - face_images (file[], 必填): 多张人脸图片，至少3张
    返回：
        - msg (string): 注册结果信息
        - 状态码 201 注册成功，400/500 失败
    """
    # 获取基本用户信息
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email')
    phone = request.data.get('phone')
    permission = request.data.get('permission', 0)  # 默认普通用户
    
    # 检查必填字段
    if not all([username, password, email, phone]):
        return Response({'msg': '用户名、密码、邮箱和手机号不能为空'}, status=status.HTTP_400_BAD_REQUEST)
    
    # 检查权限值是否合法（只允许0-普通用户，1-维修工）
    try:
        permission = int(permission)
        if permission not in [0, 1]:
            return Response({'msg': '无效的用户角色'}, status=status.HTTP_400_BAD_REQUEST)
    except (ValueError, TypeError):
        return Response({'msg': '无效的用户角色'}, status=status.HTTP_400_BAD_REQUEST)
    
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
        password=aes_encrypt_text(password),
        email=aes_encrypt_text(email),
        phone=aes_encrypt_text(phone),
        permission=permission,  # 设置用户权限
        face_image=face_images[0]  # 使用第一张图片作为主头像
    )
    user.save()
    
    # 保存所有人脸图片，只保存有face_token的
    success_faces = []
    for image in face_images:
        user_face = UserFaceImage(user=user, image=image)
        user_face.save()
        image_path = user_face.image.path
        face_token = None
        if all([BAIDU_API_KEY, BAIDU_SECRET_KEY, BAIDU_APP_ID]) and BAIDU_API_KEY != "你的百度云API Key":
            try:
                time.sleep(0.2)
                face_token = add_face_to_baidu(
                    image_path, 
                    user.id, 
                    f"{{'username': '{username}', 'email': '{email}'}}"
                )
            except Exception as e:
                print(f"上传到百度人脸库失败: {e}")
        if face_token:
            user_face.face_token = face_token
            user_face.save()
            success_faces.append(user_face)
        else:
            user_face.delete()  # 删除未同步成功的图片
    # 注册结束后判断
    if not success_faces:
        user.delete()  # 删除用户
        return Response({'msg': '人脸图片未能成功同步到百度云，请重试'}, status=500)
    create_log(request,user,'info', '注册用户', f'用户名: {username}, 邮箱: {email}, 手机: {phone}, 权限: {permission}')
    return Response({'msg': '注册成功'}, status=status.HTTP_201_CREATED)

# 登录接口
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(help_text="用户名")
    password = serializers.CharField(help_text="密码")
    captcha_id = serializers.CharField(required=False, help_text="验证码ID")
    captcha_clicks = serializers.ListField(child=serializers.DictField(), required=False, help_text="验证码点击坐标")

@swagger_auto_schema(
    method='post',
    request_body=LoginSerializer,
    responses={200: openapi.Response(
        description="登录结果",
        examples={
            "application/json": {"msg": "登录成功", "name": "user1", "permission": 0}
        }
    )}
)
@api_view(['POST'])
def login(request):
    """
    用户登录接口。

    POST参数：
        - username (string, 必填): 用户名
        - password (string, 必填): 密码
        - captcha_id (string, 可选): 验证码ID
        - captcha_clicks (list, 可选): 验证码点击坐标
    返回：
        - msg (string): 登录结果
        - name (string): 用户名
        - permission (int): 权限
        - reason (string, 可选): 错误原因
    """
    username = request.data.get('username') or request.data.get('name')
    password = request.data.get('password')
    captcha_id = request.data.get('captcha_id')
    captcha_clicks = request.data.get('captcha_clicks')
    # 验证码校验（如果前端有传）
    if captcha_id and captcha_clicks:
        session_key = 'click_captcha_%s' % captcha_id
        captcha_data = request.session.get(session_key)
        if not captcha_data:
            return Response({'msg': '验证码已过期', 'reason': 'captcha_expired'}, status=status.HTTP_400_BAD_REQUEST)
        targets = captcha_data['targets']
        positions = captcha_data['positions']
        checked = 0
        for i, target in enumerate(targets):
            for pos in positions:
                if pos['word'] == target:
                    x0, y0, w, h = pos['x'], pos['y'], pos['w'], pos['h']
                    x, y = captcha_clicks[i]['x'], captcha_clicks[i]['y']
                    if x0 <= x <= x0 + w and y0 <= y <= y0 + h:
                        checked += 1
                    break
        if checked != 4:
            return Response({'msg': '验证码错误', 'reason': 'captcha_error'}, status=status.HTTP_400_BAD_REQUEST)
    if not username or not password:
        return Response({'msg': '用户名和密码不能为空', 'reason': 'empty'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        user = UserProfile.objects.get(username=username)
        # 支持明文和加密密码
        password_match = False
        if user.password == password:
            password_match = True
        else:
            try:
                if aes_decrypt_text(user.password) == password:
                    password_match = True
            except:
                pass  # 解密失败，继续检查明文
        
        if password_match:
            request.session['username'] = user.username  # 登录成功写入session
            create_log(request,user,'info', '用户登入成功', f'用户名: {username}')
            return Response({'msg': '登录成功', 'name': user.username, 'permission': user.permission}, status=status.HTTP_200_OK)
        else:
            create_log(request,user,'info', '用户登入失败', f'用户名: {username}，密码错误')
            return Response({'msg': '密码错误', 'reason': 'password_error'}, status=status.HTTP_400_BAD_REQUEST)
    except UserProfile.DoesNotExist:
        create_log(request,None,'info', '用户登入失败', f'用户名: {username}，用户不存在')
        return Response({'msg': '用户不存在', 'reason': 'user_not_found'}, status=status.HTTP_400_BAD_REQUEST)

# 发送邮箱验证码接口
class EmailCodeSerializer(serializers.Serializer):
    email = serializers.EmailField(help_text="邮箱")

@swagger_auto_schema(
    method='post',
    request_body=EmailCodeSerializer,
    responses={200: openapi.Response(
        description="发送邮箱验证码",
        examples={
            "application/json": {"msg": "验证码已发送"}
        }
    )}
)
@api_view(['POST'])
def send_email_code(request):
    """
    发送邮箱验证码接口。

    POST参数：
        - email (string, 必填): 邮箱
    返回：
        - msg (string): 发送结果
    """
    email = request.data.get('email')
    if not email:
        return Response({'msg': '邮箱不能为空'}, status=status.HTTP_400_BAD_REQUEST)
    # 新增：先判断邮箱是否已注册
    if not UserProfile.objects.filter(email=email).exists():
        return Response({'msg': '该邮箱未注册'}, status=status.HTTP_400_BAD_REQUEST)
    # 生成6位验证码
    code = str(random.randint(100000, 999999))
    # 发送邮件
    try:
        to_addr = email
        smtp_server = 'smtp.qq.com'
        from_addr = '2640584193@qq.com'  # TODO: 改成你的发件邮箱
        password = 'czryjftofgjrebhi'  # TODO: 改成你的邮箱授权码
        msg = MIMEText(
            f'''<div style="font-size:16px;line-height:2;">
                【智能道路巡检与城市交通大数据平台】<br>
                您正在进行登录操作，本次验证码为：
                <span style="color:#1976d2;font-size:22px;font-weight:bold;">{code}</span><br>
                验证码有效期为5分钟，请勿泄露给他人。<br>
                如非本人操作，请及时忽略本邮件并注意账号安全。
            </div>''',
            'html', 'utf-8')
        from email.utils import formataddr
        msg['From'] = formataddr(("智能道路平台验证码", from_addr))
        msg['To'] = Header(to_addr, 'utf-8')
        msg['Subject'] = Header("智能道路平台登录验证码", 'utf-8')
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
class EmailLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(help_text="邮箱")
    code = serializers.CharField(help_text="邮箱验证码")

@swagger_auto_schema(
    method='post',
    request_body=EmailLoginSerializer,
    responses={200: openapi.Response(
        description="邮箱验证码登录",
        examples={
            "application/json": {"msg": "登录成功", "name": "user1", "permission": 0}
        }
    )}
)
@api_view(['POST'])
def email_login(request):
    """
    邮箱验证码登录接口。

    POST参数：
        - email (string, 必填): 邮箱
        - code (string, 必填): 邮箱验证码
    返回：
        - msg (string): 登录结果
        - name (string): 用户名
        - permission (int): 权限
    """
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
        # 支持加密邮箱
        user = None
        for u in UserProfile.objects.all():
            if u.email == email:
                user = u
                break
            else:
                try:
                    if aes_decrypt_text(u.email) == email:
                        user = u
                        break
                except:
                    pass  # 解密失败，继续检查下一个用户
        if not user:
            return Response({'msg': '用户不存在'}, status=status.HTTP_400_BAD_REQUEST)
        request.session['username'] = user.username  # 邮箱登录成功写入session
        return Response({'msg': '登录成功', 'name': user.username, 'permission': user.permission}, status=status.HTTP_200_OK)
    except UserProfile.DoesNotExist:
        return Response({'msg': '用户不存在'}, status=status.HTTP_400_BAD_REQUEST)
    
# 人脸识别接口
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def face_recognition(request):
    """
    人脸识别登录接口。

    POST参数：
        - username (string, 必填): 用户名
        - image (file, 必填): 现场图片
    返回：
        - msg (string): 识别结果
        - user (object): 用户信息（含id, username, email, score）
    """
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
                        # 尝试解密邮箱，如果失败则返回原值
                        try:
                            email = aes_decrypt_text(user.email)
                        except:
                            email = user.email
                        return Response({
                            'msg': '识别成功',
                            'user': {
                                'id': user.id,
                                'username': user.username,
                                'email': email,
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

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def liveness_detection(request):
    """
    活体检测接口。

    POST参数：
        - username (string, 必填): 用户名
        - image (file, 必填): 现场图片
    返回：
        - msg (string): 检测结果
        - user (object): 用户信息
        - score (float): 置信分数
        - liveness (float/bool): 活体检测分数/结果
    """
    """活体检测+1对N识别接口，接收图片，调用百度V3接口"""
    if 'image' not in request.FILES:
        return Response({'msg': '请上传图片'}, status=status.HTTP_400_BAD_REQUEST)
    image = request.FILES['image']
    import base64
    image_base64 = base64.b64encode(image.read()).decode('utf-8')
    token = get_baidu_token()
    if not token:
        return Response({'msg': '服务暂不可用'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    url = f"https://aip.baidubce.com/rest/2.0/face/v3/search?access_token={token}"
    data = {
        "image": image_base64,
        "image_type": "BASE64",
        "group_id_list": "user_faces",  # 你的百度人脸库分组ID
        "liveness_control": "NORMAL",   # 要求做活体检测
        "quality_control": "NORMAL"
    }
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(url, data=json.dumps(data), headers=headers)
        result = response.json()
        if result.get('error_code') == 0:
            user_list = result.get('result', {}).get('user_list', [])
            liveness = result.get('result', {}).get('face_liveness', None)
            if user_list and len(user_list) > 0:
                top_user = user_list[0]
                baidu_user_id = top_user.get('user_id')
                score = top_user.get('score')
                # 通过face_id查本地用户名
                try:
                    user = UserProfile.objects.get(face_id=baidu_user_id)
                    username = user.username
                except UserProfile.DoesNotExist:
                    username = None
                return Response({
                    'msg': '识别成功',
                    'user': {
                        'username': username,
                        'baidu_user_id': baidu_user_id
                    },
                    'score': score,
                    'liveness': liveness
                })
            else:
                return Response({'msg': '未识别到已知用户', 'liveness': liveness})
        else:
            return Response({'msg': f"识别失败: {result.get('error_msg')}", 'liveness': False})
    except Exception as e:
        return Response({'msg': f'检测过程出错: {str(e)}', 'liveness': False})

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def liveness_check(request):
    """
    活体检测二次接口。

    POST参数：
        - username (string, 必填): 用户名
        - video (file, 必填): 现场视频
    返回：
        - liveness (bool): 是否通过
        - msg (string): 检测结果说明
        - raw (object): 原始返回内容
    """
    """活体检测接口，接收视频，调用百度H5 API"""
    if 'video' not in request.FILES:
        return Response({'msg': '请上传视频', 'raw': None}, status=status.HTTP_400_BAD_REQUEST)
    video = request.FILES['video']
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp:
        temp_path = temp.name
        for chunk in video.chunks():
            temp.write(chunk)
    # 读取视频内容并转base64
    with open(temp_path, 'rb') as f:
        video_base64 = base64.b64encode(f.read()).decode('utf-8')
    token = get_baidu_token()
    if not token:
        os.unlink(temp_path)
        return Response({'msg': '活体检测服务暂不可用', 'raw': None}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    url = f"https://aip.baidubce.com/rest/2.0/face/v1/faceliveness/verify?access_token={token}"
    data = {
        "video_base64": video_base64
    }
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(url, data=json.dumps(data), headers=headers)
        os.unlink(temp_path)
        try:
            result = response.json()
        except Exception as e:
            return Response({'liveness': False, 'msg': f'API返回内容无法解析为JSON: {str(e)}', 'raw': response.text})
        if not isinstance(result, dict):
            return Response({'liveness': False, 'msg': 'API返回内容不是字典', 'raw': str(result)})
        if result.get('error_code') == 0 and result.get('result', {}).get('score', 0) > 0.8:
            return Response({'liveness': True, 'msg': '活体检测通过', 'raw': result})
        else:
            score = result.get('result', {}).get('score', 0) if result.get('result') else 0
            return Response({'liveness': False, 'msg': f"活体检测未通过，分数：{score:.2f}", 'raw': result})
    except Exception as e:
        return Response({'liveness': False, 'msg': f'检测过程出错: {str(e)}', 'raw': None})

@api_view(['GET'])
def click_captcha(request):
    """
    获取点击验证码图片和内容。
    GET: 返回验证码图片和内容。
    """
    """生成文字验证码"""
    # 生成6个随机汉字
    hanzi_list = list('的一是在不了有和人这中大为上个国我以要他时来用们生到作地于出就分对成会可主发年动同工也能下过子说产种面而方后多定行学法所民得经十三之进着等部度家电力里如水化高自二理起小物现实加量都两体制机当使点从业本去把性好应开它合还因由其些然前外天政四日那社义事平形相全表间样与关各重新线内数正心反你明看原又么利比或但质气第向道命此变条只没结解问意建月公无系军很情者最立代想已通并提直题党程展五果料象员革位入常文总次品式活设及管特件长求老头基资边流路级少图山统接知较将组见计别她手角期根论运农指几九区强放决西被干做必战先回则任取据处队南给色光门即保治北造百规热领七海口东导器压志世金增争济阶油思术极交受联什认六共权收证改清己美再采转单风切打白教速花带安场身车例真务具万每目至达走积示议声报斗完类八离华名确才科张信马节话米整空元况今集温传土许步群广石记需段研界拉林律叫且究观越织装影算低持音众书布复容儿须际商非验连断深难近矿千周委素技备半办青省列习便响约支般史感劳便团往酸历市克何除消构府称太准精值号率族维划选标写存候毛亲快效斯院查江型眼王按格养易置派层片始却专状育厂京识适属圆包火住调满县局照参红细引听该铁价严龙飞'
    )
    hanzi = random.sample(hanzi_list, 6)
    target_hanzi = random.sample(hanzi, 4)

    # 生成图片
    width, height = 320, 100
    image = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    font_path = os.path.join(os.path.dirname(__file__), 'STXINWEI.TTF')
    font = ImageFont.truetype(font_path, 36)
    positions = []
    # --- 增加干扰线 ---
    for _ in range(8):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        color = tuple(random.randint(100, 200) for _ in range(3))
        draw.line([(x1, y1), (x2, y2)], fill=color, width=2)
    # --- 增加噪点 ---
    for _ in range(300):
        x = random.randint(0, width-1)
        y = random.randint(0, height-1)
        color = tuple(random.randint(0, 255) for _ in range(3))
        image.putpixel((x, y), color)
    # --- 绘制扭曲/错位的文字 ---
    for i, word in enumerate(hanzi):
        x = 30 + i * 45 + random.randint(-5, 5)
        y = 30 + random.randint(-10, 10)
        angle = random.randint(-30, 30)
        # 生成单字图片
        char_img = Image.new('RGBA', (40, 50), (255, 255, 255, 0))
        char_draw = ImageDraw.Draw(char_img)
        char_draw.text((2, 2), word, font=font, fill=(0, 0, 0))
        char_img = char_img.rotate(angle, resample=Image.BICUBIC, expand=1)
        image.paste(char_img, (x, y), char_img)
        positions.append({'word': word, 'x': x, 'y': y, 'w': 36, 'h': 36})
    # 编码图片
    buf = io.BytesIO()
    image.save(buf, format='PNG')
    img_base64 = base64.b64encode(buf.getvalue()).decode()

    # 生成验证码ID
    captcha_id = str(int(time.time() * 1000)) + str(random.randint(1000, 9999))
    # 保存到session
    request.session['click_captcha_%s' % captcha_id] = {
        'targets': target_hanzi,
        'positions': positions,
        'timestamp': time.time()
    }
    request.session.modified = True

    return JsonResponse({
        'captcha_id': captcha_id,
        'image': img_base64,
        'targets': target_hanzi
    })


@api_view(['POST'])
def click_captcha_verify(request):
    """
    检查验证码有效性。
    POST参数：captcha_id, captcha_clicks
    返回：校验结果。
    """
    """检查验证码有效性"""
    captcha_id = request.data.get('captcha_id')
    clicks = request.data.get('clicks')  # [{x: , y: }, ...]
    if not captcha_id or not clicks or len(clicks) != 4:
        return Response({'msg': '参数错误', 'reason': 'param_error'}, status=400)
    session_key = 'click_captcha_%s' % captcha_id
    captcha_data = request.session.get(session_key)
    if not captcha_data:
        return Response({'msg': '验证码已过期', 'reason': 'captcha_expired'}, status=400)
    targets = captcha_data['targets']
    positions = captcha_data['positions']
    checked = 0
    for i, target in enumerate(targets):
        for pos in positions:
            if pos['word'] == target:
                x0, y0, w, h = pos['x'], pos['y'], pos['w'], pos['h']
                x, y = clicks[i]['x'], clicks[i]['y']
                if x0 <= x <= x0 + w and y0 <= y <= y0 + h:
                    checked += 1
                break
    if checked == 4:
        return Response({'msg': 'success'})
    else:
        return Response({'msg': '验证码错误', 'reason': 'captcha_error'}, status=400)

@api_view(['POST'])
def update_profile(request):
    """
    用户信息修改接口。

    POST参数：
        - username (string, 必填): 用户名
        - new_username (string, 可选): 新用户名
        - email (string, 可选): 新邮箱
        - password (string, 可选): 新密码
        - email_code (string, 可选): 邮箱验证码
    返回：
        - msg (string): 修改结果
    """
    username = request.data.get('username')
    new_email = request.data.get('email')
    new_password = request.data.get('password')
    email_code = request.data.get('email_code')
    new_username = request.data.get('new_username')  # 新增用户名修改字段
    new_phone = request.data.get('phone') # 新增手机号修改字段
    if not username:
        return Response({'msg': '用户名不能为空'}, status=400)
    try:
        user = UserProfile.objects.get(username=username)
        updated = False
        # 用户名修改（唯一性校验）
        if new_username and new_username != user.username:
            if UserProfile.objects.filter(username=new_username).exists():
                return Response({'msg': '新用户名已存在'}, status=400)
            old_username = user.username
            user.username = new_username
            updated = True
            # 同步人脸库face_id（如有）
            if user.face_id:
                user.face_id = user.face_id.replace(str(old_username), str(new_username))
        # 邮箱更改需要验证码校验
        try:
            current_email = aes_decrypt_text(user.email)
        except:
            current_email = user.email
        if new_email and new_email != current_email:
            if not email_code:
                return Response({'msg': '请输入邮箱验证码'}, status=400)
            real_code = email_code_cache.get(new_email)
            if not real_code:
                return Response({'msg': '请先获取验证码'}, status=400)
            if email_code != real_code:
                return Response({'msg': '验证码错误'}, status=400)
            # 检查邮箱唯一性
            if UserProfile.objects.filter(email=aes_encrypt_text(new_email)).exclude(username=user.username).exists():
                return Response({'msg': '该邮箱已被其他用户占用'}, status=400)
            user.email = aes_encrypt_text(new_email)
            updated = True
        # 手机号修改（无需验证码）
        if new_phone and new_phone != user.phone:
            # 可选：唯一性校验
            if UserProfile.objects.filter(phone=new_phone).exclude(username=user.username).exists():
                return Response({'msg': '该手机号已被其他用户占用'}, status=400)
            user.phone = new_phone
            updated = True
        if new_password:
            user.password = aes_encrypt_text(new_password)
            updated = True
        if updated:
            user.save()
            return Response({'msg': '信息修改成功'})
        else:
            return Response({'msg': '没有需要修改的信息'}, status=200)
    except UserProfile.DoesNotExist:
        return Response({'msg': '用户不存在'}, status=404)
    
class CheckEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(help_text="邮箱")
    username = serializers.CharField(required=False, help_text="用户名（可选）")

@swagger_auto_schema(
    method='post',
    request_body=CheckEmailSerializer,
    responses={200: openapi.Response(
        description="邮箱可用性",
        examples={
            "application/json": {"available": True, "msg": "邮箱可用"}
        }
    )}
)
@api_view(['POST'])
def check_email_available(request):
    """
    检查邮箱是否可用接口。

    POST参数：
        - email (string, 必填): 邮箱
        - username (string, 可选): 用户名
    返回：
        - available (bool): 邮箱是否可用
        - msg (string): 结果说明
    """
    """邮箱有效性校验"""
    email = request.data.get('email')
    username = request.data.get('username')
    if not email:
        return Response({'available': False, 'msg': '邮箱不能为空'}, status=400)
    # 只要不是当前用户自己的邮箱且已被其他用户绑定就不可用
    for u in UserProfile.objects.all():
        email_match = False
        if u.email == email:
            email_match = True
        else:
            try:
                if aes_decrypt_text(u.email) == email:
                    email_match = True
            except:
                pass
        if email_match and u.username != username:
            return Response({'available': False, 'msg': '该邮箱已被其他用户绑定'}, status=200)
    return Response({'available': True, 'msg': '邮箱可用'}, status=200)

@api_view(['GET'])
@csrf_exempt
def user_list(request):
    """
    获取所有用户列表（管理员权限）。

    GET参数：
        - username (string, 可选): 用户名（用于权限校验）
    返回：
        - users (list): 用户信息列表（含id, username, email, permission）
    """
    username = request.GET.get('username') or request.session.get('username')
    try:
        user = UserProfile.objects.get(username=username)
        if user.permission != 2:
            return JsonResponse({'msg': '无权限'}, status=403)
    except UserProfile.DoesNotExist:
        return JsonResponse({'msg': '用户不存在'}, status=404)
    users = UserProfile.objects.all()
    data = []
    for user in users:
        try:
            email = aes_decrypt_text(user.email)
        except:
            email = user.email
        data.append({
            'id': user.id,
            'username': user.username,
            'email': email,
            'permission': user.permission
        })
    return JsonResponse({'users': data})

@api_view(['POST'])
@csrf_exempt
def delete_user(request):
    """
    删除用户接口（管理员权限）。

    POST参数：
        - username (string, 必填): 管理员用户名
        - user_id (int, 必填): 目标用户ID
    返回：
        - msg (string): 删除结果
    """
    username = request.data.get('username') or request.session.get('username')
    try:
        user = UserProfile.objects.get(username=username)
        if user.permission != 2:
            return JsonResponse({'msg': '无权限'}, status=403)
    except UserProfile.DoesNotExist:
        return JsonResponse({'msg': '用户不存在'}, status=404)
    user_id = request.data.get('user_id')
    try:
        del_user = UserProfile.objects.get(id=user_id)
        # 先删除百度云人脸库信息
        token = get_baidu_token()
        if token:
            url = f"https://aip.baidubce.com/rest/2.0/face/v3/faceset/user/delete?access_token={token}"
            data = {
                "group_id": "user_faces",
                "user_id": str(del_user.id)
            }
            headers = {'Content-Type': 'application/json'}
            try:
                resp = requests.post(url, data=json.dumps(data), headers=headers)
                print("百度人脸库删除返回：", resp.text)
            except Exception as e:
                print(f"调用百度云删除用户失败: {e}")
        # 本地删除用户及人脸记录
        del_user.delete()  # 级联删除UserFaceImage
        return JsonResponse({'msg': '用户及人脸记录已删除（含百度云）'})
    except UserProfile.DoesNotExist:
        return JsonResponse({'msg': '用户不存在'}, status=404)
    except Exception as e:
        return JsonResponse({'msg': f'删除失败: {str(e)}'}, status=500)
    
@api_view(['POST'])
@csrf_exempt
def update_permission(request):
    """
    修改用户权限接口（管理员权限）。

    POST参数：
        - username (string, 必填): 管理员用户名
        - user_id (int, 必填): 目标用户ID
        - permission (int, 必填): 新权限值
    返回：
        - msg (string): 修改结果
    """
    username = request.data.get('username') or request.session.get('username')
    try:
        user = UserProfile.objects.get(username=username)
        if user.permission != 2:
            return JsonResponse({'msg': '无权限'}, status=403)
    except UserProfile.DoesNotExist:
        return JsonResponse({'msg': '用户不存在'}, status=404)
    user_id = request.data.get('user_id')
    permission = request.data.get('permission')
    try:
        target_user = UserProfile.objects.get(id=user_id)
        target_user.permission = int(permission)
        target_user.save()
        return JsonResponse({'msg': '权限修改成功'})
    except UserProfile.DoesNotExist:
        return JsonResponse({'msg': '用户不存在'}, status=404)
    except Exception as e:
        return JsonResponse({'msg': f'修改失败: {str(e)}'}, status=500)

@api_view(['GET'])
def points_api(request):
    start = request.GET.get('start')
    end = request.GET.get('end')
    car = request.GET.get('car')
    limit = int(request.GET.get('limit', 200))
    table = 'jn0912_baidu_coords'

    sql = f"SELECT LAT, LON, UTC, COMMADDR, HEAD, TFLAG, status, SPEED FROM {table} WHERE 1=1"
    params = []
    if start:
        sql += " AND UTC >= %s"
        params.append(start)
    if end:
        sql += " AND UTC <= %s"
        params.append(end)
    if car:
        sql += " AND COMMADDR = %s"
        params.append(car)
    sql += " ORDER BY UTC LIMIT %s"
    params.append(limit)

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        rows = cursor.fetchall()

    data = [
        {
            'lat': row[0],
            'lon': row[1],
            'time': row[2],
            'car': row[3],
            'head': row[4],
            'tflag': row[5],
            'status': row[6],
            'speed': row[7]
        }
        for row in rows
    ]
    return Response(data)
    
@api_view(['POST'])
def face_verify_one_to_one(request):
    """
    1:1人脸比对接口。

    POST参数：
        - username (string, 必填): 用户名
        - image (file, 必填): 现场图片
    返回：
        - msg (string): 比对结果
        - score (float): 相似度分数
    """
    """1:1人脸比对接口：当前用户主头像face_token vs 现场图片base64"""
    username = request.data.get('username') or request.session.get('username')
    if not username:
        return Response({'msg': '未登录，无法比对'}, status=401)
    try:
        user = UserProfile.objects.get(username=username)
    except UserProfile.DoesNotExist:
        return Response({'msg': '用户不存在'}, status=404)
    # 获取主头像face_token
    main_face = user.face_images.first()  # 取第一张人脸图片
    if not main_face or not main_face.face_token:
        return Response({'msg': '用户主头像未同步到百度云或未注册face_token'}, status=400)
    if 'image' not in request.FILES:
        return Response({'msg': '请上传现场图片'}, status=400)
    img2 = request.FILES['image']
    img2_base64 = base64.b64encode(img2.read()).decode()
    # 用face_token和base64做比对
    url = f"https://aip.baidubce.com/rest/2.0/face/v3/match?access_token={get_baidu_token()}"
    headers = {'Content-Type': 'application/json'}
    data = [
        {"image": main_face.face_token, "image_type": "FACE_TOKEN", "face_type": "LIVE", "quality_control": "LOW", "liveness_control": "NORMAL"},
        {"image": img2_base64, "image_type": "BASE64", "face_type": "LIVE", "quality_control": "LOW", "liveness_control": "NORMAL"}
    ]
    try:
        resp = requests.post(url, data=json.dumps(data), headers=headers)
        result = resp.json()
        if result.get('error_code') == 0:
            score = result['result']['score']
            passed = score >= 80
            return Response({'msg': '比对成功', 'score': score, 'passed': passed})
        else:
            return Response({'msg': f"比对失败: {result.get('error_msg')}", 'raw': result}, status=400)
    except Exception as e:
        return Response({'msg': f'比对过程出错: {str(e)}'}, status=500)
    
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_avatar(request):
    """
    用户头像上传接口。
    """
    import sys
    print("[upload_avatar] 接口被调用", file=sys.stderr)
    username = request.data.get('username')
    print(f"[upload_avatar] username: {username}", file=sys.stderr)
    if not username:
        print("[upload_avatar] 用户名不能为空", file=sys.stderr)
        return Response({'msg': '用户名不能为空'}, status=400)
    try:
        user = UserProfile.objects.get(username=username)
        print(f"[upload_avatar] user对象: {user}", file=sys.stderr)
        avatar = request.FILES.get('avatar')
        print(f"[upload_avatar] avatar: {avatar}", file=sys.stderr)
        if not avatar:
            print("[upload_avatar] 没有上传头像文件", file=sys.stderr)
            return Response({'msg': '请上传头像文件'}, status=400)
        avatar_data = avatar.read()
        print(f"[upload_avatar] avatar_data长度: {len(avatar_data) if avatar_data else 0}", file=sys.stderr)
        if not avatar_data:
            print("[upload_avatar] 头像文件为空或读取失败", file=sys.stderr)
            return Response({'msg': '头像文件为空或读取失败'}, status=400)
        file_size = len(avatar_data)
        print(f"[upload_avatar] file_size: {file_size}", file=sys.stderr)
        if file_size <= 0:
            print("[upload_avatar] 头像文件大小异常", file=sys.stderr)
            return Response({'msg': '头像文件大小异常'}, status=400)
        if file_size > 5 * 1024 * 1024:
            print("[upload_avatar] 头像文件过大", file=sys.stderr)
            return Response({'msg': '头像文件过大，请选择小于5MB的图片'}, status=400)
        file_name = avatar.name or f'avatar_{user.username}.jpg'
        content_type = avatar.content_type or 'image/jpeg'
        print(f"[upload_avatar] file_name: {file_name}, content_type: {content_type}", file=sys.stderr)
        try:
            user_avatar, created = UserAvatar.objects.get_or_create(user=user)
            user_avatar.avatar_data = avatar_data
            user_avatar.file_name = file_name
            user_avatar.content_type = content_type
            user_avatar.file_size = file_size
            user_avatar.save()
            print(f"[upload_avatar] 头像保存成功, created={created}", file=sys.stderr)
        except Exception as e:
            print(f"[upload_avatar] 保存头像失败: {str(e)}", file=sys.stderr)
            return Response({'msg': f'保存头像失败: {str(e)}'}, status=500)
        avatar_url = f'/api/avatar/{user.username}/'
        print(f"[upload_avatar] 返回avatar_url: {avatar_url}", file=sys.stderr)
        return Response({
            'msg': '头像上传成功（数据库存储）', 
            'avatar_url': avatar_url
        })
    except UserProfile.DoesNotExist:
        print("[upload_avatar] 用户不存在", file=sys.stderr)
        return Response({'msg': '用户不存在'}, status=404)
    except Exception as e:
        print(f"[upload_avatar] 其他异常: {str(e)}", file=sys.stderr)
        return Response({'msg': f'未知错误: {str(e)}'}, status=500)

# 工具函数：获取客户端IP

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip or '未知'

def create_log(request,user, level, action, details):
    """创建新日志条目"""
    
    # 自动获取客户端IP
    ip = get_client_ip(request)
    
    log = SystemLog(
        user=user,
        level=level,
        action=action,
        details=details,
        ip_address=ip,
        timestamp=timezone.now()
    )
    # if log.is_valid():
    log.save()
        # return Response(log.data, status=status.HTTP_201_CREATED)
    # return Response(log.errors, status=status.HTTP_400_BAD_REQUEST)
    # serializer = LogSerializer(data={'user_id': user_id, 'level': level, 'action': action, 'details': details, 'ip_address': ip,'tiemestamp': timezone.now()})
    # if serializer.is_valid():
    #     serializer.save()
    #     # return Response(serializer.data, status=status.HTTP_201_CREATED)
    # # return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
   
@api_view(['GET'])
def log_list(request):
    # 获取查询参数
    level = request.query_params.get('level')
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    username = request.query_params.get('username')
    # 初始化查询集
    logs = SystemLog.objects.all().select_related('user')

    # 根据参数过滤
    if username:
        logs = logs.filter(user__username=username)
    if level:
        logs = logs.filter(level=level)

    if start_date:
        try:
            start = timezone.make_aware(datetime.datetime.strptime(start_date, "%Y-%m-%d"))
            logs = logs.filter(timestamp__gte=start)
        except ValueError:
            return Response({"error": "无效的开始日期格式，请使用 YYYY-MM-DD"}, status=400)

    if end_date:
        try:
            end = timezone.make_aware(datetime.datetime.strptime(end_date, "%Y-%m-%d"))
            logs = logs.filter(timestamp__lte=end)
        except ValueError:
            return Response({"error": "无效的结束日期格式，请使用 YYYY-MM-DD"}, status=400)

    # 分页处理
    paginator = StandardResultsSetPagination()
    page = paginator.paginate_queryset(logs, request)

    # 序列化
    serializer = LogSerializer(page, many=True)

    # 返回分页响应
    # return paginator.get_paginated_response(serializer.data)
    return Response({
        'results': serializer.data,
        'current_page': paginator.page.number,
        'page_size': paginator.page.paginator.per_page,
        'total': paginator.page.paginator.count
    })

@api_view(['GET'])
def current_user_profile(request):
    """
    获取当前登录用户信息。

    GET参数：
        - username (string, 可选): 用户名（用于session或GET）
    返回：
        - username (string): 用户名
        - email (string): 邮箱
        - phone (string): 手机号
        - permission (int): 权限
        - avatar_url (string): 头像URL
    """
    username = request.session.get('username') or request.GET.get('username')
    if not username:
        return Response({'msg': '未登录'}, status=401)
    try:
        user = UserProfile.objects.get(username=username)
        # 尝试解密，如果失败则返回原值（兼容明文存储）
        try:
            email = aes_decrypt_text(user.email)
        except:
            email = user.email
        try:
            phone = aes_decrypt_text(user.phone)
        except:
            phone = user.phone
        # 优先返回数据库存储的头像URL，如果没有则返回本地头像URL
        avatar_url = None
        try:
            user_avatar = UserAvatar.objects.get(user=user)
            avatar_url = f'/api/avatar/{user.username}/'
        except UserAvatar.DoesNotExist:
            if user.avatar:
                avatar_url = user.avatar.url
        
        data = {
            'username': user.username,
            'email': email,
            'phone': phone,
            'permission': user.permission,
            'avatar_url': avatar_url
        }
        return Response(data)
    except UserProfile.DoesNotExist:
        return Response({'msg': '用户不存在'}, status=404)

@api_view(['GET'])
def get_avatar(request, username):
    """
    获取用户头像接口。
    GET参数：
        - username (string, 路径参数, 必填): 用户名
    返回：
        - 头像图片文件
    """
    from django.http import HttpResponse, FileResponse
    import os
    try:
        user = UserProfile.objects.get(username=username)
        try:
            user_avatar = UserAvatar.objects.get(user=user)
            # 返回数据库头像
            response = HttpResponse(user_avatar.avatar_data, content_type=user_avatar.content_type)
            response['Content-Disposition'] = f'inline; filename="{user_avatar.file_name}"'
            return response
        except UserAvatar.DoesNotExist:
            # 返回默认头像
            default_path = os.path.join(os.path.dirname(__file__), '../web/assets/default-avatar.png')
            if os.path.exists(default_path):
                return FileResponse(open(default_path, 'rb'), content_type='image/png')
            else:
                return HttpResponse('头像不存在', status=404)
    except UserProfile.DoesNotExist:
        return HttpResponse('用户不存在', status=404)

# ====== 以下为迁移自原 web/views.py 的活体检测与人脸验证接口 ======
from rest_framework.decorators import parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view
import cv2
import tempfile
from django.utils import timezone
from .models import AlertEvent, SystemLog, UserProfile
from django.http import JsonResponse

@api_view(['GET'])
def car_list(request):
    """
    支持分页和模糊搜索的车牌号列表
    """
    table = 'jn0912_baidu_coords'
    search = request.GET.get('search', '')
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    offset = (page - 1) * page_size

    sql = f"SELECT DISTINCT COMMADDR FROM {table} WHERE 1=1"
    params = []
    if search:
        sql += " AND COMMADDR LIKE %s"
        params.append(f"%{search}%")
    sql += " LIMIT %s OFFSET %s"
    params.extend([page_size, offset])

    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        rows = cursor.fetchall()

    # 统计总数
    count_sql = f"SELECT COUNT(DISTINCT COMMADDR) FROM {table} WHERE 1=1"
    count_params = []
    if search:
        count_sql += " AND COMMADDR LIKE %s"
        count_params.append(f"%{search}%")
    with connection.cursor() as cursor:
        cursor.execute(count_sql, count_params)
        total = cursor.fetchone()[0]

    cars = [row[0] for row in rows]
    return JsonResponse({'results': cars, 'count': total})

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def liveness_and_face_verify(request):
    username = request.data.get('user_id') or request.POST.get('user_id')
    video_file = request.FILES.get('video')
    frames = [file for key, file in request.FILES.items() if key.startswith('frame')]
    if not video_file or not username or not frames:
        return JsonResponse({'success': False, 'msg': '缺少参数', 'fail_type': 'param_error'}, status=400)
    try:
        user = UserProfile.objects.get(username=username)
    except UserProfile.DoesNotExist:
        return JsonResponse({'success': False, 'msg': '用户不存在', 'fail_type': 'user_not_found'}, status=400)
    try:
        # 1. 活体检测（直接转发视频给百度API）
        liveness_pass, api_raw = call_baidu_liveness_api_file(video_file, username=user.username, return_raw=True)
        # 判断特殊失败类型
        if not liveness_pass:
            msg = api_raw.get('msg') or api_raw.get('error_msg') or '活体检测未通过'
            # 视频时长过短
            if '时长' in msg or '过短' in msg:
                SystemLog.objects.create(user=user, action='活体检测失败', level='error', details=f'视频时长过短，原因：{msg}', ip_address=get_client_ip(request))
                return JsonResponse({'success': False, 'msg': msg, 'fail_type': 'short_video'})
            # 网络异常
            if '网络' in msg or 'API请求异常' in msg:
                SystemLog.objects.create(user=user, action='活体检测失败', level='error', details=f'网络异常，原因：{msg}', ip_address=get_client_ip(request))
                return JsonResponse({'success': False, 'msg': msg, 'fail_type': 'network_error'})
            # 其它情况视为入侵
            alert = AlertEvent.objects.create(user=user, alert_time=timezone.now(), alert_type='活体检测失败', status='fail', related_data=api_raw, video=video_file)
            log = SystemLog.objects.create(user=user, action='活体检测失败', level='warning', details=f'活体检测未通过，原因：{msg}', alert_event=alert, ip_address=get_client_ip(request))
            return JsonResponse({'success': False, 'msg': msg, 'fail_type': 'intrusion'})
        # 2. 人脸识别（用上传的帧图片）
        verify_success = False
        for img in frames:
            if call_face_verify_api(img.read(), user.username):
                verify_success = True
                break
        if verify_success:
            SystemLog.objects.create(user=user, action='人脸识别通过', level='info', details='人脸识别通过', ip_address=get_client_ip(request))
            return JsonResponse({'success': True, 'msg': '验证通过'})
        else:
            # 人脸识别未通过，视为入侵
            alert = AlertEvent.objects.create(user=user, alert_time=timezone.now(), alert_type='人脸识别失败', status='fail', related_data={}, video=video_file)
            log = SystemLog.objects.create(user=user, action='人脸识别失败', level='warning', details='人脸识别未通过，所有帧均未通过比对', alert_event=alert, ip_address=get_client_ip(request))
            return JsonResponse({'success': False, 'msg': '人脸识别未通过', 'fail_type': 'intrusion'})
    except Exception as e:
        SystemLog.objects.create(user=user, action='活体检测异常', level='error', details=f'后端异常: {str(e)}', ip_address=get_client_ip(request))
        return JsonResponse({'success': False, 'msg': f'后端异常: {str(e)}', 'fail_type': 'backend_error'}, status=500)

def extract_frames(video_path, num_frames=3):
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    step = max(1, total_frames // num_frames)
    frames = []
    for i in range(num_frames):
        cap.set(cv2.CAP_PROP_POS_FRAMES, i * step)
        ret, frame = cap.read()
        if ret:
            _, img_encoded = cv2.imencode('.jpg', frame)
            frames.append(img_encoded.tobytes())
    cap.release()
    return frames

def call_baidu_liveness_api_file(video_file, username=None, return_raw=False):
    import requests
    from django.conf import settings
    url = getattr(settings, 'SELF_BASE_URL', 'http://localhost:8000') + '/api/liveness_check/'
    data = {'username': username}
    files = {'video': (video_file.name, video_file, video_file.content_type)}
    try:
        resp = requests.post(url, data=data, files=files, timeout=20)
        result = resp.json()
        liveness = result.get('liveness', False)
        if return_raw:
            return liveness, result
        return liveness
    except Exception as e:
        if return_raw:
            return False, {'msg': f'API请求异常: {str(e)}'}
        return False

def call_face_verify_api(img_bytes, username):
    from django.test import RequestFactory
    from .views import face_verify_one_to_one
    from django.core.files.uploadedfile import SimpleUploadedFile
    factory = RequestFactory()
    image_file = SimpleUploadedFile('frame.jpg', img_bytes, content_type='image/jpeg')
    data = {'username': username}
    files = {'image': image_file}
    request = factory.post('/api/face_verify_one_to_one/', data, files=files)
    request.FILES['image'] = image_file
    response = face_verify_one_to_one(request)
    if hasattr(response, 'data'):
        return response.data.get('passed', False)
    return False