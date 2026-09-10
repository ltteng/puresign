#!/usr/bin/env bash
# 在 macOS / Linux 构建机上生成 Windows x64 + Python 3.11 的离线部署包。
#
# 关键点：不能直接把 wheel 交给 pip download 让它自行解析依赖。
# pip 的 --platform 只影响 wheel 标签匹配，不影响环境标记（environment marker）求值，
# 标记仍按构建机求值。在 macOS 上 sys_platform == "darwin"，
# 于是 uvicorn[standard] 的 uvloop 被算作必需依赖，而 uvloop 没有 win_amd64 wheel，
# 配合 --only-binary=:all: 必然报 ResolutionImpossible。
#
# 因此这里分两步：
# 1. uv pip compile --python-platform x86_64-pc-windows-msvc 按 Windows 目标求值标记，
#    输出一份不含标记的扁平锁定清单（自动排除 uvloop，纳入 colorama / win32-setctime）。
# 2. pip download --no-deps -r 该清单，pip 只负责按目标标签取包，不再做任何解析。

set -euo pipefail

PY_TAG="${PY_TAG:-311}"                                   # pip 用：311
PY_DOT="${PY_DOT:-3.11}"                                  # uv 用：3.11
WHEEL_PLATFORM="${WHEEL_PLATFORM:-win_amd64}"             # pip wheel 标签
UV_PLATFORM="${UV_PLATFORM:-x86_64-pc-windows-msvc}"      # uv 目标平台

# 脚本位于 deploy/，项目根是它的父目录。
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

if ! command -v uv >/dev/null 2>&1; then
    echo "未找到 uv。请先安装：curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
    exit 1
fi

# ---------- 1. 构建项目 wheel ----------
BUILD_DIR="$PROJECT_ROOT/dist/windows-build"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

uv build --wheel --out-dir "$BUILD_DIR"

WHEEL_PATH="$(find "$BUILD_DIR" -name 'puresign-*.whl' -type f | sort | tail -n 1)"
if [[ -z "$WHEEL_PATH" ]]; then
    echo "uv build 未生成 puresign wheel。" >&2
    exit 1
fi
WHEEL_NAME="$(basename "$WHEEL_PATH")"

# puresign-0.3.0-py3-none-any.whl -> puresign-0.3.0
BUNDLE_NAME="${WHEEL_NAME%.whl}"
BUNDLE_NAME="${BUNDLE_NAME%-py3-none-any}"

BUNDLE_DIR="$PROJECT_ROOT/dist/${BUNDLE_NAME}-windows-offline"
rm -rf "$BUNDLE_DIR"
mkdir -p "$BUNDLE_DIR/wheelhouse"

# ---------- 2. 按 Windows 目标解析依赖 ----------
REQUIREMENTS="$BUNDLE_DIR/requirements-windows.txt"
uv pip compile pyproject.toml \
    --python-platform "$UV_PLATFORM" \
    --python-version "$PY_DOT" \
    --quiet \
    --output-file "$REQUIREMENTS"

# ---------- 3. 准备一个自带 pip 的临时环境 ----------
# macOS 上的 python3 未必带可用 pip，uv 创建的环境默认也不含 pip，这里显式装一个。
TOOLS_VENV="$PROJECT_ROOT/dist/.build-tools"
rm -rf "$TOOLS_VENV"
uv venv --quiet "$TOOLS_VENV"
uv pip install --quiet --python "$TOOLS_VENV/bin/python" pip
TOOLS_PYTHON="$TOOLS_VENV/bin/python"

# ---------- 4. 下载 Windows wheel ----------
"$TOOLS_PYTHON" -m pip download \
    --disable-pip-version-check \
    --only-binary=:all: \
    --no-deps \
    --dest "$BUNDLE_DIR/wheelhouse" \
    --platform "$WHEEL_PLATFORM" \
    --python-version "$PY_TAG" \
    --implementation cp \
    --abi "cp$PY_TAG" \
    --requirement "$REQUIREMENTS"

rm -rf "$TOOLS_VENV"

# 校验：不应出现构建机平台的二进制 wheel
STRAY="$(find "$BUNDLE_DIR/wheelhouse" -name '*.whl' \
    ! -name '*-none-any.whl' ! -name '*win_amd64.whl' -print)"
if [[ -n "$STRAY" ]]; then
    echo "检测到非 Windows 平台的 wheel，离线包不可用：" >&2
    echo "$STRAY" >&2
    exit 1
fi

# ---------- 5. 组装部署包 ----------
cp "$WHEEL_PATH" "$BUNDLE_DIR/"
cp "$SCRIPT_DIR/install.bat" "$BUNDLE_DIR/"
cp "$SCRIPT_DIR/start.bat" "$BUNDLE_DIR/"

(
    cd "$BUNDLE_DIR"
    find . -type f ! -name SHA256SUMS.txt -print0 |
        sort -z |
        xargs -0 shasum -a 256 |
        sed 's|\./||' >SHA256SUMS.txt
)

ARCHIVE="$BUNDLE_DIR.zip"
rm -f "$ARCHIVE"
# 从 BUNDLE_DIR 内部打包，ZIP 根直接是文件而非再套一层同名目录。
# Windows 资源管理器「解压全部」本身会按 ZIP 文件名建一层目录，
# 压缩包内如果再带顶层目录就会出现双层嵌套。
(
    cd "$BUNDLE_DIR"
    zip -q -r -X "$ARCHIVE" .
)

WHEEL_COUNT="$(find "$BUNDLE_DIR/wheelhouse" -name '*.whl' | wc -l | tr -d ' ')"
echo "Windows 离线部署包已生成：$ARCHIVE"
echo "依赖 wheel 数量：$WHEEL_COUNT（目标 Windows x64 / Python $PY_DOT）"
