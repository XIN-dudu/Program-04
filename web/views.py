from rest_framework.decorators import parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
import cv2
import tempfile
from django.utils import timezone
from web.models import AlertEvent, SystemLog, UserProfile
from django.http import JsonResponse

from rest_framework.decorators import api_view

 print("web.views.py loaded")

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def liveness_and_face_verify(request):
    print("liveness_and_face_verify called")
    user_id = request.data.get('user_id') or request.POST.get('user_id')
    video_file = request.FILES.get('video')
    if not video_file or not user_id:
        return JsonResponse({'success': False, 'msg': '缺少参数'}, status=400)
    with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as tmp_video:
        for chunk in video_file.chunks():
            tmp_video.write(chunk)
        video_path = tmp_video.name
    try:
        liveness_pass = call_baidu_liveness_api(video_path, username=user_id)
        if not liveness_pass:
            AlertEvent.objects.create(user_id=user_id, alert_type='活体检测失败', alert_time=timezone.now())
            SystemLog.objects.create(user_id=user_id, action='活体检测失败', log_time=timezone.now())
            return JsonResponse({'success': False, 'msg': '活体检测未通过'})
        images = extract_frames(video_path, num_frames=3)
        verify_success = False
        for img in images:
            if call_face_verify_api(img, user_id):
                verify_success = True
                break
        if verify_success:
            SystemLog.objects.create(user_id=user_id, action='人脸识别通过', log_time=timezone.now())
            return JsonResponse({'success': True, 'msg': '验证通过'})
        else:
            AlertEvent.objects.create(user_id=user_id, alert_type='人脸识别失败', alert_time=timezone.now())
            SystemLog.objects.create(user_id=user_id, action='人脸识别失败', log_time=timezone.now())
            return JsonResponse({'success': False, 'msg': '人脸识别未通过'})
    finally:
        import os
        if os.path.exists(video_path):
            os.remove(video_path)

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

def call_baidu_liveness_api(video_path, username=None):
    import requests
    from django.conf import settings
    import base64
    import cv2
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames // 2)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return False
    _, img_encoded = cv2.imencode('.jpg', frame)
    img_bytes = img_encoded.tobytes()
    url = getattr(settings, 'SELF_BASE_URL', 'http://localhost:8000') + '/api/liveness_check/'
    data = {'username': username}
    files = {'image': ('frame.jpg', img_bytes, 'image/jpeg')}
    try:
        resp = requests.post(url, data=data, files=files, timeout=10)
        result = resp.json()
        return result.get('liveness', False)
    except Exception:
        return False

def call_face_verify_api(img_bytes, username):
    from django.test import RequestFactory
    from web.views import face_verify_one_to_one
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