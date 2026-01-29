# Puresign

Puresign 是一个专门用于提取手写签名和文字的图像处理服务。它提供了一个高性能的 Python 后端 API，能够去除图片中的复杂背景，提取出干净、透明背景的签名线条，并支持自定义线条颜色。

## 👋 前端开发者的 Python 指南

既然你是第一次接触 Python 项目，这里有一些关键概念的类比，帮助你快速上手：

| Python 概念 | 前端/Node.js 类比 | 说明 |
| :--- | :--- | :--- |
| **`python`** | `node` | 运行环境。本项目要求 Python 3.11+ |
| **`uv`** | `npm` / `pnpm` | **包管理器**。你需要用它来安装依赖、并在隔离的虚拟环境中运行脚本。 |
| **`pyproject.toml`** | `package.json` | 配置文件。定义了项目名称、版本、依赖列表以及工具配置（如 linter）。 |
| **`lock` 文件** | `package-lock.json` | `uv` 会生成 `uv.lock` 文件来锁定依赖版本。 |
| **FastAPI** | Express.js / Next.js API | Web 框架。我们用它来处理 HTTP 请求和路由。 |
| **OpenCV** (`cv2`) | Canvas API (服务端版) | 强大的图像处理库，用于做像素级的操作（去底、二值化）。 |
| **Ruff** | ESLint + Prettier | 极速的代码格式化和检查工具。 |
| **Mypy** | TypeScript | 静态类型检查器。Python 是动态语言，加上 Type Hints 后就像 TS 一样安全。 |

## 🚀 快速开始

### 1. 安装工具链
本项目使用 **[uv](https://github.com/astral-sh/uv)** 进行全栈管理。

### 2. 初始化项目
在项目根目录下运行以下命令，这将安装依赖并自动配置 Git Hooks（代码检查与提交规范）：
```bash
uv run poe setup
```

### 3. 启动开发服务器
```bash
uv run fastapi dev src/puresign/main.py --port 8008
```
*   这相当于 `npm run dev`。
*   服务器将在 `http://127.0.0.1:8008` 启动。
*   支持热重载（修改代码后自动重启）。

---

## 🛠 功能与测试

### 内置测试页面
启动服务后，直接访问：
👉 **http://127.0.0.1:8008/test**

这是一个内置的简单 HTML 页面，你可以：
1. 上传一张包含签名的图片。
2. 实时看到去底后的效果。
3. 调整提取后的签名颜色。

### API 文档
FastAPI 自带了非凡的自动文档功能（Swagger UI）：
👉 **http://127.0.0.1:8008/docs**

你可以在这个页面直接测试 API 接口。

### 核心 API
**`POST /extract`**
*   **Request**: `multipart/form-data`
    *   `file`: 图片文件
    *   `color` (Query Param, 可选): 目标颜色代码 (例如 `%23FF0000` 代表红色)，默认黑色。
*   **Response**: `image/png` (带有透明背景的图片流)

---

## 📂 项目结构

```
puresign/
├── src/
│   └── puresign/
│       ├── main.py       # 核心逻辑入口 (类似 index.js + controller)
│       └── test.html     # 用于测试的简单前端页面
├── pyproject.toml        # 项目配置与依赖 (package.json)
├── uv.lock              # 依赖版本锁定文件
├── README.md             # 你现在看到的文档
└── start.bat / Makefile  # 快捷启动脚本
```

## ⌨️ 开发工作流

在提交代码前，建议运行以下命令以保持代码质量：

**1. 格式化 & Lint (Ruff)**
```bash
# 检查并自动修复（类似 eslint --fix）
uv run ruff check --fix

# 格式化代码（类似 prettier write）
uv run ruff format
```

**2. 类型检查 (Mypy)**
```bash
# 检查类型错误（类似 tsc）
uv run mypy src
```

## 🧩 核心逻辑解析

核心图像处理函数 `process_signature` 在 `src/puresign/main.py` 中。它的工作流程如下：
1.  **解码**: 将上传的二进制流转为 OpenCV 图像对象。
2.  **预处理**: 如果图片本身有些许透明度但非全透，先转为实色背景处理。
3.  **灰度化**: 将彩色图片转为灰度图 (`Gray Scale`)。
4.  **自适应阈值 (Adaptive Threshold)**: 这是核心算法。它不使用全局固定的阈值，而是计算每个像素周围小区域的亮度，根据局部对比度来决定该点是“黑”还是“白”。这能有效应对光照不均或纸张阴影。
5.  **构建 Alpha 通道**: 将检测到的文字部分设为不透明，背景设为完全透明。
6.  **着色**: 将文字部分的像素替换为你指定的颜色（如红色）。

Enjoy your first Python journey! 🐍
