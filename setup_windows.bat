@echo off
REM ==============================================================
REM Windows 一键环境配置脚本
REM 适用于：Windows 10/11 + Python 3.10+
REM 项目：中远海运散货 AI Agent「散运助手」
REM ==============================================================

echo 🚀 正在为Windows配置Python虚拟环境...
echo ========================================
echo.

REM 检查 Python 是否已安装
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ❌ 未检测到 python，请先安装 Python 3.10+
    echo    https://www.python.org/downloads/
    echo    ⚠️ 安装时务必勾选 "Add Python to PATH"
    pause
    exit /b 1
)

python --version
echo ✅ Python 已检测到
echo.

REM 创建虚拟环境
echo 📦 正在创建虚拟环境 venv\ ...
python -m venv venv
echo ✅ 虚拟环境创建完成
echo.

REM 激活虚拟环境（Windows 路径）
echo 🔌 正在激活虚拟环境...
call venv\Scripts\activate.bat
echo ✅ 虚拟环境已激活
echo.

REM 升级 pip
echo ⬆️  正在升级 pip...
python -m pip install --upgrade pip --quiet
echo ✅ pip 已升级到最新版本
echo.

REM 安装依赖
echo 📥 正在安装项目依赖...
pip install -r requirements.txt --quiet
echo ✅ 所有依赖安装完成
echo.

echo ========================================
echo ✅ 环境配置完成！
echo.
echo 📋 下一步操作：
echo    1. 确认虚拟环境已激活: venv\Scripts\activate.bat
echo    2. 创建 .env 文件并配置 API Key:
echo       copy .env.example .env
echo       notepad .env    （填入你的 DEEPSEEK_API_KEY）
echo    3. 启动应用: streamlit run app.py
echo.
echo 🌐 启动后浏览器访问: http://localhost:8501
echo ========================================
pause
