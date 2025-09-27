"""
データベース接続とセッション管理
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import os

from app.core.config import settings
from app.core.logging import StructuredLogger
from app.models.database_models import Base

logger = StructuredLogger(__name__)


class DatabaseManager:
    """データベース管理クラス"""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._initialized = False
    
    def initialize(self):
        """データベース初期化"""
        if self._initialized:
            return
        
        try:
            # データベースURL構築
            if settings.DATABASE_URL:
                database_url = settings.DATABASE_URL
            else:
                # 開発環境用SQLite
                database_url = f"sqlite:///{settings.DATABASE_PATH}"
                os.makedirs(os.path.dirname(settings.DATABASE_PATH), exist_ok=True)
            
            # エンジン作成
            if database_url.startswith("sqlite"):
                # SQLite用設定
                self.engine = create_engine(
                    database_url,
                    poolclass=StaticPool,
                    connect_args={
                        "check_same_thread": False,
                        "timeout": 20
                    },
                    echo=settings.DATABASE_ECHO
                )
            else:
                # PostgreSQL/MySQL用設定
                self.engine = create_engine(
                    database_url,
                    pool_pre_ping=True,
                    pool_recycle=300,
                    pool_size=10,
                    max_overflow=20,
                    echo=settings.DATABASE_ECHO
                )
            
            # セッションファクトリ作成
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # SQLiteの場合はWALモードを有効化
            if database_url.startswith("sqlite"):
                @event.listens_for(self.engine, "connect")
                def set_sqlite_pragma(dbapi_connection, connection_record):
                    cursor = dbapi_connection.cursor()
                    cursor.execute("PRAGMA journal_mode=WAL")
                    cursor.execute("PRAGMA synchronous=NORMAL")
                    cursor.execute("PRAGMA cache_size=1000")
                    cursor.execute("PRAGMA foreign_keys=ON")
                    cursor.close()
            
            self._initialized = True
            logger.info("Database initialized successfully", database_url=database_url.split('@')[-1])
            
        except Exception as e:
            logger.error("Failed to initialize database", error=str(e))
            raise
    
    def create_tables(self):
        """テーブル作成"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error("Failed to create database tables", error=str(e))
            raise
    
    def drop_tables(self):
        """テーブル削除（開発・テスト用）"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error("Failed to drop database tables", error=str(e))
            raise
    
    def get_session(self) -> Session:
        """データベースセッション取得"""
        if not self._initialized:
            self.initialize()
        return self.SessionLocal()
    
    @asynccontextmanager
    async def get_async_session(self) -> AsyncGenerator[Session, None]:
        """非同期セッション取得"""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def health_check(self) -> bool:
        """データベース接続確認"""
        try:
            from sqlalchemy import text
            with self.get_session() as session:
                session.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error("Database health check failed", error=str(e))
            return False


# グローバルデータベースマネージャー
db_manager = DatabaseManager()


def get_database_session() -> Session:
    """FastAPI依存関数：データベースセッション取得"""
    session = db_manager.get_session()
    try:
        yield session
    finally:
        session.close()


async def init_database():
    """データベース初期化（アプリケーション起動時）"""
    try:
        db_manager.initialize()
        db_manager.create_tables()
        
        # 初期データ作成
        await create_initial_data()
        
        logger.info("Database initialization completed")
    except Exception as e:
        logger.error("Database initialization failed", error=str(e))
        raise


async def create_initial_data():
    """初期データ作成"""
    try:
        async with db_manager.get_async_session() as session:
            # 管理者ユーザーが存在しない場合は作成
            from app.models.database_models import User
            from app.core.auth import auth_service
            
            admin_user = session.query(User).filter(User.email == "admin@gaitanalysis.com").first()
            
            if not admin_user:
                admin_user = User(
                    email="admin@gaitanalysis.com",
                    username="admin",
                    hashed_password=auth_service.hash_password("admin123"),  # 本番環境では変更必須
                    full_name="System Administrator",
                    user_type="admin",
                    is_active=True,
                    is_verified=True
                )
                session.add(admin_user)
                session.commit()
                logger.info("Admin user created")
        
    except Exception as e:
        logger.error("Failed to create initial data", error=str(e))


class DatabaseMigration:
    """データベースマイグレーション管理"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    async def migrate_to_latest(self):
        """最新バージョンにマイグレート"""
        try:
            # バージョンテーブルが存在しない場合は作成
            await self._ensure_version_table()
            
            # 現在のバージョンを取得
            current_version = await self._get_current_version()
            
            # 必要なマイグレーションを実行
            migrations = self._get_pending_migrations(current_version)
            
            for migration in migrations:
                await self._execute_migration(migration)
                await self._update_version(migration['version'])
            
            logger.info("Database migration completed", 
                       current_version=current_version,
                       migrations_applied=len(migrations))
            
        except Exception as e:
            logger.error("Database migration failed", error=str(e))
            raise
    
    async def _ensure_version_table(self):
        """バージョンテーブル確保"""
        async with self.db_manager.get_async_session() as session:
            session.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
    
    async def _get_current_version(self) -> int:
        """現在のスキーマバージョン取得"""
        async with self.db_manager.get_async_session() as session:
            result = session.execute("SELECT MAX(version) FROM schema_version")
            version = result.scalar()
            return version if version is not None else 0
    
    def _get_pending_migrations(self, current_version: int) -> list:
        """適用待ちマイグレーション取得"""
        # マイグレーション定義
        migrations = [
            {
                'version': 1,
                'name': 'Initial schema',
                'sql': None  # 初期スキーマは既に適用済み
            },
            {
                'version': 2,
                'name': 'Add user preferences',
                'sql': """
                    ALTER TABLE users ADD COLUMN notification_enabled BOOLEAN DEFAULT TRUE;
                    ALTER TABLE users ADD COLUMN preferred_units VARCHAR(10) DEFAULT 'metric';
                """
            },
            # 将来のマイグレーションをここに追加
        ]
        
        return [m for m in migrations if m['version'] > current_version and m['sql']]
    
    async def _execute_migration(self, migration: dict):
        """マイグレーション実行"""
        async with self.db_manager.get_async_session() as session:
            session.execute(migration['sql'])
            logger.info("Migration applied", version=migration['version'], name=migration['name'])
    
    async def _update_version(self, version: int):
        """バージョン更新"""
        async with self.db_manager.get_async_session() as session:
            session.execute(
                "INSERT INTO schema_version (version) VALUES (?)",
                (version,)
            )