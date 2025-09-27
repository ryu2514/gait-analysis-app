"""
ユーザー管理サービス
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc

from app.core.auth import auth_service
from app.core.logging import StructuredLogger
from app.database.connection import get_database_session
from app.models.database_models import User, RefreshToken, PasswordResetToken, LoginHistory
from app.models.user_models import UserCreate, UserUpdate, UserResponse, UserStats

logger = StructuredLogger(__name__)


class UserService:
    """ユーザーサービス"""
    
    def __init__(self):
        pass
    
    async def create_user(self, user_data: UserCreate, db: Session) -> UserResponse:
        """ユーザー作成"""
        try:
            # メールアドレスの重複確認
            existing_user = db.query(User).filter(User.email == user_data.email).first()
            if existing_user:
                raise ValueError("このメールアドレスは既に登録されています")
            
            # パスワードハッシュ化
            hashed_password = auth_service.hash_password(user_data.password)
            
            # ユーザー作成
            user = User(
                id=str(uuid.uuid4()),
                email=user_data.email,
                hashed_password=hashed_password,
                full_name=user_data.full_name,
                height_cm=user_data.height_cm,
                weight_kg=user_data.weight_kg,
                age=user_data.age,
                gender=user_data.gender.value if user_data.gender else None,
                created_at=datetime.utcnow(),
                is_active=True,
                is_verified=False
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            logger.info("User created successfully", user_id=user.id, email=user.email)
            
            return self._convert_to_user_response(user)
            
        except Exception as e:
            db.rollback()
            logger.error("Failed to create user", error=str(e), email=user_data.email)
            raise
    
    async def authenticate_user(self, email: str, password: str, db: Session) -> Optional[UserResponse]:
        """ユーザー認証"""
        try:
            user = db.query(User).filter(
                and_(User.email == email, User.is_active == True)
            ).first()
            
            if not user or not user.hashed_password:
                logger.warning("Authentication failed - user not found", email=email)
                return None
            
            if not auth_service.verify_password(password, user.hashed_password):
                logger.warning("Authentication failed - invalid password", email=email)
                return None
            
            # 最終ログイン時刻更新
            user.last_login = datetime.utcnow()
            db.commit()
            
            logger.info("User authenticated successfully", user_id=user.id, email=email)
            
            return self._convert_to_user_response(user)
            
        except Exception as e:
            logger.error("Authentication error", error=str(e), email=email)
            return None
    
    async def get_user_by_id(self, user_id: str, db: Session) -> Optional[UserResponse]:
        """ユーザーID取得"""
        try:
            user = db.query(User).filter(
                and_(User.id == user_id, User.is_active == True)
            ).first()
            
            if not user:
                return None
            
            return self._convert_to_user_response(user)
            
        except Exception as e:
            logger.error("Failed to get user by ID", error=str(e), user_id=user_id)
            return None
    
    async def get_user_by_email(self, email: str, db: Session) -> Optional[UserResponse]:
        """メールアドレスでユーザー取得"""
        try:
            user = db.query(User).filter(
                and_(User.email == email, User.is_active == True)
            ).first()
            
            if not user:
                return None
            
            return self._convert_to_user_response(user)
            
        except Exception as e:
            logger.error("Failed to get user by email", error=str(e), email=email)
            return None
    
    async def update_user(self, user_id: str, user_data: UserUpdate, db: Session) -> Optional[UserResponse]:
        """ユーザー情報更新"""
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            # 更新データの適用
            update_data = user_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if hasattr(user, field):
                    setattr(user, field, value)
            
            user.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(user)
            
            logger.info("User updated successfully", user_id=user_id)
            
            return self._convert_to_user_response(user)
            
        except Exception as e:
            db.rollback()
            logger.error("Failed to update user", error=str(e), user_id=user_id)
            raise
    
    async def create_firebase_user(self, firebase_uid: str, email: str, full_name: str, db: Session) -> UserResponse:
        """Firebaseユーザー作成"""
        try:
            # 既存ユーザー確認
            existing_user = db.query(User).filter(
                User.firebase_uid == firebase_uid
            ).first()
            
            if existing_user:
                return self._convert_to_user_response(existing_user)
            
            # メールアドレスでの重複確認
            email_user = db.query(User).filter(User.email == email).first()
            if email_user:
                # 既存ユーザーにFirebase UIDを関連付け
                email_user.firebase_uid = firebase_uid
                email_user.is_verified = True
                db.commit()
                db.refresh(email_user)
                return self._convert_to_user_response(email_user)
            
            # 新規Firebaseユーザー作成
            user = User(
                id=str(uuid.uuid4()),
                email=email,
                firebase_uid=firebase_uid,
                full_name=full_name,
                created_at=datetime.utcnow(),
                is_active=True,
                is_verified=True  # Firebase認証済み
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            logger.info("Firebase user created", user_id=user.id, firebase_uid=firebase_uid)
            
            return self._convert_to_user_response(user)
            
        except Exception as e:
            db.rollback()
            logger.error("Failed to create Firebase user", error=str(e), firebase_uid=firebase_uid)
            raise
    
    async def get_user_stats(self, user_id: str, db: Session) -> UserStats:
        """ユーザー統計取得"""
        try:
            # データサービスから統計を取得（循環インポートを避けるため動的インポート）
            from app.services.data_service import data_service
            
            stats_data = await data_service.get_user_statistics(user_id)
            
            # ユーザー作成日取得
            user = db.query(User).filter(User.id == user_id).first()
            account_created_days = 0
            if user:
                account_created_days = (datetime.utcnow() - user.created_at).days
            
            return UserStats(
                total_analyses=stats_data.get("total_analyses", 0),
                this_month_analyses=stats_data.get("this_month_analyses", 0),
                average_score=stats_data.get("average_score", 0.0),
                latest_analysis_date=stats_data.get("latest_analysis_date"),
                account_created_days=account_created_days,
                streak_days=stats_data.get("streak_days", 0)
            )
            
        except Exception as e:
            logger.error("Failed to get user stats", error=str(e), user_id=user_id)
            # デフォルト値を返す
            return UserStats(
                total_analyses=0,
                this_month_analyses=0,
                average_score=0.0,
                latest_analysis_date=None,
                account_created_days=0,
                streak_days=0
            )
    
    async def log_login(self, user_id: str, ip_address: str, user_agent: str, 
                       login_method: str, success: bool, failure_reason: str = None, db: Session = None):
        """ログイン履歴記録"""
        try:
            login_record = LoginHistory(
                user_id=user_id,
                login_timestamp=datetime.utcnow(),
                ip_address=ip_address,
                user_agent=user_agent,
                login_method=login_method,
                success=success,
                failure_reason=failure_reason
            )
            
            db.add(login_record)
            db.commit()
            
        except Exception as e:
            logger.error("Failed to log login", error=str(e), user_id=user_id)
    
    async def get_login_history(self, user_id: str, limit: int = 10, db: Session = None) -> List[Dict[str, Any]]:
        """ログイン履歴取得"""
        try:
            history = db.query(LoginHistory).filter(
                LoginHistory.user_id == user_id
            ).order_by(desc(LoginHistory.login_timestamp)).limit(limit).all()
            
            return [
                {
                    "timestamp": record.login_timestamp,
                    "ip_address": record.ip_address,
                    "user_agent": record.user_agent,
                    "login_method": record.login_method,
                    "success": record.success,
                    "failure_reason": record.failure_reason
                }
                for record in history
            ]
            
        except Exception as e:
            logger.error("Failed to get login history", error=str(e), user_id=user_id)
            return []
    
    def _convert_to_user_response(self, user: User) -> UserResponse:
        """ユーザーモデルをレスポンスモデルに変換"""
        from app.models.user_models import UserType, Gender
        
        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            user_type=UserType(user.user_type),
            height_cm=user.height_cm,
            weight_kg=user.weight_kg,
            age=user.age,
            gender=Gender(user.gender) if user.gender else None,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
            is_active=user.is_active,
            is_verified=user.is_verified,
            timezone=user.timezone,
            language=user.language
        )


# ユーザーサービスインスタンス
user_service = UserService()