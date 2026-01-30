from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from loguru import logger

from puresign.logger import setup_logger
from puresign.processor import process_signature


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Configure logging
    setup_logger()
    logger.info("Service starting up...")
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
        # Pass color to processing function
        processed_image = process_signature(contents, color)
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
