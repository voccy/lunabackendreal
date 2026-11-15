@echo off
setlocal
cd /d "%~dp0.."
echo Downloading official NASA NAIF SPICE kernels for LUNA Site01...
where py >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
  echo ERROR: Python launcher "py" was not found. Install Python 3.11+ first.
  exit /b 1
)
py scripts\download_spice_kernels.py
if %ERRORLEVEL% NEQ 0 (
  echo.
  echo DOWNLOAD INCOMPLETE: Please check your internet connection and retry.
  exit /b 1
)
echo.
echo Kernels downloaded. Run: py scripts\verify_spice.py
exit /b 0
