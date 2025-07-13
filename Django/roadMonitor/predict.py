import os
from ultralytics import YOLO
from django.conf import settings

def predict_image(test_path):
    print(1)
    # 创建结果保存目录（YOLO会自动创建子目录）
    pth_path=r"Django/best.pt"
    save_dir=r"Django/media/road"
    os.makedirs(save_dir, exist_ok=True)

    print(2)
    model = YOLO(pth_path)
    
    print(3)
    # 执行预测
    results = model(
        test_path,
        save=True,
        conf=0.5,
        project=save_dir,  # 指定根目录
        name='results',    # 创建results子目录
        exist_ok=True
    )
    
    print(4)
    # 解析预测结果路径
    file_name = os.path.basename(test_path)
    print(5)
    
    # 构造完整结果路径：Django/media/road/results/
    return os.path.join(save_dir, 'results', file_name)

if __name__ == "__main__":
    test_path = r"Django/media/road/China_Drone_000002.jpg"
    print(predict_image(test_path))

    # print(os.path.join(settings.BASE_DIR, "roadMonitor", "best.pt"))