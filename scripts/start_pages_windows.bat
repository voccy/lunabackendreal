@echo off
setlocal
cd /d "%~dp0.."
where node >nul 2>nul
if errorlevel 1 (
 echo Node.js is required. Install from https://nodejs.org/
 exit /b 1
)
node scripts\build_pages.mjs
if errorlevel 1 exit /b 1
echo Starting Cloudflare Pages local preview. Run scripts\start_science_windows.bat in another terminal.
echo For local API proxy set LUNA_SCIENCE_API_URL=http://127.0.0.1:8000 in .dev.vars
npx wrangler pages dev public
