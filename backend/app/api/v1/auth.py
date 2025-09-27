"""
認証関連APIエンドポイント
"""

from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.auth import auth_service, get_current_user, get_current_active_user, TokenData
from app.core.config import settings
from app.database.connection import get_database_session
from app.services.user_service import user_service
from app.models.user_models import (
    UserCreate, UserLogin, UserResponse, TokenResponse, 
    PasswordReset, PasswordResetConfirm, UserUpdate, UserStats
)
from app.core.advanced_logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["認証"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_database_session)
):
    """
    新規ユーザー登録
    
    Args:
        user_data: ユーザー登録データ
        request: HTTPリクエスト
        db: データベースセッション
        
    Returns:
        TokenResponse: 認証トークンとユーザー情報
    """
    try:
        # ユーザー作成
        user = await user_service.create_user(user_data, db)
        
        # アクセストークン生成
        access_token = auth_service.create_user_token(
            user_id=user.id,
            email=user.email,
            user_type=user.user_type.value
        )
        
        # ログイン履歴記録
        await user_service.log_login(
            user_id=user.id,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent", ""),
            login_method="registration",
            success=True,
            db=db
        )
        
        logger.info("User registered successfully", user_id=user.id, email=user.email)
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=int(settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60),
            user=user
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Registration failed", error=str(e), email=user_data.email)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登録処理でエラーが発生しました"
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    user_data: UserLogin,
    request: Request,
    db: Session = Depends(get_database_session)
):
    """
    ユーザーログイン
    
    Args:
        user_data: ログインデータ
        request: HTTPリクエスト
        db: データベースセッション
        
    Returns:
        TokenResponse: 認証トークンとユーザー情報
    """
    try:
        # ユーザー認証
        user = await user_service.authenticate_user(user_data.email, user_data.password, db)
        
        if not user:
            # ログイン失敗記録
            temp_user = await user_service.get_user_by_email(user_data.email, db)
            if temp_user:
                await user_service.log_login(
                    user_id=temp_user.id,
                    ip_address=request.client.host,
                    user_agent=request.headers.get("user-agent", ""),
                    login_method="password",
                    success=False,
                    failure_reason="invalid_credentials",
                    db=db
                )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="メールアドレスまたはパスワードが間違っています"
            )
        
        # アクセストークン生成
        access_token = auth_service.create_user_token(
            user_id=user.id,
            email=user.email,
            user_type=user.user_type.value
        )
        
        # ログイン成功記録
        await user_service.log_login(
            user_id=user.id,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent", ""),
            login_method="password",
            success=True,
            db=db
        )
        
        logger.info("User logged in successfully", user_id=user.id, email=user.email)
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=int(settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60),
            user=user
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Login failed", error=str(e), email=user_data.email)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ログイン処理でエラーが発生しました"
        )


