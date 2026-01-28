from fastapi import FastAPI, UploadFile, Response
from fastapi.responses import HTMLResponse
from pathlib import Path
import cv2
import numpy as np

app = FastAPI()


def process_signature(image_bytes: bytes) -> bytes:
    """
    读取图片字节，使用自适应阈值提取深色文字，
    并返回带有透明背景的 PNG 字节。
    """
    # 1. 将字节转换为 numpy 数组
    nparr = np.frombuffer(image_bytes, np.uint8)

    # 2. 解码图片
    # 使用 ORG_UNCHANGED 以便检测 Alpha 通道
    img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError("Could not decode image")

    # 检查是否已经是透明背景 (4通道且存在透明像素)
    if len(img.shape) == 3 and img.shape[2] == 4:
        # 获取 Alpha 通道
        alpha_channel = img[:, :, 3]
        # 如果存在任何非完全不透明的像素，则视为已有透明背景，直接返回原图
        if np.min(alpha_channel) < 255:
            return image_bytes
        
        # 否则，虽然是 4 通道但没有透明内容，丢弃 Alpha 继续处理
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

    # 3. 转为灰度图
    # 无论原图是 BGR 还是 BGRA，OpenCV 通常需要正确转换
    if len(img.shape) == 3 and img.shape[2] == 3:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        # 兜底：如果是灰度图直接用，或者其他情况
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if len(img.shape) == 3 else img

    # 4.1 自适应阈值化以查找文字
    # C=15: 较高的阈值偏移量使判定更加严格，从而获得更细的线条
    mask = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 21, 8
    )

    # 4.2 形态学闭运算：连接断裂的笔画
    # 使用小矩形核修复细微断裂，保证线条连贯性
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    # 5. 创建 RGBA 图像
    # 创建纯黑色背景，这样无论原字是什么颜色（如灰色），输出都会强制变为纯黑 (#000000)
    h, w = img.shape[:2]
    black_bgr = np.zeros((h, w, 3), dtype=np.uint8)
    rgba = cv2.merge((black_bgr[:,:,0], black_bgr[:,:,1], black_bgr[:,:,2], mask))

    # 6. 重新编码为 PNG (以保留透明度)
    success, encoded_image = cv2.imencode(".png", rgba)
    if not success:
        raise ValueError("Could not encode image")

    return encoded_image.tobytes()


@app.get("/")
def read_root():
    return "Welcome to the Signature Extraction Service"


@app.get("/test", response_class=HTMLResponse)
def test_page():
    html_path = Path(__file__).parent / "test.html"
    return html_path.read_text(encoding="utf-8")


@app.post("/extract")
async def extract_signature_endpoint(file: UploadFile):
    contents = await file.read()
    try:
        processed_image = process_signature(contents)
        return Response(content=processed_image, media_type="image/png")
    except Exception as e:
        return {"error": str(e)}



def main():
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8008)


if __name__ == "__main__":
    main()
