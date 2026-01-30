import cv2
import numpy as np


def process_cv2_image(img: np.ndarray, color_hex: str = "#000000") -> bytes:
    """
    处理已经解码的 OpenCV 图像 (BGR/BGRA)，返回 PNG 字节
    """
    # 解析颜色 (hex -> BGR)
    hex_clean = color_hex.lstrip("#")
    if len(hex_clean) != 6:
        # 默认黑色
        b_val, g_val, r_val = 0, 0, 0
    else:
        r_val = int(hex_clean[0:2], 16)
        g_val = int(hex_clean[2:4], 16)
        b_val = int(hex_clean[4:6], 16)

    # 检查是否已经是透明背景 (4通道且存在透明像素)
    # 若直接返回原图，需重新编码为bytes
    if len(img.shape) == 3 and img.shape[2] == 4:
        alpha_channel = img[:, :, 3]
        if np.min(alpha_channel) < 255:
            success, encoded_image = cv2.imencode(".png", img)
            if not success:
                raise ValueError("Could not encode image")
            return encoded_image.tobytes()

        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    # 3. 转为灰度图
    if len(img.shape) == 3 and img.shape[2] == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img

    # 4.1 自适应阈值化
    mask = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 21, 8
    )

    # 4.2 形态学闭运算
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # 5. 创建 RGBA 图像
    h, w = img.shape[:2]
    foreground = np.zeros((h, w, 3), dtype=np.uint8)
    foreground[:] = (b_val, g_val, r_val)

    rgba = cv2.merge((foreground[:, :, 0], foreground[:, :, 1], foreground[:, :, 2], mask))

    # 6. 重新编码为 PNG
    success, encoded_image = cv2.imencode(".png", rgba)
    if not success:
        raise ValueError("Could not encode image")

    return encoded_image.tobytes()


def process_signature(image_bytes: bytes, color_hex: str = "#000000") -> bytes:
    """
    (Legacy Wrapper) 读取图片字节，处理后返回 PNG 字节
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError("Could not decode image")

    return process_cv2_image(img, color_hex)
