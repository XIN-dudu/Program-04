from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import parser_classes
from django.views.decorators.csrf import csrf_exempt

from web.serializers import UserSerializer
from .models import UserProfile, UserFaceImage, aes_decrypt_image, AES_KEY
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
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def register(request):
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
        password=password,
        email=email,
        phone=phone,
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
<<<<<<< Updated upstream
=======
                time.sleep(0.2)
>>>>>>> Stashed changes
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
            return Response({'msg': '登录成功', 'name': user.username, 'permission': user.permission}, status=status.HTTP_200_OK)
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
    # 允许任意邮箱发送验证码，不校验是否注册
    # 生成6位验证码
    code = str(random.randint(100000, 999999))
    # 发送邮件
    try:
        to_addr = email
        smtp_server = 'smtp.qq.com'
        from_addr = '2640584193@qq.com'  # TODO: 改成你的发件邮箱
        password = 'czryjftofgjrebhi'  # TODO: 改成你的邮箱授权码
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
        return Response({'msg': '登录成功', 'name': user.username, 'permission': user.permission}, status=status.HTTP_200_OK)
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

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def liveness_detection(request):
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
    captcha_id = request.data.get('captcha_id')
    clicks = request.data.get('clicks')  # [{x: , y: }, ...]
    if not captcha_id or not clicks or len(clicks) != 4:
        return Response({'msg': '参数错误'}, status=400)
    session_key = 'click_captcha_%s' % captcha_id
    captcha_data = request.session.get(session_key)
    if not captcha_data:
        return Response({'msg': '验证码已过期'}, status=400)
    targets = captcha_data['targets']
    positions = captcha_data['positions']
    # 依次校验点击是否落在目标汉字区域
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
        return Response({'msg': 'fail'}, status=400)

@api_view(['POST'])
def update_profile(request):
    username = request.data.get('username')
    new_email = request.data.get('email')
    new_password = request.data.get('password')
    email_code = request.data.get('email_code')
    if not username:
        return Response({'msg': '用户名不能为空'}, status=400)
    try:
        user = UserProfile.objects.get(username=username)
        updated = False
        # 邮箱更改需要验证码校验
        if new_email and new_email != user.email:
            if not email_code:
                return Response({'msg': '请输入邮箱验证码'}, status=400)
            real_code = email_code_cache.get(new_email)
            if not real_code:
                return Response({'msg': '请先获取验证码'}, status=400)
            if email_code != real_code:
                return Response({'msg': '验证码错误'}, status=400)
            # 检查邮箱唯一性
            if UserProfile.objects.filter(email=new_email).exclude(username=username).exists():
                return Response({'msg': '该邮箱已被其他用户占用'}, status=400)
            user.email = new_email
            updated = True
        if new_password:
            user.password = new_password
            updated = True
        if updated:
            user.save()
            return Response({'msg': '信息修改成功'})
        else:
            return Response({'msg': '没有需要修改的信息'}, status=200)
    except UserProfile.DoesNotExist:
        return Response({'msg': '用户不存在'}, status=404)
    
@api_view(['POST'])
def check_email_available(request):
    email = request.data.get('email')
    username = request.data.get('username')
    if not email:
        return Response({'available': False, 'msg': '邮箱不能为空'}, status=400)
    # 只要不是当前用户自己的邮箱且已被其他用户绑定就不可用
    if UserProfile.objects.filter(email=email).exclude(username=username).exists():
        return Response({'available': False, 'msg': '该邮箱已被其他用户绑定'}, status=200)
    return Response({'available': True, 'msg': '邮箱可用'}, status=200)

@api_view(['GET'])
@csrf_exempt
def user_list(request):
    username = request.GET.get('username') or request.session.get('username')
    try:
        user = UserProfile.objects.get(username=username)
        if user.permission != 2:
            return JsonResponse({'msg': '无权限'}, status=403)
    except UserProfile.DoesNotExist:
        return JsonResponse({'msg': '用户不存在'}, status=404)
    users = UserProfile.objects.all()
    data = [
        {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'permission': user.permission
        }
        for user in users
    ]
    return JsonResponse({'users': data})

@api_view(['POST'])
@csrf_exempt
def delete_user(request):
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
    """
    GET /api/points/?start=2013/9/12 0:00&end=2013/9/12 1:00&car=15053112970&limit=1000
    只读取前2万行，按参数筛选，返回前limit条。
    """
    start = request.GET.get('start')
    end = request.GET.get('end')
    car = request.GET.get('car')
    limit = int(request.GET.get('limit', 1000))
    file_path = r'C:/Users/27448/Desktop/jn0912_baidu_coords.csv'
    # 只读取前2万行
    df = pd.read_csv(file_path, nrows=20000)
    df.columns = [c.strip() for c in df.columns]
    if start:
        df = df[df['UTC'] >= start]
    if end:
        df = df[df['UTC'] <= end]
    if car:
        df = df[df['COMMADDR'].astype(str) == str(car)]
    result = df[['LAT', 'LON', 'UTC', 'COMMADDR', 'TFLAG', 'status']].head(limit)
    data = [
        {
            'lat': row['LAT'],
            'lon': row['LON'],
            'time': row['UTC'],
            'car': row['COMMADDR'],
            'tflag': row['TFLAG'],
            'status': row['status']
        }
        for _, row in result.iterrows()
    ]
    return Response(data)
    
@api_view(['POST'])
def face_verify_one_to_one(request):
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
def face_verify_one_to_one(request):
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
    
