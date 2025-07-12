import os
from ultralytics import YOLO

if __name__ == "__main__":
    pth_path = r"roadMonitor/best.pt"

    test_path = r"media/road/China_Drone_000008.jpg"

    # 指定自定义保存路径（需要先创建目录）
    save_dir = r"media/road/results"  # 你的目标路径
    os.makedirs(save_dir, exist_ok=True)  # 自动创建目录（如果不存在）

    # Load a model
    # model = YOLO('yolov8n.pt')  # load an official model
    model = YOLO(pth_path)  # load a custom model

    # Predict with the model
    # 预测并指定保存路径
    results = model(
        test_path,
        save=True,
        conf=0.5,
        project=save_dir  # 关键参数：指定保存目录
    )