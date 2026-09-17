# 纯内网部署方案

两个方案都使用 `8008` 端口，服务启动后可访问：

- 服务检查：`http://服务器地址:8008/`
- 测试页面：`http://服务器地址:8008/test`
- API 文档：`http://服务器地址:8008/docs`

建议只在内网防火墙放行 `8008`，不要暴露到公网。当前服务没有登录鉴权，内网防火墙是主要访问边界。

## 方案一：Windows Server + Python

适合已有 Windows Server 主机、允许安装 Python 的环境。

### 1. 在 macOS / Linux 构建机生成离线包

```bash
./deploy/build_windows_offline.sh
```

产物 `dist/puresign-<version>-windows-offline.zip`，解压后即为完整部署目录：

```text
puresign-<version>-windows-offline/
├── install.bat                      创建 .venv 并从 wheelhouse 离线安装
├── start.bat                        启动服务
├── disable_quick_edit.py            启动前关闭控制台的「快速编辑模式」
├── puresign-<version>-py3-none-any.whl  项目包
├── requirements-windows.txt         按 Windows 目标求值的依赖清单
├── wheelhouse/                      48 个 Windows wheel
└── SHA256SUMS.txt                   校验和
```


跨平台构建有个坑：`pip download --platform` 只影响 wheel 标签匹配，环境标记（environment marker）仍按构建机求值。macOS 上 `uvicorn[standard]` 因此把没有 Windows wheel 的 `uvloop` 算作必需依赖，直接报 `ResolutionImpossible`。脚本先用 `uv pip compile --python-platform x86_64-pc-windows-msvc` 按 Windows 目标求值出扁平清单，再用 `pip download --no-deps` 取包，最后校验 `wheelhouse` 里没有构建机平台的 wheel。

### 2. 在 Windows Server 安装

目标服务器必须是 Windows x64 + Python 3.11。先确认 `python.exe` 已加入 PATH：

```powershell
python --version
```

把 ZIP 复制到服务器解压，在解压目录执行安装。cmd、PowerShell 和资源管理器双击都可以：

```bat
install.bat
```

脚本会检查 Python 版本、创建 `.venv`，再用 `--no-index --find-links` 从本地 `wheelhouse` 安装，全程不访问外网，失败时返回非 0 退出码。

安装逻辑写成批处理而不是 PowerShell，是因为批处理不受 ExecutionPolicy 约束。组策略可以锁定 `MachinePolicy` 作用域，该作用域无法用 `-ExecutionPolicy Bypass` 覆盖，纯 PowerShell 实现会被直接拦下。

双击运行结束时会 `pause` 保留窗口。PowerShell 启动 `.bat` 同样经过 `cmd /c`，无法与双击区分，自动化调用需要抑制暂停：

```bat
set PURESIGN_NO_PAUSE=1
install.bat
```

### 3. 启动服务


```bat
start.bat
```

`start.bat` 会先关掉该控制台的「快速编辑模式」再启动服务，然后把 uvicorn 日志直接打在窗口里。这个模式是 Windows 控制台的默认行为：鼠标在窗口里点一下就会进入「选择」状态（标题栏出现「选择:」前缀），屏幕停止刷新、写控制台的进程被阻塞。双击启动时那一下点击常常正好落进刚创建的窗口，于是窗口始终空白，服务却其实在跑。没有可用控制台时（例如任务计划程序无窗口运行），脚本会自动改为把输出追加到 `logs\server.out.log`。

窗口空白但接口可用时，按一下 `Esc` 解除冻结即可看到缓冲区里的内容。

生产环境建议用 Windows 任务计划程序托管：触发器设为「系统启动时」，操作程序设为 `start.bat`，「起始于」设为部署目录，并开启失败后自动重启。

### 4. Windows 防火墙

只允许内网网段访问 TCP `8008`。如果只允许固定客户端访问，应将规则限制到对应网段或 IP。

## 方案二：Linux + Docker Compose

适合已安装 Docker Engine 和 Docker Compose Plugin、希望使用容器自动重启和隔离运行的环境。

仓库已提供 `Dockerfile`（基于 Python 3.11 slim）、`docker-compose.yml`（映射 `8008`、自动重启、健康检查）和 `.dockerignore`。

### 1. 构建并导入

纯内网环境推荐在可访问镜像源和 PyPI 的构建机上构建，再把镜像导入内网服务器，这样服务器不需要再下载基础镜像或依赖。构建机和目标服务器的 CPU 架构必须相同。

```bash
docker compose build
docker save puresign:<version> -o puresign-<version>.tar
```

把 `docker-compose.yml` 和 `puresign-<version>.tar` 复制到服务器：

```bash
docker load -i puresign-<version>.tar
docker compose up -d --no-build
```

如果服务器可以访问企业内网镜像仓库，也可以直接在服务器构建：

```bash
docker compose build
docker compose up -d
```

### 2. 运维命令

```bash
docker compose ps
docker compose logs -f puresign
docker compose down
```

### 3. 运行特性

- 容器内监听 `0.0.0.0:8008`，宿主机通过 `8008:8008` 对内网提供访问。
- `restart: unless-stopped` 在容器异常退出或 Docker 重启后自动拉起。
- `/app/logs` 使用 named volume `puresign_logs` 持久化。
- 健康检查访问根路径 `/`，连续失败可通过 Compose 状态发现。

## 其他注意事项

- 当前 CORS 配置允许所有来源，若内网存在多个业务系统，建议按实际前端地址收紧。
- 端口在代码中固定为 `8008`，如需改用其他端口，通过 Windows 端口代理或 Compose 端口映射实现。
