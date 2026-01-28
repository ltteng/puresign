# Puresign Project Instructions

## Overview
Puresign is a Python project built with FastAPI that provides specialized image processing services for extracting handwritten signatures and text. It uses OpenCV for background removal and text extraction.

## Tech Stack
- **Language**: Python (>=3.11.9)
- **Framework**: FastAPI (standard edition)
- **Core Libraries**: `opencv-python-headless`, `numpy`
- **Package Manager**: [uv](https://docs.astral.sh/uv/)
- **Linter/Formatter**: [Ruff](https://docs.astral.sh/ruff/)

## Development Ecosystem & Workflow
- **Dependency Management**:
  - STRICTLY use `uv` for all package operations.
  - Add dependency: `uv add <package>`
  - Sync environment: `uv sync`
- **Execution**:
  - Run Server (Dev): `uv run fastapi dev src/puresign/main.py --port 8008`
  - Run Server (Script): `uv run python src/puresign/main.py` (Default port: 8008)
  - Run Entry Point: `uv run puresign-server` (after install)

## Coding Standards
- **Style**: Follow Ruff defaults. Run `uv run ruff format` often.
- **Typing**: Enforce strict type hinting.
- **Image Processing**:
  - Use `cv2.imdecode` with `np.frombuffer` for handling UploadFile bytes.
  - Prefer `cv2.IMREAD_UNCHANGED` to preserve Alpha channels.
  - Processing pipeline: Background Normalization -> Adaptive Thresholding -> Mask Generation -> Color Replacement.

## Project Structure
- `src/puresign/`: Source code package.
- `src/puresign/main.py`: FastAPI entry point. Contains `app` and image processing logic.
- `src/puresign/test.html`: Simple frontend for testing image extraction.
- `pyproject.toml`: dependencies and `[project.scripts]` configuration.

## Key Features
- **Signature Extraction**: `process_signature` function removes complex backgrounds using morphological operations and adaptive thresholding.
- **Color Customization**: Supports re-coloring extracted text via query parameter (default Black #000000).
- **Embedded Test Page**: Serves a testing UI at `GET /test`.

## Critical Files
- [pyproject.toml](pyproject.toml): Dependencies.
- [src/puresign/main.py](src/puresign/main.py): All core logic.
