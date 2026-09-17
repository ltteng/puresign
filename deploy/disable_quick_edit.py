"""启动服务前关掉当前控制台的「快速编辑模式」(QuickEdit)。

Windows 控制台默认开启 QuickEdit：鼠标在窗口里点一下就进入「标记/选择」模式，conhost 停止
渲染屏幕，写入控制台的数据不再显示；屏幕缓冲区填满后，写入进程会一直阻塞在 WriteFile /
WriteConsole 上，直到按 Enter 或 Esc 退出选择模式。

双击 .bat 启动正好提供了这一下点击（鼠标抬起事件常常落进刚创建的控制台窗口），于是窗口从
第一行起就是冻结的。两个典型症状：

1. 窗口始终空白，但服务其实在正常运行；
2. 服务把日志写向控制台时被阻塞 —— uvicorn 的 "Started server process" 是在绑定端口之前
   输出的，所以这一下阻塞会让端口根本没被监听，看起来就是「按回车服务才起来」。

这里用 SetConsoleMode 清掉 ENABLE_QUICK_EDIT_MODE。控制台的输入模式属于控制台输入缓冲区，
附着到同一个控制台的所有进程共享，因此子进程修改同样生效。清掉之后这个窗口不会再进入选择
模式，日志可以安全地直接打在窗口里。

退出码：0 表示已关闭（或本来就没开）；1 表示没控制台/改不动，调用方应回退为「日志写文件」。
"""

import ctypes
import sys

STD_INPUT_HANDLE = -10
ENABLE_QUICK_EDIT_MODE = 0x0040
ENABLE_EXTENDED_FLAGS = 0x0080
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value


def disable_quick_edit() -> bool:
    """关闭当前控制台的 QuickEdit。成功或本来就是关闭状态时返回 True。"""
    if sys.platform != "win32":
        return False

    # WinDLL 只存在于 Windows；用 getattr 取出以便静态检查器在别的平台也能通过。
    win_dll = getattr(ctypes, "WinDLL", None)
    if win_dll is None:
        return False

    kernel32 = win_dll("kernel32", use_last_error=True)
    kernel32.GetStdHandle.argtypes = [ctypes.c_uint32]
    kernel32.GetStdHandle.restype = ctypes.c_void_p
    kernel32.GetConsoleMode.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint32)]
    kernel32.GetConsoleMode.restype = ctypes.c_int
    kernel32.SetConsoleMode.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
    kernel32.SetConsoleMode.restype = ctypes.c_int

    # STD_INPUT_HANDLE 是 -10，按 DWORD 传入需要转成无符号值。
    handle = kernel32.GetStdHandle(ctypes.c_uint32(STD_INPUT_HANDLE & 0xFFFFFFFF).value)
    # 没有控制台（任务计划程序、重定向）时只会拿到空句柄或 INVALID_HANDLE_VALUE。
    if not handle or handle == INVALID_HANDLE_VALUE:
        return False

    mode = ctypes.c_uint32()
    if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
        return False
    if not mode.value & ENABLE_QUICK_EDIT_MODE:
        return True

    # 修改 QuickEdit 时必须同时置上 ENABLE_EXTENDED_FLAGS，否则 Windows 会忽略这次调用。
    new_mode = (mode.value & ~ENABLE_QUICK_EDIT_MODE) | ENABLE_EXTENDED_FLAGS
    return bool(kernel32.SetConsoleMode(handle, new_mode))


def main() -> int:
    if disable_quick_edit():
        return 0
    print("[WARN] Could not disable console QuickEdit mode.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
