import os
from pathlib import Path
import threading

from loguru import logger
import numpy as np
from paddleocr import PaddleOCR

# 全局单例
_ocr_engine: PaddleOCR | None = None
_lock = threading.Lock()


def get_ocr_engine() -> PaddleOCR:
    """
    获取全局唯一的 PaddleOCR 实例（懒加载 + 线程安全）
    """
    global _ocr_engine
    if _ocr_engine is None:
        with _lock:
            if _ocr_engine is None:
                logger.info("Initializing PaddleOCR engine...")

                # 设置模型存储路径到项目下的 models 目录
                project_models_dir = Path.cwd() / "models"
                os.environ["PADDLEOCR_HOME"] = str(project_models_dir)

                # use_angle_cls=True: 支持方向分类
                # lang="ch": 中英文通用
                # show_log=False:仅仅为了减少日志噪音
                _ocr_engine = PaddleOCR(
                    use_angle_cls=True,
                    lang="ch",
                    show_log=False,
                    use_gpu=False,
                    det_db_box_thresh=0.3,  # 降低检测阈值，防止遗漏细笔画
                )
                logger.success("PaddleOCR engine initialized")

    if _ocr_engine is None:
        raise RuntimeError("Failed to initialize PaddleOCR engine")

    return _ocr_engine


def detect_and_crop(img: np.ndarray, padding: int = 10) -> np.ndarray:
    """
    使用 OCR 检测文字区域并裁剪。
    如果未检测到文字，返回原图。
    """
    ocr = get_ocr_engine()

    # 1. 检测 (det=True, rec=False 以提高速度)
    # result 结构: [[[[x1, y1], [x2, y2], [x3, y3], [x4, y4]], (text, confidence)], ...]
    # 但当 rec=False 时，返回的是一系列坐标框
    # 注意: ocr.ocr() 返回的是一个 list，第一层对应 batch_size (通常为1)

    try:
        results = ocr.ocr(img, det=True, rec=False, cls=False)
    except Exception as e:
        logger.error(f"OCR detection failed: {e}")
        return img

    if not results or results[0] is None:
        logger.warning("No text detected by OCR, returning original image")
        return img

    boxes = results[0]  # 获取第一张图的结果
    if not boxes:
        return img

    # 2. 计算最小外接矩形
    # boxes 中的点通常是 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
    # 我们需要找到所有框的 global min_x, min_y, max_x, max_y

    all_points = []
    for box in boxes:
        for point in box:
            all_points.append(point)

    all_points = np.array(all_points)

    x_min = int(np.min(all_points[:, 0]))
    y_min = int(np.min(all_points[:, 1]))
    x_max = int(np.max(all_points[:, 0]))
    y_max = int(np.max(all_points[:, 1]))

    # 3. 添加 Padding 并处理边界
    h, w = img.shape[:2]

    x_min = max(0, x_min - padding)
    y_min = max(0, y_min - padding)
    x_max = min(w, x_max + padding)
    y_max = min(h, y_max + padding)

    logger.info(f"Cropping image to area: ({x_min}, {y_min}) - ({x_max}, {y_max})")

    # 4. 裁剪
    cropped_img = img[y_min:y_max, x_min:x_max]

    # 防止裁剪出空图
    if cropped_img.size == 0:
        return img

    return cropped_img


def preload_ocr():
    """在应用启动时预热模型"""
    try:
        get_ocr_engine()
    except Exception as e:
        logger.error(f"Failed to preload OCR engine: {e}")
