#!/usr/bin/env python3
"""
Advanced Logger テストスクリプト
高機能ログシステムの動作確認
"""

import sys
import os
import time
import threading
from datetime import datetime

# プロジェクトのパスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.advanced_logger import (
    AdvancedLogger, get_logger, setup_advanced_logging,
    LogLevel, LogCategory, set_global_context, clear_global_context
)


def test_basic_logging():
    """基本ログ機能のテスト"""
    print("🧪 Testing Basic Logging...")
    
    logger = get_logger("test_basic")
    
    # 基本ログレベル
    logger.trace("Trace level message")
    logger.debug("Debug level message")
    logger.info("Info level message")
    logger.warning("Warning level message")
    logger.error("Error level message")
    logger.critical("Critical level message")
    
    print("✅ Basic logging test completed")


def test_contextual_logging():
    """コンテキストログ機能のテスト"""
    print("🧪 Testing Contextual Logging...")
    
    logger = get_logger("test_context")
    
    # グローバルコンテキスト設定
    set_global_context(
        user_id="test_user_123",
        session_id="session_abc",
        request_id="req_xyz"
    )
    
    logger.info("Message with global context")
    
    # 一時的なコンテキスト
    with logger.context_manager(analysis_id="analysis_456", ip_address="192.168.1.100"):
        logger.info("Message with temporary context")
        logger.auth("Authentication attempt", success=True, method="jwt")
    
    logger.info("Message after context manager")
    
    clear_global_context()
    print("✅ Contextual logging test completed")


def test_category_logging():
    """カテゴリ別ログ機能のテスト"""
    print("🧪 Testing Category Logging...")
    
    logger = get_logger("test_category")
    
    # API関連ログ
    logger.api("API request received", endpoint="/gait/analyze", method="POST", status_code=200)
    
    # データベース関連ログ
    logger.database("Database query executed", table="users", operation="SELECT", duration_ms=25)
    
    # 認証関連ログ
    logger.auth("User login", user_id="user123", success=True, ip_address="192.168.1.50")
    
    # 歩行分析関連ログ
    logger.gait_analysis("Analysis started", video_duration=5.2, analysis_mode="detailed")
    
    # MediaPipe関連ログ
    logger.mediapipe("Pose detection completed", confidence=0.92, landmarks_detected=33)
    
    # レポート関連ログ
    logger.report("PDF report generated", analysis_id="ana_123", file_size_kb=245)
    
    # ユーザーアクション
    logger.user_action("Video uploaded", filename="gait_test.mp4", file_size_mb=15.5)
    
    print("✅ Category logging test completed")


def test_security_logging():
    """セキュリティログ機能のテスト"""
    print("🧪 Testing Security Logging...")
    
    logger = get_logger("test_security")
    
    # ログイン試行
    logger.security.login_attempt("user123", True, "192.168.1.100")
    logger.security.login_attempt("user456", False, "10.0.0.1")
    
    # 権限拒否
    logger.security.permission_denied("user789", "admin_panel", "access")
    
    # データアクセス
    logger.security.data_access("user123", "gait_analysis", "analysis_456", "read")
    logger.security.data_access("user123", "user_profile", "profile_789", "update")
    
    # 疑わしい活動
    logger.security.suspicious_activity(
        "Multiple failed login attempts",
        user_id="user999",
        ip_address="203.0.113.1",
        attempt_count=5,
        time_window_minutes=5
    )
    
    print("✅ Security logging test completed")


def test_performance_monitoring():
    """パフォーマンス監視機能のテスト"""
    print("🧪 Testing Performance Monitoring...")
    
    logger = get_logger("test_performance")
    
    # コンテキストマネージャによる測定
    with logger.performance_timer("database_query"):
        time.sleep(0.05)  # 50ms のシミュレーション
    
    with logger.performance_timer("gait_analysis"):
        time.sleep(0.1)   # 100ms のシミュレーション
    
    with logger.performance_timer("report_generation"):
        time.sleep(0.02)  # 20ms のシミュレーション
    
    # 統計情報取得
    stats = logger.get_performance_stats()
    print("📊 Performance Statistics:")
    for operation, stat in stats.items():
        if stat:
            print(f"   {operation}: avg={stat['avg']:.3f}s, count={stat['count']}")
    
    print("✅ Performance monitoring test completed")


def test_performance_decorator():
    """パフォーマンスデコレータのテスト"""
    print("🧪 Testing Performance Decorator...")
    
    logger = get_logger("test_decorator")
    
    @logger.performance_decorator("custom_operation")
    def slow_operation():
        """時間のかかる処理のシミュレーション"""
        time.sleep(0.03)
        return "operation completed"
    
    @logger.exception_handler
    def risky_operation():
        """例外が発生する可能性のある処理"""
        import random
        if random.random() < 0.3:  # 30%の確率で例外
            raise ValueError("Random error occurred")
        return "success"
    
    # パフォーマンステスト
    result = slow_operation()
    logger.info(f"Slow operation result: {result}")
    
    # 例外ハンドリングテスト
    try:
        for i in range(5):
            try:
                result = risky_operation()
                logger.info(f"Risky operation {i+1} result: {result}")
            except ValueError:
                logger.info(f"Risky operation {i+1} failed as expected")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    
    print("✅ Performance decorator test completed")


