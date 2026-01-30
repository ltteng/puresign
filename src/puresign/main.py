from contextlib import asynccontextmanager
from pathlib import Path

import cv2
from fastapi import FastAPI, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from loguru import logger
import numpy as np

from puresign.logger import setup_logger
from puresign.ocr import detect_and_crop, preload_ocr
from puresign.processor import process_cv2_image


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Configure logging
    setup_logger()
    logger.info("Service starting up...")

    # 预热 OCR 模型
    preload_ocr()

    yield
    # Shutdown: Clean up if necessary
    logger.info("Service shutting down...")


app = FastAPI(title="Signature Extraction Service", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,  # type: ignore
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root() -> str:
    return "Welcome to the Signature Extraction Service"


@app.get("/test", response_class=HTMLResponse)
def test_page() -> str:
    html_path = Path(__file__).parent / "test.html"
    return html_path.read_text(encoding="utf-8")


@app.post("/extract")
async def extract_signature_endpoint(file: UploadFile, color: str = "#000000") -> Response:
    logger.info(f"Received extraction request for file: {file.filename}, color: {color}")
    contents = await file.read()
    try:
        # 1. 解码图片
        nparr = np.frombuffer(contents, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
        if img is None:
            raise ValueError("Could not decode image")

        # 2. OCR 智能裁剪 (如果找不到文字会返回原图)
        cropped_img = detect_and_crop(img)

        # 3. 图像处理 (去背 + 变色)
        processed_image = process_cv2_image(cropped_img, color)

        logger.success(f"Successfully processed image: {len(processed_image)} bytes")
        return Response(content=processed_image, media_type="image/png")
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        # Return error as JSON response manually
        return JSONResponse(status_code=400, content={"error": str(e)})


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8008)


if __name__ == "__main__":
    main()
