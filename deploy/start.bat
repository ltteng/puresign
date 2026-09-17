@echo off
rem ---------------------------------------------------------------------------
rem Puresign service launcher.
rem
rem Run from cmd.exe:     start.bat
rem Run from PowerShell:  .\start.bat
rem Or double-click this file in Explorer.
rem
rem Why this script touches QuickEdit:
rem
rem A Windows console has "QuickEdit Mode" on by default. A single mouse click
rem inside the window puts conhost into mark/selection mode: the display stops
rem rendering, and once the screen buffer fills up the writing process blocks
rem inside WriteFile until Enter or Esc. Double-clicking a .bat is exactly that
rem click - the mouse-up often lands in the freshly created console - so the
rem window can already be frozen before the first line is drawn.
rem
rem That produces two confusing symptoms: a completely blank window while the
rem service is actually running, and "the API only answers after pressing
rem Enter" (uvicorn logs "Started server process" *before* it binds the socket,
rem so a blocked write there means the port never opens).
rem
rem disable_quick_edit.py clears ENABLE_QUICK_EDIT_MODE on this console before
rem the service starts. The console input mode lives in the console input
rem buffer, which every process attached to the console shares, so a child
rem process can change it. Once cleared the window cannot freeze and the
rem service can log straight into it.
rem
rem If the flag cannot be cleared - no console at all (Task Scheduler) or a
rem policy - the script falls back to appending to logs\server.out.log, where a
rem frozen console can no longer block the service.
rem
rem Kept ASCII-only on purpose: cmd.exe decodes .bat files with the active
rem console code page (936 on Chinese Windows), so non-ASCII text here would
rem render as mojibake or break parsing. Messages are therefore English.
rem ---------------------------------------------------------------------------

setlocal EnableExtensions
cd /d "%~dp0"

set "EXITCODE=0"
set "CONSOLE_OK=0"
set "SERVER_LOG=%~dp0logs\server.out.log"

if not exist ".venv\Scripts\python.exe" goto :no_venv

rem The fallback redirection needs logs\ before the command runs; the service
rem creates it during startup, which is already too late.
if not exist "logs" mkdir "logs"

".venv\Scripts\python.exe" "%~dp0disable_quick_edit.py" >nul 2>&1
if not errorlevel 1 set "CONSOLE_OK=1"

echo Starting Puresign service...
echo       URL: http://127.0.0.1:8008/
if "%CONSOLE_OK%"=="1" (
    echo       Log: this window
) else (
    echo       Log: %SERVER_LOG%
    echo       Note: no usable console, or QuickEdit could not be disabled, so the
    echo             service writes to the log file instead.
)
echo.
echo Keep this window open. Closing it stops the service.
echo.

if "%CONSOLE_OK%"=="1" goto :run_console

:run_file
rem Appended, not truncated: under Task Scheduler auto-restart, truncating would
rem discard the crash output of the run that triggered the restart.
echo.>>"%SERVER_LOG%"
echo ==== start %DATE% %TIME% ====>>"%SERVER_LOG%"
call ".venv\Scripts\activate.bat"
puresign-server >>"%SERVER_LOG%" 2>&1
set "EXITCODE=%ERRORLEVEL%"
goto :after_serve

:run_console
call ".venv\Scripts\activate.bat"
puresign-server
set "EXITCODE=%ERRORLEVEL%"
goto :after_serve

:after_serve
rem Capture before anything else touches ERRORLEVEL. Compared as a string rather
rem than with "if errorlevel 1", which is false for negative codes - and a
rem Windows crash reports exactly that (e.g. -1073741819 for 0xC0000005).
if not "%EXITCODE%"=="0" goto :server_failed

echo Service stopped.
goto :finish

rem --------------------------------- errors ---------------------------------

:no_venv
echo.
echo [ERROR] .venv not found next to this script.
echo         Run install.bat first.
set "EXITCODE=1"
goto :finish

:server_failed
echo.
echo [ERROR] The service exited with code %EXITCODE%.
rem In console mode the crash output is already on this window.
if "%CONSOLE_OK%"=="0" echo         See: %SERVER_LOG%
goto :finish

:finish
rem Pause on double-click so the window stays open long enough to read the
rem result. PowerShell also launches .bat files through "cmd /c", so CMDCMDLINE
rem cannot tell an interactive call from a double-click. For automation such as
rem Task Scheduler, set PURESIGN_NO_PAUSE=1 to skip the pause.
if defined PURESIGN_NO_PAUSE goto :done
echo.%CMDCMDLINE% | find /i "%~nx0" >nul && pause

:done
exit /b %EXITCODE%
