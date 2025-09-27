#!/bin/bash

# MediaPipe歩行分析API - 依存関係インストールスクリプト

echo "🚀 Installing MediaPipe Gait Analysis API dependencies..."

# 仮想環境をアクティベート
source venv/bin/activate

# pipのアップグレード
echo "📦 Upgrading pip..."
pip install --upgrade pip

# 依存関係のインストール
echo "📥 Installing dependencies..."
pip install -r requirements.txt

echo "✅ Dependencies installed successfully!"

# インストール確認
echo "🔍 Verifying installation..."
python -c "
try:
    import fastapi
    import mediapipe as mp
    import cv2
    import numpy as np
    from pydantic_settings import BaseSettings
    print('✅ All main packages imported successfully!')
    print(f'FastAPI version: {fastapi.__version__}')
    print(f'MediaPipe version: {mp.__version__}')
except Exception as e:
    print(f'❌ Import error: {e}')
"

echo "🎉 Setup complete! You can now run the server with:"
echo "source venv/bin/activate && python main.py"