@router.post("/firebase", response_model=TokenResponse)
async def firebase_login(
    firebase_token: HTTPAuthorizationCredentials,
    request: Request,
    db: Session = Depends(get_database_session)
):
    """
    Firebase認証ログイン
    
    Args:
        firebase_token: FirebaseIDトークン
        request: HTTPリクエスト
        db: データベースセッション
        
    Returns:
        TokenResponse: 認証トークンとユーザー情報
    """
    try:
        # Firebase IDトークン検証
        firebase_user = auth_service.verify_firebase_token(firebase_token.credentials)
        
        # ユーザー取得または作成
        user = await user_service.create_firebase_user(
            firebase_uid=firebase_user["uid"],
            email=firebase_user.get("email", ""),
            full_name=firebase_user.get("name", "Firebase User"),
            db=db
        )
        
        # アクセストークン生成
        access_token = auth_service.create_user_token(
            user_id=user.id,
            email=user.email,
            user_type=user.user_type.value
        )
        
        # ログイン履歴記録
        await user_service.log_login(
            user_id=user.id,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent", ""),
            login_method="firebase",
            success=True,
            db=db
        )
        
        logger.info("Firebase user logged in", user_id=user.id, firebase_uid=firebase_user["uid"])
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=int(settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60),
            user=user
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Firebase login failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Firebase認証でエラーが発生しました"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_database_session)
):
    """
    現在のユーザー情報取得
    
    Args:
        current_user: 現在のユーザー（認証情報）
        db: データベースセッション
        
    Returns:
        UserResponse: ユーザー情報
    """
    try:
        user = await user_service.get_user_by_id(current_user.user_id, db)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザーが見つかりません"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get current user", error=str(e), user_id=current_user.user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ユーザー情報取得でエラーが発生しました"
        )


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_database_session)
):
    """
    現在のユーザー情報更新
    
    Args:
        user_data: 更新データ
        current_user: 現在のユーザー（認証情報）
        db: データベースセッション
        
    Returns:
        UserResponse: 更新後のユーザー情報
    """
    try:
        user = await user_service.update_user(current_user.user_id, user_data, db)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ユーザーが見つかりません"
            )
        
        logger.info("User updated", user_id=current_user.user_id)
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update user", error=str(e), user_id=current_user.user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ユーザー情報更新でエラーが発生しました"
        )


@router.get("/stats", response_model=UserStats)
async def get_user_statistics(
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_database_session)
):
    """
    ユーザー統計情報取得
    
    Args:
        current_user: 現在のユーザー（認証情報）
        db: データベースセッション
        
    Returns:
        UserStats: ユーザー統計情報
    """
    try:
        stats = await user_service.get_user_stats(current_user.user_id, db)
        return stats
        
    except Exception as e:
        logger.error("Failed to get user stats", error=str(e), user_id=current_user.user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="統計情報取得でエラーが発生しました"
        )


@router.post("/verify-token")
async def verify_token(current_user: TokenData = Depends(get_current_user)):
    """
    トークン検証
    
    Args:
        current_user: 現在のユーザー（認証情報）
        
    Returns:
        dict: トークン検証結果
    """
    return {
        "valid": True,
        "user_id": current_user.user_id,
        "email": current_user.email,
        "user_type": current_user.user_type,
        "expires_at": current_user.exp
    }


@router.post("/password/reset")
async def request_password_reset(
    reset_data: PasswordReset,
    db: Session = Depends(get_database_session)
):
    """
    パスワードリセット要求
    
    Args:
        reset_data: パスワードリセットデータ
        db: データベースセッション
        
    Returns:
        dict: リセット要求結果
    """
    try:
        # ユーザー存在確認
        user = await user_service.get_user_by_email(reset_data.email, db)
        
        if not user:
            # セキュリティのため、存在しないメールアドレスでも成功として返す
            return {"message": "パスワードリセットメールを送信しました"}
        
        # TODO: パスワードリセットトークン生成とメール送信
        logger.info("Password reset requested", email=reset_data.email)
        
        return {"message": "パスワードリセットメールを送信しました"}
        
    except Exception as e:
        logger.error("Password reset request failed", error=str(e), email=reset_data.email)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="パスワードリセット要求でエラーが発生しました"
        )


@router.get("/login-history")
async def get_login_history(
    limit: int = 10,
    current_user: TokenData = Depends(get_current_active_user),
    db: Session = Depends(get_database_session)
):
    """
    ログイン履歴取得
    
    Args:
        limit: 取得件数
        current_user: 現在のユーザー（認証情報）
        db: データベースセッション
        
    Returns:
        dict: ログイン履歴
    """
    try:
        history = await user_service.get_login_history(current_user.user_id, limit, db)
        
        return {
            "status": "success",
            "data": {
                "history": history,
                "total": len(history)
            }
        }
        
    except Exception as e:
        logger.error("Failed to get login history", error=str(e), user_id=current_user.user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ログイン履歴取得でエラーが発生しました"
        )