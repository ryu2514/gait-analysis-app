#!/usr/bin/env python3
"""
Performance Optimization Test Script
パフォーマンス最適化テストスクリプト
"""

import asyncio
import time
import sys
import os
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.performance_config import (
    cache_manager, 
    performance_monitor, 
    task_queue, 
    PerformanceConfig,
    init_performance_systems
)
from app.core.advanced_logger import get_logger
from app.services.optimized_video_service import optimized_video_processor

logger = get_logger("performance_test")


async def test_cache_system():
    """キャッシュシステムのテスト"""
    logger.info("Testing cache system...")
    
    # テストデータ
    test_key = "test_key"
    test_value = {"data": "test_value", "timestamp": time.time()}
    
    # Set test
    await cache_manager.set(test_key, test_value, ttl=60)
    
    # Get test
    retrieved_value = await cache_manager.get(test_key)
    
    if retrieved_value == test_value:
        logger.info("Cache system test: PASSED")
        return True
    else:
        logger.error("Cache system test: FAILED")
        return False


async def test_performance_monitor():
    """パフォーマンス監視システムのテスト"""
    logger.info("Testing performance monitor...")
    
    # メトリクス記録テスト
    test_metrics = [
        ("cpu_usage_percent", 45.5),
        ("memory_usage_mb", 1024.0),
        ("response_time_ms", 250.0),
        ("api_requests_per_second", 100.0)
    ]
    
    for metric_name, value in test_metrics:
        performance_monitor.record_metric(metric_name, value, {"test": "true"})
    
    # 要約取得テスト
    summary = performance_monitor.get_metrics_summary("cpu_usage_percent")
    
    if summary and "avg" in summary:
        logger.info("Performance monitor test: PASSED")
        return True
    else:
        logger.error("Performance monitor test: FAILED")
        return False


async def test_task_queue():
    """タスクキューのテスト"""
    logger.info("Testing task queue...")
    
    # ワーカー開始
    await task_queue.start_workers()
    
    # テストタスク
    def test_task(task_id):
        logger.debug(f"Processing test task {task_id}")
        time.sleep(0.1)  # 短い処理時間をシミュレート
        return f"Task {task_id} completed"
    
    # タスクを追加
    for i in range(5):
        await task_queue.add_task(test_task, i)
    
    # 処理完了を待機
    await asyncio.sleep(1)
    
    # 統計確認
    stats = task_queue.get_stats()
    
    # ワーカー停止
    await task_queue.stop_workers()
    
    if stats["tasks_processed"] >= 5:
        logger.info("Task queue test: PASSED")
        return True
    else:
        logger.error("Task queue test: FAILED")
        return False


def test_optimization_config():
    """最適化設定のテスト"""
    logger.info("Testing optimization configuration...")
    
    try:
        # 最適化設定取得
        optimized_settings = PerformanceConfig.get_optimized_settings()
        
        # 設定項目確認
        required_sections = ["mediapipe", "video_processing", "database", "api", "memory"]
        
        for section in required_sections:
            if section not in optimized_settings:
                logger.error(f"Missing optimization section: {section}")
                return False
        
        logger.info("Optimization configuration test: PASSED")
        return True
        
    except Exception as e:
        logger.error(f"Optimization configuration test: FAILED - {e}")
        return False


def test_video_processor():
    """動画プロセッサーのテスト"""
    logger.info("Testing video processor...")
    
    try:
        # 統計取得テスト
        stats = optimized_video_processor.get_optimization_stats()
        
        if isinstance(stats, dict) and "performance_metrics" in stats:
            logger.info("Video processor test: PASSED")
            return True
        else:
            logger.error("Video processor test: FAILED - Invalid stats format")
            return False
            
    except Exception as e:
        logger.error(f"Video processor test: FAILED - {e}")
        return False


async def run_performance_tests():
    """パフォーマンステスト実行"""
    logger.info("🚀 Starting performance optimization tests...")
    
    test_results = {
        "cache_system": False,
        "performance_monitor": False,
        "task_queue": False,
        "optimization_config": False,
        "video_processor": False
    }
    
    try:
        # キャッシュシステムテスト
        test_results["cache_system"] = await test_cache_system()
        
        # パフォーマンス監視テスト
        test_results["performance_monitor"] = await test_performance_monitor()
        
        # タスクキューテスト
        test_results["task_queue"] = await test_task_queue()
        
        # 最適化設定テスト
        test_results["optimization_config"] = test_optimization_config()
        
        # 動画プロセッサーテスト
        test_results["video_processor"] = test_video_processor()
        
    except Exception as e:
        logger.error(f"Test execution failed: {e}")
    
    # 結果集計
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    logger.info("📊 Performance Test Results:")
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"  {test_name}: {status}")
    
    logger.info(f"Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        logger.info("🎉 All performance optimization tests passed!")
        return True
    else:
        logger.warning(f"⚠️  {total_tests - passed_tests} tests failed")
        return False


def main():
    """メイン実行"""
    try:
        # パフォーマンステスト実行
        success = asyncio.run(run_performance_tests())
        
        if success:
            print("\n✅ Performance optimization system is ready!")
            print("   - Cache system operational")
            print("   - Performance monitoring active")
            print("   - Task queue functional")
            print("   - Optimization settings applied")
            print("   - Video processing optimized")
            
            # 統計表示
            print("\n📈 Current System Stats:")
            cache_stats = cache_manager.get_stats()
            print(f"   Cache hit rate: {cache_stats.get('hit_rate_percent', 0):.1f}%")
            print(f"   Local cache size: {cache_stats.get('local_cache_size', 0)}")
            print(f"   Redis available: {cache_stats.get('redis_available', False)}")
            
        else:
            print("\n❌ Performance optimization system has issues!")
            print("   Please check the logs for details.")
            
    except Exception as e:
        logger.error(f"Performance test execution failed: {e}")
        print(f"\n💥 Test execution failed: {e}")


if __name__ == "__main__":
    main()