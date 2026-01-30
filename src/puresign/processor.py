import cv2
import numpy as np


# 核心处理逻辑：输入 BGR 图像和目标颜色，返回处理后的 RGBA 图像
def core_process_image(img_bgr: np.ndarray, color_bgr: tuple[int, int, int]) -> np.ndarray:
    # 转为灰度图
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    # 自适应阈值化
    mask = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 21, 8
    )

    # 形态学闭运算
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # 创建 RGBA 图像
    h, w = img_bgr.shape[:2]
    foreground = np.zeros((h, w, 3), dtype=np.uint8)
    foreground[:] = color_bgr

    rgba = cv2.merge((foreground[:, :, 0], foreground[:, :, 1], foreground[:, :, 2], mask))
    return rgba


# 处理已经解码的 OpenCV 图像 (BGR/BGRA)，返回 PNG 字节
def process_cv2_image(img: np.ndarray, color_hex: str = "#000000") -> bytes:
    # 解析颜色 (hex -> BGR)
    hex_clean = color_hex.lstrip("#")
    if len(hex_clean) != 6:
        # 默认黑色
        b_val, g_val, r_val = 0, 0, 0
    else:
        r_val = int(hex_clean[0:2], 16)
        g_val = int(hex_clean[2:4], 16)
        b_val = int(hex_clean[4:6], 16)

    target_color = (b_val, g_val, r_val)

    # 检查是否已经是透明背景 (4通道且存在透明像素)
    if len(img.shape) == 3 and img.shape[2] == 4:
        alpha_channel = img[:, :, 3]
        if np.min(alpha_channel) < 255:
            # 1. 寻找非透明区域的包围盒
            # findNonZero 需要单通道
            coords = cv2.findNonZero(alpha_channel)
            if coords is not None:
                x, y, w, h = cv2.boundingRect(coords)

                # 增加 padding (防止边缘被切断)
                pad = -2
                h_img, w_img = img.shape[:2]
                x_start = max(0, x - pad)
                y_start = max(0, y - pad)
                x_end = min(w_img, x + w + pad)
                y_end = min(h_img, y + h + pad)

                # 2. 裁剪有效区域
                roi_rgba = img[y_start:y_end, x_start:x_end]

                # 3. 将透明底转为白底 (为了让阈值算法正常工作)
                # 分离通道
                roi_alpha = roi_rgba[:, :, 3] / 255.0
                roi_bgr = roi_rgba[:, :, :3]

                # 创建白底
                white_bg = np.ones_like(roi_bgr, dtype=np.uint8) * 255

                # 混合: alpha * foreground + (1-alpha) * background
                # 注意需要广播
                roi_composite = (
                    roi_bgr * roi_alpha[:, :, np.newaxis]
                    + white_bg * (1 - roi_alpha[:, :, np.newaxis])
                ).astype(np.uint8)

                # 4. 处理核心逻辑
                processed_roi = core_process_image(roi_composite, target_color)

                # 5. 恢复到原尺寸全透明画布
                final_h, final_w = img.shape[:2]
                final_rgba = np.zeros((final_h, final_w, 4), dtype=np.uint8)

                # 贴回原位
                final_rgba[y_start:y_end, x_start:x_end] = processed_roi

                success, encoded_image = cv2.imencode(".png", final_rgba)
                if not success:
                    raise ValueError("Could not encode image")
                return encoded_image.tobytes()

            # 如果全是透明的，直接返回全透明图或原图
            success, encoded_image = cv2.imencode(".png", img)
            return encoded_image.tobytes()

        # 虽然是4通道但没有透明像素，转BGR继续
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    # 普通 BGR 图片处理
    processed_rgba = core_process_image(img, target_color)

    # 重新编码为 PNG
    success, encoded_image = cv2.imencode(".png", processed_rgba)
    if not success:
        raise ValueError("Could not encode image")

    return encoded_image.tobytes()


# 处理图片字节，返回 PNG 字节
def process_signature(image_bytes: bytes, color_hex: str = "#000000") -> bytes:
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)

    if img is None:
        raise ValueError("Could not decode image")

    return process_cv2_image(img, color_hex)
