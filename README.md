# Puresign

Puresign 是一个专门用于提取手写签名和文字的图像处理服务。它提供了一个高性能的 Python 后端 API，能够去除图片中的复杂背景，提取出干净、透明背景的签名线条，并支持自定义线条颜色。

## 👋 前端开发者的 Python 指南

既然你是第一次接触 Python 项目，这里有一些关键概念的类比，帮助你快速上手：

| Python 概念 | 前端/Node.js 类比 | 说明 |
| :--- | :--- | :--- |
| **`python`** | `node` | 运行环境。本项目要求 Python 3.11+ |
| **`uv`** | `npm` / `pnpm` | **包管理器**。你需要用它来安装依赖、并在隔离的虚拟环境中运行脚本。 |
| **`pyproject.toml`** | `package.json` | 配置文件。定义了项目名称、版本、依赖列表以及工具配置。 |
| **`poe`** (PoeThePoet) | `npm scripts` | **任务运行器**。定义简单的命令别名（如 `dev`, `lint`）。 |
| **FastAPI** | Express.js / Next.js API | Web 框架。我们用它来处理 HTTP 请求和路由。 |
| **OpenCV** (`cv2`) | Canvas API (服务端版) | 强大的图像处理库，用于做像素级的操作（去底、二值化）。 |
| **Ruff** | ESLint + Prettier | 极速的代码格式化和检查工具。 |
| **Ty** | TypeScript (tsc) | **静态类型检查器**。Python 是动态语言，加上 Type Hints 后就像 TS 一样安全。 |

## 🚀 快速开始

### 1. 安装工具链
本项目使用 **[uv](https://github.com/astral-sh/uv)** 进行全栈管理。你需要先安装它：
```bash
# Mac/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. 初始化项目 & 同步依赖
在项目根目录下运行以下命令，这将安装依赖并自动配置 Git Hooks（代码检查与提交规范）：
```bash
uv run poe setup
```
> **注意**：如果未来依赖有更新，请运行 `uv sync` 同步环境。

### 3. 启动开发服务器
```bash
uv run poe dev
```
*   这相当于 `npm run dev`。
*   服务器将在 `http://127.0.0.1:8008` 启动。
*   支持热重载（修改代码后自动重启）。

---

## ⌨️ 开发工作流

本项目配置了自动化任务（类似 `npm run xxx`），统一使用 `poe` 管理。可以通过 `uv run poe <task>` 运行：

| 任务命令 | 作用 | Node.js 类比 |
| :--- | :--- | :--- |
| **`uv run poe dev`** | 启动开发服务器 (Hot Reload) | `npm run dev` |
| **`uv run poe start`** | 启动生产环境服务器 | `npm start` |
| **`uv run poe check`** | **一键检查**：格式化 + Lint + 类型检查 | `npm run check` |
| **`uv run poe format`** | 格式化代码 (Ruff) | `npm run format` |
| **`uv run poe lint`** | 检查代码风格并修复 (Ruff) | `npm run lint` |
| **`uv run poe type`** | 运行类型检查 (Ty) | `npm run type-check` |
| **`uv run poe build`** | 构建项目包 | `npm run build` |

## 🚀 纯内网部署

项目提供两种部署方式：

1. **Windows Server + Python**：在 macOS / Linux 构建机运行 `deploy/build_windows_offline.sh` 生成包含全部依赖的一体化 ZIP，服务器安装 Python 3.11 后运行 `install.bat` 和 `start.bat`。
2. **Linux + Docker Compose**：使用仓库中的 `Dockerfile` 和 `docker-compose.yml` 构建并启动容器。

完整的准备、离线依赖、启动和防火墙说明见 [DEPLOYMENT.md](DEPLOYMENT.md)。

### ✅ Git 提交规范
本项目集成了 **[Pre-commit](https://pre-commit.com/)** 和 **[Commitizen](https://commitizen-tools.github.io/commitizen/)**：

1.  **Pre-commit Hook**: 每次 `git commit` 时，会自动运行 `check` 任务。如果有代码风格错误，提交会被阻止。
2.  **Commit Message**: 提交信息必须遵守 [Conventional Commits](https://www.conventionalcommits.org/) 规范。
    *   ❌ `fix bug`
    *   ✅ `fix: handle transparent background correctly`
    *   ✅ `feat: add color customization`

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
├── pyproject.toml        # === package.json (配置中心)
├── uv.lock              # === package-lock.json (版本锁定)
├── .pre-commit-config.yaml # Git Hooks 配置
└── README.md
```

## 🧩 核心逻辑解析

核心图像处理函数 `process_signature` 在 `src/puresign/main.py` 中。流程如下：
1.  **解码**: `cv2.imdecode` 读取图片。
2.  **预处理**: 统一处理图片透明度通道。
3.  **灰度化**: `cv2.cvtColor` 转灰度。
4.  **自适应阈值**: `cv2.adaptiveThreshold` 智能提取文字线条，忽略光照阴影。
5.  **构建 Alpha**: 将提取的 Mask 作为 Alpha 通道，实现去底。
6.  **着色**: 像素级颜色替换。

Enjoy your first Python journey! 🐍
