@echo off
rem ---------------------------------------------------------------------------
rem Puresign offline installer for Windows.
rem
rem Run from cmd.exe:     install.bat
rem Run from PowerShell:  .\install.bat
rem Or double-click this file in Explorer.
rem
rem Written as a batch file on purpose: batch is not subject to ExecutionPolicy.
rem Group Policy can lock the MachinePolicy scope, and -ExecutionPolicy Bypass
rem cannot override that scope, so a PowerShell installer can be blocked
rem outright on a locked-down domain machine.
rem
rem Kept ASCII-only on purpose: cmd.exe decodes .bat files with the active
rem console code page (936 on Chinese Windows), so non-ASCII text here would
rem render as mojibake or break parsing. Messages are therefore English.
rem ---------------------------------------------------------------------------

setlocal EnableExtensions
cd /d "%~dp0"

set "EXITCODE=0"
set "VENV_DIR=%~dp0.venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "WHEELHOUSE=%~dp0wheelhouse"

echo [1/4] Checking Python...

where python.exe >nul 2>nul
if errorlevel 1 goto :no_python

rem usebackq lets the Python snippet use single quotes without escaping.
for /f "usebackq delims=" %%V in (`python -c "import sys,struct;print(sys.version.split()[0], str(8*struct.calcsize('P'))+'-bit')"`) do set "PYINFO=%%V"
if not defined PYINFO goto :no_python

rem Ask Python itself rather than parsing localized "python --version" output.
python -c "import sys,struct;sys.exit(0 if sys.version_info[:2]==(3,11) and struct.calcsize('P')==8 else 1)" >nul 2>nul
if errorlevel 1 goto :bad_python

echo       Found Python %PYINFO%

echo [2/4] Locating offline package...

set "WHEEL="
for %%F in ("%~dp0puresign-*.whl") do set "WHEEL=%%~fF"
if not defined WHEEL goto :no_wheel
if not exist "%WHEELHOUSE%" goto :no_wheelhouse

for %%F in ("%WHEEL%") do echo       Package: %%~nxF

echo [3/4] Creating virtual environment...

if exist "%VENV_PYTHON%" goto :venv_ready
python -m venv "%VENV_DIR%"
if errorlevel 1 goto :venv_failed
if not exist "%VENV_PYTHON%" goto :venv_failed

:venv_ready
"%VENV_PYTHON%" -c "import sys;sys.exit(0 if sys.version_info[:2]==(3,11) else 1)" >nul 2>nul
if errorlevel 1 goto :bad_venv
echo       Ready: .venv

echo [4/4] Installing from local wheelhouse (no network access)...

"%VENV_PYTHON%" -m pip install --disable-pip-version-check --no-index --find-links "%WHEELHOUSE%" "%WHEEL%"
if errorlevel 1 goto :install_failed

echo.
echo Install complete. Run start.bat to launch the Puresign service.
echo Service URL: http://localhost:8008/
goto :finish

rem --------------------------------- errors ---------------------------------

:no_python
echo.
echo [ERROR] python.exe not found on PATH.
echo         Install 64-bit Python 3.11 and enable "Add python.exe to PATH".
set "EXITCODE=1"
goto :finish

:bad_python
echo.
echo [ERROR] This offline bundle is built for 64-bit Python 3.11.
echo         Detected: %PYINFO%
set "EXITCODE=1"
goto :finish

:no_wheel
echo.
echo [ERROR] No puresign-*.whl found next to this script.
echo         Extract the full offline ZIP and run it from that folder.
set "EXITCODE=1"
goto :finish

:no_wheelhouse
echo.
echo [ERROR] wheelhouse folder not found next to this script.
echo         Extract the full offline ZIP and run it from that folder.
set "EXITCODE=1"
goto :finish

:venv_failed
echo.
echo [ERROR] Failed to create the virtual environment at .venv
set "EXITCODE=1"
goto :finish

:bad_venv
echo.
echo [ERROR] Existing .venv is not Python 3.11. Delete it and run this again.
set "EXITCODE=1"
goto :finish

:install_failed
echo.
echo [ERROR] pip install failed. See the output above.
echo         A missing dependency usually means the wheelhouse folder is incomplete.
set "EXITCODE=1"
goto :finish

:finish
rem Pause on double-click so the window stays open long enough to read the
rem result. PowerShell also launches .bat files through "cmd /c", so CMDCMDLINE
rem cannot tell an interactive call from a double-click. For automation, set
rem PURESIGN_NO_PAUSE=1 before calling to skip the pause.
if defined PURESIGN_NO_PAUSE goto :done
echo.%CMDCMDLINE% | find /i "%~nx0" >nul && pause

:done
exit /b %EXITCODE%
