#!/bin/bash
set -e  # 若發生錯誤，立即停止

# 更新 pip
pip install --upgrade pip

# 安裝 Python 依賴
pip install -r requirements.txt

# 讓 start.sh 有執行權限 (Render 不能直接執行 chmod，所以改用這裡處理)
chmod +x start.sh
