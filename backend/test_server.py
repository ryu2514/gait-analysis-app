"""
バックエンドサーバーのテストスクリプト
"""

import asyncio
import httpx
import os
import sys

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import app
import uvicorn
from multiprocessing import Process
import time


async def test_health_endpoint():
    """ヘルスチェックエンドポイントのテスト"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8000/api/v1/health")
            print(f"Health Check Status: {response.status_code}")
            print(f"Response: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"Health check failed: {e}")
            return False


async def test_supported_formats():
    """サポートフォーマットエンドポイントのテスト"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8000/api/v1/gait-analysis/supported-formats")
            print(f"Supported Formats Status: {response.status_code}")
            print(f"Response: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"Supported formats test failed: {e}")
            return False


async def test_root_endpoint():
    """ルートエンドポイントのテスト"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8000/")
            print(f"Root Endpoint Status: {response.status_code}")
            print(f"Response: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"Root endpoint test failed: {e}")
            return False


def run_server():
    """テスト用サーバー起動"""
    uvicorn.run(app, host="localhost", port=8000, log_level="info")


async def run_tests():
    """全テストの実行"""
    print("🚀 Starting backend API tests...")
    
    # サーバー起動待機（最大60秒リトライ）
    print("⏳ Waiting for server to start...")
    ready = False
    for i in range(60):
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get("http://localhost:8000/")
                if r.status_code == 200:
                    ready = True
                    break
        except Exception:
            pass
        await asyncio.sleep(1)
    if not ready:
        print("❌ Server did not become ready within timeout")
    
    tests = [
        ("Root Endpoint", test_root_endpoint),
        ("Health Check", test_health_endpoint), 
        ("Supported Formats", test_supported_formats),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        result = await test_func()
        results.append((test_name, result))
        print(f"✅ {test_name}: {'PASSED' if result else 'FAILED'}")
    
    print("\n📊 Test Results Summary:")
    print("-" * 30)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Check the logs above.")
    
    return passed == total


if __name__ == "__main__":
    import multiprocessing
    
    # サーバープロセスを起動
    server_process = Process(target=run_server)
    server_process.start()
    
    try:
        # テスト実行
        result = asyncio.run(run_tests())
        
        # 結果に応じて終了コード設定
        exit_code = 0 if result else 1
        
    finally:
        # サーバープロセス終了
        server_process.terminate()
        server_process.join()
        
    sys.exit(exit_code)
