#!/bin/bash
set -e  # 如果有錯誤，立即停止執行

# 更新 pip
pip install --upgrade pip

# 安裝 Python 依賴
pip install -r requirements.txt

# 安裝 Playwright 的 Chromium 瀏覽器
python -m playwright install chromium

# 啟動 Flask 應用
gunicorn -b 0.0.0.0:$PORT main:app
