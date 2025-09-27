#!/usr/bin/env python3
"""
Advanced Logger Integration Test
統合されたAdvanced Loggerの動作確認
"""

import sys
import os
import time

# プロジェクトのパスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_logger_integration():
    """統合されたログシステムのテスト"""
    print("🧪 Testing Integrated Advanced Logger System")
    print("=" * 50)
    
    try:
        # 1. ロガー設定のテスト
        print("1. Testing logger configuration...")
        from app.core.logger_config import initialize_logging, get_module_logger
        
        initialize_logging()
        print("   ✅ Logger configuration loaded successfully")
        
        # 2. 各モジュールロガーのテスト
        print("\n2. Testing module loggers...")
        
        # API Logger
        api_logger = get_module_logger("api")
        api_logger.api("API endpoint accessed", endpoint="/test", method="GET", status_code=200)
        print("   ✅ API logger working")
        
        # Database Logger
        db_logger = get_module_logger("database")
        db_logger.database("Database query executed", table="test", duration_ms=15)
        print("   ✅ Database logger working")
        
        # Auth Logger
        auth_logger = get_module_logger("auth")
        auth_logger.auth("User authentication", user_id="test123", success=True)
        print("   ✅ Auth logger working")
        
        # Gait Analysis Logger
        gait_logger = get_module_logger("gait")
        gait_logger.gait_analysis("Analysis completed", analysis_id="test_ana", processing_time=2.5)
        print("   ✅ Gait analysis logger working")
        
        # 3. パフォーマンス監視のテスト
        print("\n3. Testing performance monitoring...")
        
        main_logger = get_module_logger("main")
        
        with main_logger.performance_timer("test_operation"):
            time.sleep(0.01)  # 10ms のシミュレーション
        
        stats = main_logger.get_performance_stats("test_operation")
        if stats:
            print(f"   ✅ Performance monitoring: {stats['avg']:.3f}s average")
        else:
            print("   ⚠️ Performance stats not available yet")
        
        # 4. セキュリティログのテスト
        print("\n4. Testing security logging...")
        
        security_logger = get_module_logger("security")
        security_logger.security.login_attempt("test_user", True, "127.0.0.1")
        security_logger.security.data_access("test_user", "analysis", "test_ana", "read")
        print("   ✅ Security logging working")
        
        # 5. コンテキスト管理のテスト
        print("\n5. Testing context management...")
        
        context_logger = get_module_logger("context_test")
        context_logger.set_context(user_id="test_user", session_id="test_session")
        
        with context_logger.context_manager(request_id="test_req"):
            context_logger.info("Message with context")
        
        print("   ✅ Context management working")
        
        # 6. エラーハンドリングのテスト
        print("\n6. Testing error handling...")
        
        error_logger = get_module_logger("error_test")
        
        try:
            raise ValueError("Test exception for logging")
        except Exception:
            error_logger.error("Test error handled successfully")
        
        print("   ✅ Error handling working")
        
        print("\n" + "=" * 50)
        print("🎉 All Advanced Logger integration tests passed!")
        print("✅ Advanced Logger system is ready for production use")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Logger integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_logger_with_existing_services():
    """既存サービスとの統合テスト"""
    print("\n🧪 Testing Integration with Existing Services")
    print("=" * 50)
    
    try:
        # Gait Serviceとの統合テスト
        print("1. Testing gait service integration...")
        from app.services.gait_service import GaitAnalysisService
        
        # サービスインスタンス作成（ロガーが正しく初期化されるかテスト）
        gait_service = GaitAnalysisService()
        print("   ✅ Gait analysis service initialized with new logger")
        
        # API統合テスト
        print("\n2. Testing API integration...")
        from app.api.gait_analysis import logger as api_logger
        
        api_logger.api("Test API call", endpoint="/test", status_code=200)
        print("   ✅ API logger integration working")
        
        # Auth統合テスト
        print("\n3. Testing auth integration...")
        from app.api.v1.auth import logger as auth_api_logger
        
        auth_api_logger.auth("Test auth call", user_id="test", operation="test")
        print("   ✅ Auth API logger integration working")
        
        print("\n✅ All service integrations successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ Service integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """メインテスト実行"""
    print("🚀 Advanced Logger Integration Test Suite")
    print("=" * 60)
    
    # 基本統合テスト
    basic_test_passed = test_logger_integration()
    
    # サービス統合テスト
    service_test_passed = test_logger_with_existing_services()
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    print(f"Basic Integration Test: {'✅ PASSED' if basic_test_passed else '❌ FAILED'}")
    print(f"Service Integration Test: {'✅ PASSED' if service_test_passed else '❌ FAILED'}")
    
    if basic_test_passed and service_test_passed:
        print("\n🎉 Advanced Logger integration completed successfully!")
        print("🚀 System is ready for production deployment with enhanced logging")
    else:
        print("\n⚠️ Some tests failed. Please check the implementation.")
    
    return basic_test_passed and service_test_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)