#!/usr/bin/env python3
"""
認証システムの基本テスト
"""

import asyncio
import sys
import os
from datetime import datetime

# プロジェクトのパスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.connection import db_manager, init_database
from app.services.user_service import user_service
from app.core.auth import auth_service
from app.models.user_models import UserCreate, UserLogin, Gender


def create_test_user() -> UserCreate:
    """テスト用ユーザーデータ作成"""
    return UserCreate(
        email="test@gaitanalysis.com",
        password="TestPassword123",
        full_name="テストユーザー",
        height_cm=170.0,
        weight_kg=65.0,
        age=30,
        gender=Gender.MALE
    )


async def test_database_initialization():
    """データベース初期化テスト"""
    print("🔧 Testing Database Initialization...")
    
    try:
        await init_database()
        
        # 接続確認
        health_status = db_manager.health_check()
        
        if health_status:
            print("✅ Database initialized and connection successful")
            return True
        else:
            print("❌ Database connection failed")
            return False
            
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False


async def test_user_registration():
    """ユーザー登録テスト"""
    print("🔧 Testing User Registration...")
    
    try:
        user_data = create_test_user()
        session = db_manager.get_session()
        
        try:
            user = await user_service.create_user(user_data, session)
            
            if user:
                print("✅ User registration successful")
                print(f"   - User ID: {user.id}")
                print(f"   - Email: {user.email}")
                print(f"   - Full Name: {user.full_name}")
                return True
            else:
                print("❌ User registration failed")
                return False
                
        finally:
            session.close()
            
    except Exception as e:
        print(f"❌ User registration failed: {e}")
        return False


async def test_user_authentication():
    """ユーザー認証テスト"""
    print("🔧 Testing User Authentication...")
    
    try:
        session = db_manager.get_session()
        
        try:
            # 正しい認証情報でテスト
            user = await user_service.authenticate_user(
                "test@gaitanalysis.com", 
                "TestPassword123", 
                session
            )
            
            if user:
                print("✅ User authentication successful")
                print(f"   - Authenticated user: {user.email}")
                
                # 間違ったパスワードでテスト
                wrong_user = await user_service.authenticate_user(
                    "test@gaitanalysis.com", 
                    "WrongPassword", 
                    session
                )
                
                if wrong_user is None:
                    print("✅ Wrong password correctly rejected")
                    return True
                else:
                    print("❌ Wrong password was accepted")
                    return False
            else:
                print("❌ User authentication failed")
                return False
                
        finally:
            session.close()
            
    except Exception as e:
        print(f"❌ User authentication failed: {e}")
        return False


async def test_jwt_token_operations():
    """JWTトークン操作テスト"""
    print("🔧 Testing JWT Token Operations...")
    
    try:
        # トークン作成
        token_data = {
            "user_id": "test-user-id",
            "email": "test@gaitanalysis.com",
            "user_type": "standard"
        }
        
        token = auth_service.create_access_token(token_data)
        print(f"✅ JWT token created: {token[:50]}...")
        
        # トークン検証
        decoded_data = auth_service.verify_token(token)
        
        if (decoded_data.user_id == token_data["user_id"] and 
            decoded_data.email == token_data["email"]):
            print("✅ JWT token verification successful")
            print(f"   - User ID: {decoded_data.user_id}")
            print(f"   - Email: {decoded_data.email}")
            print(f"   - Expires: {decoded_data.exp}")
            return True
        else:
            print("❌ JWT token verification failed")
            return False
            
    except Exception as e:
        print(f"❌ JWT token operations failed: {e}")
        return False


async def test_password_hashing():
    """パスワードハッシュ化テスト"""
    print("🔧 Testing Password Hashing...")
    
    try:
        password = "TestPassword123"
        
        # パスワードハッシュ化
        hashed = auth_service.hash_password(password)
        print(f"✅ Password hashed: {hashed[:50]}...")
        
        # パスワード検証
        is_valid = auth_service.verify_password(password, hashed)
        is_invalid = auth_service.verify_password("WrongPassword", hashed)
        
        if is_valid and not is_invalid:
            print("✅ Password verification successful")
            return True
        else:
            print("❌ Password verification failed")
            return False
            
    except Exception as e:
        print(f"❌ Password hashing failed: {e}")
        return False


async def test_user_service_operations():
    """ユーザーサービス操作テスト"""
    print("🔧 Testing User Service Operations...")
    
    try:
        session = db_manager.get_session()
        
        try:
            # ユーザー取得（メールアドレス）
            user = await user_service.get_user_by_email("test@gaitanalysis.com", session)
            
            if user:
                print("✅ Get user by email successful")
                
                # ユーザー取得（ID）
                user_by_id = await user_service.get_user_by_id(user.id, session)
                
                if user_by_id and user_by_id.id == user.id:
                    print("✅ Get user by ID successful")
                    
                    # ユーザー統計取得
                    stats = await user_service.get_user_stats(user.id, session)
                    
                    if stats:
                        print("✅ Get user stats successful")
                        print(f"   - Total analyses: {stats.total_analyses}")
                        print(f"   - Account age: {stats.account_created_days} days")
                        return True
                    else:
                        print("❌ Get user stats failed")
                        return False
                else:
                    print("❌ Get user by ID failed")
                    return False
            else:
                print("❌ Get user by email failed")
                return False
                
        finally:
            session.close()
            
    except Exception as e:
        print(f"❌ User service operations failed: {e}")
        return False


async def run_all_tests():
    """全テスト実行"""
    print("🚀 Starting Authentication System Tests\n")
    
    tests = [
        ("Database Initialization", test_database_initialization),
        ("User Registration", test_user_registration),
        ("User Authentication", test_user_authentication),
        ("JWT Token Operations", test_jwt_token_operations),
        ("Password Hashing", test_password_hashing),
        ("User Service Operations", test_user_service_operations),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        result = await test_func()
        results.append((test_name, result))
    
    print("\n" + "="*60)
    print("📊 Authentication System Test Results")
    print("="*60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nTotal: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All authentication tests passed!")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
    
    return passed == len(results)


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)