def test_concurrent_logging():
    """並行ログ処理のテスト"""
    print("🧪 Testing Concurrent Logging...")
    
    logger = get_logger("test_concurrent")
    
    def worker_thread(thread_id: int):
        """ワーカースレッド"""
        logger.set_context(thread_id=thread_id)
        
        for i in range(10):
            logger.info(f"Thread {thread_id} - Message {i+1}")
            time.sleep(0.001)  # 1ms 待機
    
    # 5つの並行スレッドを開始
    threads = []
    for i in range(5):
        thread = threading.Thread(target=worker_thread, args=(i+1,))
        threads.append(thread)
        thread.start()
    
    # すべてのスレッドの完了を待機
    for thread in threads:
        thread.join()
    
    logger.info("All concurrent threads completed")
    print("✅ Concurrent logging test completed")


def test_exception_logging():
    """例外ログ機能のテスト"""
    print("🧪 Testing Exception Logging...")
    
    logger = get_logger("test_exception")
    
    try:
        # 意図的にエラーを発生
        raise ValueError("This is a test exception")
    except Exception as e:
        logger.error("Exception occurred during test", exception=str(e))
    
    try:
        # ゼロ除算エラー
        result = 10 / 0
    except ZeroDivisionError:
        logger.error("Division by zero error")
    
    try:
        # ファイル読み込みエラー
        with open("nonexistent_file.txt", "r") as f:
            content = f.read()
    except FileNotFoundError:
        logger.error("File not found error")
    
    print("✅ Exception logging test completed")


def test_audit_logging():
    """監査ログ機能のテスト"""
    print("🧪 Testing Audit Logging...")
    
    logger = get_logger("test_audit")
    
    # 監査イベント
    logger.audit("User created", user_id="new_user_123", created_by="admin", timestamp=datetime.now())
    logger.audit("Analysis data exported", analysis_id="ana_456", exported_by="user_789", format="PDF")
    logger.audit("System configuration changed", setting="max_upload_size", old_value="100MB", new_value="200MB")
    logger.audit("User permission updated", user_id="user_123", permission="admin", granted_by="super_admin")
    
    print("✅ Audit logging test completed")


def test_log_filtering():
    """ログフィルタリング機能のテスト"""
    print("🧪 Testing Log Filtering...")
    
    logger = get_logger("test_filter")
    
    # フィルタ関数を追加
    def sensitive_data_filter(log_entry):
        """機密データを含むログをフィルタ"""
        sensitive_keywords = ["password", "secret", "token"]
        message_lower = log_entry.message.lower()
        return not any(keyword in message_lower for keyword in sensitive_keywords)
    
    logger.filter.add_filter(sensitive_data_filter)
    
    # テストメッセージ
    logger.info("Normal log message")  # 表示される
    logger.info("User password updated")  # フィルタされる
    logger.info("Secret key rotated")  # フィルタされる
    logger.info("Authentication token generated")  # フィルタされる
    logger.info("User profile updated")  # 表示される
    
    print("✅ Log filtering test completed")


def run_comprehensive_test():
    """包括的なテスト実行"""
    print("🚀 Starting Advanced Logger Comprehensive Test\n")
    
    # ログシステム初期化
    setup_advanced_logging()
    
    # 各テストを実行
    test_basic_logging()
    print()
    
    test_contextual_logging()
    print()
    
    test_category_logging()
    print()
    
    test_security_logging()
    print()
    
    test_performance_monitoring()
    print()
    
    test_performance_decorator()
    print()
    
    test_concurrent_logging()
    print()
    
    test_exception_logging()
    print()
    
    test_audit_logging()
    print()
    
    test_log_filtering()
    print()
    
    print("=" * 60)
    print("📊 Advanced Logger Test Results")
    print("=" * 60)
    
    # 統計情報表示
    main_logger = get_logger()
    all_stats = main_logger.get_performance_stats()
    
    if all_stats:
        print("Performance Statistics:")
        for operation, stats in all_stats.items():
            if stats:
                print(f"  {operation}:")
                print(f"    Count: {stats['count']}")
                print(f"    Average: {stats['avg']:.3f}s")
                print(f"    Min: {stats['min']:.3f}s")
                print(f"    Max: {stats['max']:.3f}s")
                print(f"    P95: {stats['p95']:.3f}s")
                print()
    
    print("🎉 All Advanced Logger tests completed successfully!")
    
    # ログシステムをシャットダウン
    main_logger.shutdown()


if __name__ == "__main__":
    run_comprehensive_test()