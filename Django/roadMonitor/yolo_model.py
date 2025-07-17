import base64
import io
import os
from PIL import Image, ImageDraw, ImageFont
from django.conf import settings
from ultralytics import YOLO

model = YOLO(os.path.join(settings.BASE_DIR, "best2.pt"))

label_map = {
    0: "D00",
    1: "D10",
    2: "D20",
    3: "D40",
    4: "repair"
}

def run_detection_in_memory(file_obj):
    image = Image.open(file_obj).convert('RGB')
    results = model(image)[0]

    orig_w, orig_h = image.size
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype("arial.ttf", 16)  # 可替换成其他字体
    except:
        font = ImageFont.load_default()

    detections = []

    for box in results.boxes:
        cls_id = int(box.cls[0].item())
        conf = float(box.conf[0].item())
        x1, y1, x2, y2 = box.xyxy[0].tolist()

        disease_type = label_map.get(cls_id, f'类别{cls_id}')
        severity = '高' if conf > 0.7 else '中' if conf > 0.4 else '低'
        area = ((x2 - x1) * (y2 - y1)) / (orig_w * orig_h)
        length = x2 - x1

        # 绘制框
        color = (255, 0, 0)
        draw.rectangle([x1, y1, x2, y2], outline=color, width=3)

        text = f"{disease_type} {conf:.2f}"
        bbox = draw.textbbox((x1, y1), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        text_bg = [x1, y1 - text_h, x1 + text_w, y1]
        draw.rectangle(text_bg, fill=color)
        draw.text((x1, y1 - text_h), text, fill=(255, 255, 255), font=font)

        detections.append({
            "disease_type": disease_type,
            "severity": severity,
            "area": round(area, 4),
            "length": round(length, 4)
        })

    buffer = io.BytesIO()
    image.save(buffer, format='JPEG')
    base64_full = base64.b64encode(buffer.getvalue()).decode('utf-8')
    full_image_base64 = f"data:image/jpeg;base64,{base64_full}"

    return detections, full_image_base64
