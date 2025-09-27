"""
認証システム
JWT認証とFirebase認証の統合実装
"""

import jwt
import json
import firebase_admin
from firebase_admin import credentials, auth
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import StructuredLogger

logger = StructuredLogger(__name__)

# パスワードハッシュ化設定
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTPベアラートークン設定
security = HTTPBearer()


class TokenData(BaseModel):
    """JWTトークンデータ"""
    sub: str
    exp: datetime
    iat: datetime
    user_id: str
    email: str
    user_type: str = "standard"


class UserCreate(BaseModel):
    """ユーザー作成データ"""
    email: str
    password: str
    full_name: str
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    age: Optional[int] = None
    gender: Optional[str] = None


class UserResponse(BaseModel):
    """ユーザーレスポンス"""
    id: str
    email: str
    full_name: str
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    created_at: datetime
    is_active: bool = True


class AuthService:
    """認証サービス"""
    
    def __init__(self):
        self.jwt_secret = settings.JWT_SECRET_KEY
        self.jwt_algorithm = settings.JWT_ALGORITHM
        self.access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        # Firebase初期化
        self._init_firebase()
    
    def _init_firebase(self):
        """Firebase初期化"""
        try:
            if not firebase_admin._apps:
                # 認証情報ファイルまたは環境変数から初期化
                if hasattr(settings, 'FIREBASE_CREDENTIALS_PATH') and settings.FIREBASE_CREDENTIALS_PATH:
                    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
                else:
                    # 環境変数から初期化（本番環境用）
                    cred = credentials.ApplicationDefault()
                
                firebase_admin.initialize_app(cred)
                logger.info("Firebase initialized successfully")
        except Exception as e:
            logger.warning("Firebase initialization failed", error=str(e))
    
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """JWTアクセストークン作成"""
        to_encode = data.copy()
        expire = datetime.utcnow() + self.access_token_expires
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow()
        })
        
        encoded_jwt = jwt.encode(
            to_encode, 
            self.jwt_secret, 
            algorithm=self.jwt_algorithm
        )
        
        logger.info("Access token created", user_id=data.get("user_id"))
        return encoded_jwt
    
    def verify_token(self, token: str) -> TokenData:
        """JWTトークン検証"""
        try:
            payload = jwt.decode(
                token, 
                self.jwt_secret, 
                algorithms=[self.jwt_algorithm]
            )
            
            user_id = payload.get("user_id")
            email = payload.get("email")
            
            if user_id is None or email is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload"
                )
            
            token_data = TokenData(
                sub=payload.get("sub", user_id),
                exp=datetime.fromtimestamp(payload.get("exp")),
                iat=datetime.fromtimestamp(payload.get("iat")),
                user_id=user_id,
                email=email,
                user_type=payload.get("user_type", "standard")
            )
            
            return token_data
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
    
    def verify_firebase_token(self, token: str) -> Dict[str, Any]:
        """Firebase IDトークン検証"""
        try:
            decoded_token = auth.verify_id_token(token)
            logger.info("Firebase token verified", uid=decoded_token.get("uid"))
            return decoded_token
        except Exception as e:
            logger.error("Firebase token verification failed", error=str(e))
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Firebase token"
            )
    
    def hash_password(self, password: str) -> str:
        """パスワードハッシュ化"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """パスワード検証"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_user_token(self, user_id: str, email: str, user_type: str = "standard") -> str:
        """ユーザー用トークン作成"""
        token_data = {
            "user_id": user_id,
            "email": email,
            "user_type": user_type,
            "sub": user_id
        }
        return self.create_access_token(token_data)


# 認証サービスインスタンス
auth_service = AuthService()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """現在のユーザー取得（依存性注入用）"""
    token = credentials.credentials
    
    # JWTトークンまたはFirebase IDトークンを試行
    try:
        # まずJWTトークンとして検証
        return auth_service.verify_token(token)
    except HTTPException:
        try:
            # FirebaseIDトークンとして検証
            firebase_user = auth_service.verify_firebase_token(token)
            
            # FirebaseユーザーからTokenDataを作成
            return TokenData(
                sub=firebase_user.get("uid"),
                exp=datetime.fromtimestamp(firebase_user.get("exp")),
                iat=datetime.fromtimestamp(firebase_user.get("iat")),
                user_id=firebase_user.get("uid"),
                email=firebase_user.get("email", ""),
                user_type="firebase"
            )
        except HTTPException:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )


async def get_current_active_user(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """現在のアクティブユーザー取得"""
    # ここで必要に応じてユーザーの活性状態を確認
    return current_user


# オプショナル認証（ログインしていなくても使用可能なエンドポイント用）
async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))) -> Optional[TokenData]:
    """オプショナルユーザー取得"""
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


def require_user_type(allowed_types: list):
    """特定のユーザータイプを要求するデコレータ"""
    def decorator(current_user: TokenData = Depends(get_current_active_user)):
        if current_user.user_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return decorator


# 管理者専用
admin_required = require_user_type(["admin"])

# プレミアムユーザー以上
premium_required = require_user_type(["premium", "admin"])