@echo off
setlocal
cd /d "%~dp0.."
if not exist "science_api\kernels\de421.bsp" (
  echo ERROR: Required DE421 kernel missing. See KERNEL_INSTALL_STATUS.md.
  exit /b 1
)
echo Starting LUNA Python science service on http://127.0.0.1:8000
python -m uvicorn main:app --app-dir science_api --host 127.0.0.1 --port 8000
