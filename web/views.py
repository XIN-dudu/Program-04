from rest_framework.decorators import parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
import cv2
import tempfile
from django.utils import timezone
from web.models import AlertEvent, SystemLog, UserProfile
from django.http import JsonResponse
from rest_framework.decorators import api_view


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