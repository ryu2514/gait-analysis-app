"""
ユーザー関連のデータモデル
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class UserType(str, Enum):
    """ユーザータイプ"""
    STANDARD = "standard"
    PREMIUM = "premium"
    PROFESSIONAL = "professional"
    ADMIN = "admin"


class Gender(str, Enum):
    """性別"""
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class User(BaseModel):
    """ユーザーモデル"""
    id: str = Field(..., description="ユーザーID")
    email: str = Field(..., description="メールアドレス")
    full_name: str = Field(..., description="フルネーム")
    user_type: UserType = Field(UserType.STANDARD, description="ユーザータイプ")
    
    # 身体情報
    height_cm: Optional[float] = Field(None, description="身長（cm）")
    weight_kg: Optional[float] = Field(None, description="体重（kg）")
    age: Optional[int] = Field(None, description="年齢")
    gender: Optional[Gender] = Field(None, description="性別")
    
    # システム情報
    created_at: datetime = Field(default_factory=datetime.utcnow, description="作成日時")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新日時")
    last_login: Optional[datetime] = Field(None, description="最終ログイン日時")
    is_active: bool = Field(True, description="アクティブ状態")
    is_verified: bool = Field(False, description="メール認証状態")
    
    # 設定
    timezone: str = Field("Asia/Tokyo", description="タイムゾーン")
    language: str = Field("ja", description="言語設定")
    
    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, v):
        """メールアドレスの妥当性チェック"""
        if not v or "@" not in v:
            raise ValueError("無効なメールアドレスです")
        return v.lower()
    
    @field_validator("height_cm", mode="before")
    @classmethod
    def validate_height(cls, v):
        """身長の妥当性チェック"""
        if v is not None and (v < 100 or v > 250):
            raise ValueError("身長は100-250cmの範囲で入力してください")
        return v
    
    @field_validator("weight_kg", mode="before")
    @classmethod
    def validate_weight(cls, v):
        """体重の妥当性チェック"""
        if v is not None and (v < 30 or v > 200):
            raise ValueError("体重は30-200kgの範囲で入力してください")
        return v
    
    @field_validator("age", mode="before")
    @classmethod
    def validate_age(cls, v):
        """年齢の妥当性チェック"""
        if v is not None and (v < 1 or v > 120):
            raise ValueError("年齢は1-120歳の範囲で入力してください")
        return v


class UserCreate(BaseModel):
    """ユーザー作成リクエスト"""
    email: str = Field(..., description="メールアドレス")
    password: str = Field(..., description="パスワード")
    full_name: str = Field(..., description="フルネーム")
    height_cm: Optional[float] = Field(None, description="身長（cm）")
    weight_kg: Optional[float] = Field(None, description="体重（kg）")
    age: Optional[int] = Field(None, description="年齢")
    gender: Optional[Gender] = Field(None, description="性別")
    
    @field_validator("password", mode="before")
    @classmethod
    def validate_password(cls, v):
        """パスワードの妥当性チェック"""
        if len(v) < 8:
            raise ValueError("パスワードは8文字以上である必要があります")
        if not any(c.isdigit() for c in v):
            raise ValueError("パスワードには数字を含める必要があります")
        if not any(c.isalpha() for c in v):
            raise ValueError("パスワードには英字を含める必要があります")
        return v


class UserUpdate(BaseModel):
    """ユーザー更新リクエスト"""
    full_name: Optional[str] = Field(None, description="フルネーム")
    height_cm: Optional[float] = Field(None, description="身長（cm）")
    weight_kg: Optional[float] = Field(None, description="体重（kg）")
    age: Optional[int] = Field(None, description="年齢")
    gender: Optional[Gender] = Field(None, description="性別")
    timezone: Optional[str] = Field(None, description="タイムゾーン")
    language: Optional[str] = Field(None, description="言語設定")


class UserLogin(BaseModel):
    """ログインリクエスト"""
    email: str = Field(..., description="メールアドレス")
    password: str = Field(..., description="パスワード")


class UserResponse(BaseModel):
    """ユーザーレスポンス（パスワードなし）"""
    id: str
    email: str
    full_name: str
    user_type: UserType
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    age: Optional[int] = None
    gender: Optional[Gender] = None
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool
    is_verified: bool
    timezone: str
    language: str


class TokenResponse(BaseModel):
    """トークンレスポンス"""
    access_token: str = Field(..., description="アクセストークン")
    token_type: str = Field("bearer", description="トークンタイプ")
    expires_in: int = Field(..., description="有効期限（秒）")
    user: UserResponse = Field(..., description="ユーザー情報")


class PasswordReset(BaseModel):
    """パスワードリセットリクエスト"""
    email: str = Field(..., description="メールアドレス")


class PasswordResetConfirm(BaseModel):
    """パスワードリセット確認"""
    token: str = Field(..., description="リセットトークン")
    new_password: str = Field(..., description="新しいパスワード")
    
    @field_validator("new_password", mode="before")
    @classmethod
    def validate_new_password(cls, v):
        """新しいパスワードの妥当性チェック"""
        if len(v) < 8:
            raise ValueError("パスワードは8文字以上である必要があります")
        return v


class UserStats(BaseModel):
    """ユーザー統計情報"""
    total_analyses: int = Field(..., description="総分析回数")
    this_month_analyses: int = Field(..., description="今月の分析回数")
    average_score: float = Field(..., description="平均スコア")
    latest_analysis_date: Optional[datetime] = Field(None, description="最新分析日時")
    account_created_days: int = Field(..., description="アカウント作成からの日数")
    streak_days: int = Field(0, description="連続使用日数")


class UserPreferences(BaseModel):
    """ユーザー設定"""
    notifications_enabled: bool = Field(True, description="通知有効")
    email_reports: bool = Field(True, description="メールレポート送信")
    data_sharing: bool = Field(False, description="データ共有許可")
    auto_backup: bool = Field(True, description="自動バックアップ")
    analysis_reminders: bool = Field(False, description="分析リマインダー")
    theme: str = Field("light", description="テーマ設定")
    default_analysis_mode: str = Field("standard", description="デフォルト分析モード")