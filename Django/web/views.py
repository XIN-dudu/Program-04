from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status

from web.serializers import UserSerializer
from .models import UserProfile
import random
import smtplib
from email.mime.text import MIMEText
from email.header import Header

# 简单内存验证码存储（生产建议用redis等）
email_code_cache = {}

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
def register(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        # 检查用户名、邮箱、手机号唯一性
        username = serializer.validated_data.get('username')
        email = serializer.validated_data.get('email')
        phone = serializer.validated_data.get('phone')
        if UserProfile.objects.filter(username=username).exists():
            return Response({'msg': '用户名已存在'}, status=status.HTTP_400_BAD_REQUEST)
        if UserProfile.objects.filter(email=email).exists():
            return Response({'msg': '邮箱已存在'}, status=status.HTTP_400_BAD_REQUEST)
        if UserProfile.objects.filter(phone=phone).exists():
            return Response({'msg': '手机号已存在'}, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response({'msg': '注册成功'}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
        from_addr = '2640584193@qq.com'
        password = 'bqnpbsdaifxtebgc'
        to_addr = email
        smtp_server = 'smtp.qq.com'
        msg = MIMEText(f'正在进行登录验证，请勿告诉他人，如非您本人操作不用理会，您的登录验证码是：{code}，5分钟内有效。', 'plain', 'utf-8')
        msg['From'] = from_addr
        msg['To'] = Header("用户", 'utf-8')
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
    
