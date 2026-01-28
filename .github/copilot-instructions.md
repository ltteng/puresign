# Puresign Project Instructions

## Overview
Puresign is a Python project built with FastAPI, managed by `uv`.

## Tech Stack
- **Language**: Python (>=3.13)
- **Framework**: FastAPI (standard edition)
- **Package Manager**: [uv](https://docs.astral.sh/uv/)
- **Linter/Formatter**: [Ruff](https://docs.astral.sh/ruff/)

## Development Ecosystem & Workflow
- **Dependency Management**:
  - STRICTLY use `uv` for all package operations.
  - Add dependency: `uv add <package>`
  - Dev dependency: `uv add --dev <package>`
  - Sync environment: `uv sync`
- **Execution**:
  - Run scripts via `uv run`: `uv run python src/puresign/main.py`
  - Run FastAPI dev server: `uv run fastapi dev src/puresign/main.py` (once configured)

## Coding Standards
- **Style & Linting**: 
  - Follow Ruff defaults. 
  - Run checks: `uv run ruff check`
  - Format code: `uv run ruff format`
- **Typing**: Enforce strict type hinting on all function signatures. Use Pydantic models for data validation.

## Project Structure
- `src/puresign/`: Source code directory.
- `src/puresign/main.py`: FastAPI application entry point. Must initialize `app = FastAPI()`. Use `if __name__ == "__main__":` block to run via `uv run fastapi dev` or `uvicorn`.
- `pyproject.toml`: Single source of truth for dependencies and tool configuration.

## Critical Files
- [pyproject.toml](pyproject.toml): Dependencies and project metadata.
- [src/puresign/main.py](src/puresign/main.py): Application entry point.
