@echo off
chcp 65001 >nul
title 家庭理财手机共享服务

echo ========================================
echo   家庭理财手机共享 · 启动中
echo ========================================
echo.

REM 获取本机 IP
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4"') do (
    set "LOCAL_IP=%%a"
    goto :got_ip
)
:got_ip
set "LOCAL_IP=%LOCAL_IP: =%"

echo 电脑访问：http://localhost:8000
echo 手机访问：http://%LOCAL_IP%:8000
echo.
echo 【让手机能用】
echo   1. 电脑和手机连同一个 Wi-Fi
echo   2. 手机浏览器输入上面的"手机访问"地址
echo   3. 如果打不开，关闭电脑防火墙再试
echo.
echo 【提示】这只是临时方案
echo   长期使用请按 README 部署到腾讯云 CloudBase
echo   部署后所有家人都能直接扫码打开
echo.
echo 按 Ctrl+C 可停止服务
echo ========================================
echo.

REM 切换到本脚本所在目录
cd /d "%~dp0"

REM 启动 Python 自带 HTTP 服务（如果电脑装了 Python）
where python >nul 2>nul
if %errorlevel% equ 0 (
    echo [使用 Python 启动]
    python -m http.server 8000
    goto :end
)

REM 用 PowerShell 的简易 HTTP 服务
where powershell >nul 2>nul
if %errorlevel% equ 0 (
    echo [使用 PowerShell 启动]
    powershell -Command "$H=New-Object Net.HttpListener; $H.Prefixes.Add('http://+:8000/'); $H.Start(); Write-Host '已启动，访问 http://%LOCAL_IP%:8000'; while($H.IsListening){$C=$H.GetContext(); $P=Join-Path (Get-Location) ($C.Request.Url.LocalPath.TrimStart('/')); if(Test-Path $P -PathType Leaf){$B=[IO.File]::ReadAllBytes($P); $C.Response.ContentLength64=$B.Length; $C.Response.OutputStream.Write($B,0,$B.Length)} else {$C.Response.StatusCode=404}; $C.Response.Close()}"
    goto :end
)

echo [错误] 未检测到 Python 或 PowerShell
echo 请安装 Python 3 后再试：https://www.python.org/downloads/
pause
:end
