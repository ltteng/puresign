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
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image")

    # 3. 转为灰度图
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # 4. 自适应阈值化以查找文字
    # blockSize=21, C=10 是针对手写文字的良好启发式默认值
    mask = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 21, 10
    )

    # 5. 创建 RGBA 图像
    # 使用原始颜色通道，但使用掩码作为 Alpha 通道
    b, g, r = cv2.split(img)
    rgba = cv2.merge((b, g, r, mask))

    # 6. 重新编码为 PNG (以保留透明度)
    success, encoded_image = cv2.imencode(".png", rgba)
    if not success:
        raise ValueError("Could not encode image")

    return encoded_image.tobytes()


@app.get("/")
def read_root():
    return {"Hello": "World"}


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
