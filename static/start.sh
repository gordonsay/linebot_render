#!/bin/bash
set -e  # 如果有錯誤，立即停止執行

# 更新 pip
pip install --upgrade pip

# 安裝 Python 依賴
pip install -r requirements.txt

# 安裝 Playwright 的 Chromium 瀏覽器
python -m playwright install chromium

# 啟動應用（請根據你的應用修改這行）
gunicorn -b 0.0.0.0:8000 main:app
