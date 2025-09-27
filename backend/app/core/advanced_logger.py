"""
Advanced Logger System - 高機能ログシステム
歩行分析アプリケーション用に特別に設計された包括的なログシステム
"""

import logging
import logging.handlers
import sys
import os
import json
import traceback
import time
import threading
import queue
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union, Callable
from contextlib import contextmanager
from functools import wraps
from enum import Enum
from dataclasses import dataclass, asdict
from pathlib import Path

from app.core.config import settings


class LogLevel(Enum):
    """ログレベル列挙型"""
    TRACE = 5
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50
    SECURITY = 60  # セキュリティ関連のログ


class LogCategory(Enum):
    """ログカテゴリ"""
    SYSTEM = "system"
    API = "api"
    DATABASE = "database"
    AUTHENTICATION = "auth"
    GAIT_ANALYSIS = "gait"
    MEDIAPIPE = "mediapipe"
    REPORT = "report"
    PERFORMANCE = "performance"
    SECURITY = "security"
    USER_ACTION = "user_action"
    ERROR = "error"
    AUDIT = "audit"


@dataclass
class LogContext:
    """ログコンテキスト情報"""
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    trace_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    analysis_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class LogEntry:
    """ログエントリ"""
    timestamp: datetime
    level: LogLevel
    category: LogCategory
    message: str
    context: LogContext
    module: str
    function: str
    line_number: int
    thread_id: int
    process_id: int
    extra_data: Dict[str, Any]
    exception: Optional[str] = None
    stack_trace: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level.name,
            "category": self.category.value,
            "message": self.message,
            "context": self.context.to_dict(),
            "module": self.module,
            "function": self.function,
            "line_number": self.line_number,
            "thread_id": self.thread_id,
            "process_id": self.process_id,
            "extra_data": self.extra_data,
            "exception": self.exception,
            "stack_trace": self.stack_trace
        }
    
    def to_json(self) -> str:
        """JSON形式に変換"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=None)


class LogFilter:
    """ログフィルタ"""
    
    def __init__(self):
        self.filters: List[Callable[[LogEntry], bool]] = []
        
    def add_filter(self, filter_func: Callable[[LogEntry], bool]) -> None:
        """フィルタ関数を追加"""
        self.filters.append(filter_func)
        
    def should_log(self, entry: LogEntry) -> bool:
        """ログエントリがフィルタを通過するかチェック"""
        return all(f(entry) for f in self.filters)


class LogRotator:
    """ログローテーション管理"""
    
    def __init__(self, log_dir: str, max_size_mb: int = 100, max_files: int = 10):
        self.log_dir = Path(log_dir)
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_files = max_files
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
    def get_handler(self, filename: str) -> logging.handlers.RotatingFileHandler:
        """ローテーション付きファイルハンドラを取得"""
        filepath = self.log_dir / filename
        return logging.handlers.RotatingFileHandler(
            filepath,
            maxBytes=self.max_size_bytes,
            backupCount=self.max_files,
            encoding='utf-8'
        )


class PerformanceMonitor:
    """パフォーマンス監視"""
    
    def __init__(self):
        self.measurements: Dict[str, List[float]] = {}
        self.lock = threading.Lock()
        
    def add_measurement(self, operation: str, duration: float) -> None:
        """測定値を追加"""
        with self.lock:
            if operation not in self.measurements:
                self.measurements[operation] = []
            self.measurements[operation].append(duration)
            
            # 最新100件のみ保持
            if len(self.measurements[operation]) > 100:
                self.measurements[operation] = self.measurements[operation][-100:]
    
    def get_stats(self, operation: str) -> Dict[str, float]:
        """統計情報を取得"""
        with self.lock:
            if operation not in self.measurements or not self.measurements[operation]:
                return {}
                
            durations = self.measurements[operation]
            return {
                "count": len(durations),
                "avg": sum(durations) / len(durations),
                "min": min(durations),
                "max": max(durations),
                "p95": sorted(durations)[int(len(durations) * 0.95)] if len(durations) > 0 else 0
            }


class SecurityLogger:
    """セキュリティログ専用クラス"""
    
    def __init__(self, logger: 'AdvancedLogger'):
        self.logger = logger
        
    def login_attempt(self, user_id: str, success: bool, ip_address: str = None) -> None:
        """ログイン試行をログ"""
        self.logger.security(
            f"Login {'successful' if success else 'failed'} for user {user_id}",
            user_id=user_id,
            success=success,
            ip_address=ip_address,
            event_type="login_attempt"
        )
        
    def permission_denied(self, user_id: str, resource: str, action: str) -> None:
        """権限拒否をログ"""
        self.logger.security(
            f"Permission denied: user {user_id} attempted {action} on {resource}",
            user_id=user_id,
            resource=resource,
            action=action,
            event_type="permission_denied"
        )
        
    def data_access(self, user_id: str, resource_type: str, resource_id: str, action: str) -> None:
        """データアクセスをログ"""
        self.logger.security(
            f"Data access: user {user_id} {action} {resource_type} {resource_id}",
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            event_type="data_access"
        )
        
    def suspicious_activity(self, description: str, **kwargs) -> None:
        """疑わしい活動をログ"""
        self.logger.security(
            f"Suspicious activity detected: {description}",
            event_type="suspicious_activity",
            **kwargs
        )


class AdvancedLogger:
    """高機能ログクラス"""
    
    _instances: Dict[str, 'AdvancedLogger'] = {}
    _lock = threading.Lock()
    
    def __new__(cls, name: str) -> 'AdvancedLogger':
        """シングルトンパターンで名前付きインスタンスを管理"""
        with cls._lock:
            if name not in cls._instances:
                instance = super().__new__(cls)
                cls._instances[name] = instance
            return cls._instances[name]
    
    def __init__(self, name: str):
        if hasattr(self, '_initialized'):
            return
            
        self.name = name
        self.context = LogContext()
        self.filter = LogFilter()
        self.performance_monitor = PerformanceMonitor()
        self.security = SecurityLogger(self)
        
        # ログキューとワーカー設定
        self.log_queue = queue.Queue(maxsize=10000)
        self.worker_thread = None
        self.shutdown_event = threading.Event()
        
        # ログローテーター
        self.rotator = LogRotator(
            log_dir=getattr(settings, 'LOG_DIR', 'logs'),
            max_size_mb=getattr(settings, 'LOG_MAX_SIZE_MB', 100),
            max_files=getattr(settings, 'LOG_MAX_FILES', 10)
        )
        
        # ハンドラー設定
        self._setup_handlers()
        self._start_worker()
        
        self._initialized = True
    
    def _setup_handlers(self) -> None:
        """ハンドラーを設定"""
        self.handlers = {}
        
        # コンソールハンドラー
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        formatter = self._create_formatter()
        console_handler.setFormatter(formatter)
        self.handlers['console'] = console_handler
        
        # ファイルハンドラー（レベル別）
        for level_name in ['error', 'warning', 'info', 'debug']:
            handler = self.rotator.get_handler(f"{level_name}.log")
            handler.setLevel(getattr(logging, level_name.upper()))
            handler.setFormatter(self._create_json_formatter())
            self.handlers[level_name] = handler
            
        # セキュリティログ専用ハンドラー
        security_handler = self.rotator.get_handler("security.log")
        security_handler.setLevel(LogLevel.SECURITY.value)
        security_handler.setFormatter(self._create_json_formatter())
        self.handlers['security'] = security_handler
        
        # 監査ログハンドラー
        audit_handler = self.rotator.get_handler("audit.log")
        audit_handler.setLevel(logging.INFO)
        audit_handler.setFormatter(self._create_json_formatter())
        self.handlers['audit'] = audit_handler
    
    def _create_formatter(self) -> logging.Formatter:
        """標準フォーマッターを作成"""
        return logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def _create_json_formatter(self) -> logging.Formatter:
        """JSONフォーマッターを作成"""
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                if hasattr(record, 'log_entry'):
                    return record.log_entry.to_json()
                return super().format(record)
        
        return JsonFormatter()
    
    def _start_worker(self) -> None:
        """ワーカースレッドを開始"""
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
    
    def _worker(self) -> None:
        """ログ処理ワーカー"""
        while not self.shutdown_event.is_set():
            try:
                entry = self.log_queue.get(timeout=1.0)
                if entry is None:  # シャットダウンシグナル
                    break
                self._process_log_entry(entry)
                self.log_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Logger worker error: {e}", file=sys.stderr)
    
    def _process_log_entry(self, entry: LogEntry) -> None:
        """ログエントリを処理"""
        if not self.filter.should_log(entry):
            return
            
        # 標準ログレコード作成
        record = logging.LogRecord(
            name=self.name,
            level=entry.level.value,
            pathname="",
            lineno=entry.line_number,
            msg=entry.message,
            args=(),
            exc_info=None
        )
        record.log_entry = entry
        
        # ハンドラーに配信
        if entry.category == LogCategory.SECURITY:
            self.handlers['security'].handle(record)
        elif entry.category == LogCategory.AUDIT:
            self.handlers['audit'].handle(record)
        
        # レベル別ハンドラー
        level_name = entry.level.name.lower()
        if level_name in self.handlers:
            self.handlers[level_name].handle(record)
            
        # コンソール出力
        if getattr(settings, 'LOG_CONSOLE', True):
            self.handlers['console'].handle(record)
    
    def set_context(self, **kwargs) -> None:
        """ログコンテキストを設定"""
        for key, value in kwargs.items():
            if hasattr(self.context, key):
                setattr(self.context, key, value)
    
    def clear_context(self) -> None:
        """ログコンテキストをクリア"""
        self.context = LogContext()
    
    @contextmanager
    def context_manager(self, **kwargs):
        """一時的なコンテキスト設定"""
        old_context = LogContext(**self.context.to_dict())
        try:
            self.set_context(**kwargs)
            yield
        finally:
            self.context = old_context
    
    def _create_log_entry(
        self,
        level: LogLevel,
        category: LogCategory,
        message: str,
        **kwargs
    ) -> LogEntry:
        """ログエントリを作成"""
        frame = sys._getframe(3)  # 呼び出し元のフレーム
        
        return LogEntry(
            timestamp=datetime.now(timezone.utc),
            level=level,
            category=category,
            message=message,
            context=LogContext(**self.context.to_dict()),
            module=frame.f_globals.get('__name__', 'unknown'),
            function=frame.f_code.co_name,
            line_number=frame.f_lineno,
            thread_id=threading.current_thread().ident,
            process_id=os.getpid(),
            extra_data=kwargs,
            exception=kwargs.get('exception'),
            stack_trace=kwargs.get('stack_trace')
        )
    
    def log(self, level: LogLevel, category: LogCategory, message: str, **kwargs) -> None:
        """基本ログメソッド"""
        entry = self._create_log_entry(level, category, message, **kwargs)
        
        try:
            self.log_queue.put_nowait(entry)
        except queue.Full:
            # キューが満杯の場合は緊急出力
            print(f"LOG QUEUE FULL: {entry.to_json()}", file=sys.stderr)
    
    # 便利メソッド群
    def trace(self, message: str, **kwargs) -> None:
        """トレースログ"""
        self.log(LogLevel.TRACE, LogCategory.SYSTEM, message, **kwargs)
    
    def debug(self, message: str, **kwargs) -> None:
        """デバッグログ"""
        self.log(LogLevel.DEBUG, LogCategory.SYSTEM, message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """情報ログ"""
        self.log(LogLevel.INFO, LogCategory.SYSTEM, message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """警告ログ"""
        self.log(LogLevel.WARNING, LogCategory.SYSTEM, message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """エラーログ"""
        if 'exception' not in kwargs:
            # 現在の例外情報を取得
            exc_info = sys.exc_info()
            if exc_info[0] is not None:
                kwargs['exception'] = str(exc_info[1])
                kwargs['stack_trace'] = ''.join(traceback.format_exception(*exc_info))
        
        self.log(LogLevel.ERROR, LogCategory.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """重大エラーログ"""
        self.log(LogLevel.CRITICAL, LogCategory.ERROR, message, **kwargs)
    
    # カテゴリ別メソッド
    def api(self, message: str, **kwargs) -> None:
        """APIログ"""
        self.log(LogLevel.INFO, LogCategory.API, message, **kwargs)
    
    def database(self, message: str, **kwargs) -> None:
        """データベースログ"""
        self.log(LogLevel.INFO, LogCategory.DATABASE, message, **kwargs)
    
    def auth(self, message: str, **kwargs) -> None:
        """認証ログ"""
        self.log(LogLevel.INFO, LogCategory.AUTHENTICATION, message, **kwargs)
    
    def gait_analysis(self, message: str, **kwargs) -> None:
        """歩行分析ログ"""
        self.log(LogLevel.INFO, LogCategory.GAIT_ANALYSIS, message, **kwargs)
    
    def mediapipe(self, message: str, **kwargs) -> None:
        """MediaPipeログ"""
        self.log(LogLevel.DEBUG, LogCategory.MEDIAPIPE, message, **kwargs)
    
    def report(self, message: str, **kwargs) -> None:
        """レポートログ"""
        self.log(LogLevel.INFO, LogCategory.REPORT, message, **kwargs)
    
    def security(self, message: str, **kwargs) -> None:
        """セキュリティログ"""
        self.log(LogLevel.SECURITY, LogCategory.SECURITY, message, **kwargs)
    
    def audit(self, message: str, **kwargs) -> None:
        """監査ログ"""
        self.log(LogLevel.INFO, LogCategory.AUDIT, message, **kwargs)
    
    def user_action(self, message: str, **kwargs) -> None:
        """ユーザーアクションログ"""
        self.log(LogLevel.INFO, LogCategory.USER_ACTION, message, **kwargs)
    
    @contextmanager
    def performance_timer(self, operation: str):
        """パフォーマンス測定コンテキストマネージャ"""
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.performance_monitor.add_measurement(operation, duration)
            self.log(
                LogLevel.INFO,
                LogCategory.PERFORMANCE,
                f"Operation '{operation}' completed",
                operation=operation,
                duration_seconds=duration
            )
    
    def performance_decorator(self, operation: str = None):
        """パフォーマンス測定デコレータ"""
        def decorator(func):
            op_name = operation or f"{func.__module__}.{func.__name__}"
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                with self.performance_timer(op_name):
                    return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def exception_handler(self, func):
        """例外ハンドリングデコレータ"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                self.error(
                    f"Exception in {func.__name__}",
                    function=func.__name__,
                    exception=str(e),
                    stack_trace=traceback.format_exc()
                )
                raise
        return wrapper
    
    def get_performance_stats(self, operation: str = None) -> Dict[str, Any]:
        """パフォーマンス統計を取得"""
        if operation:
            return self.performance_monitor.get_stats(operation)
        return {
            op: self.performance_monitor.get_stats(op)
            for op in self.performance_monitor.measurements.keys()
        }
    
    def shutdown(self) -> None:
        """ログシステムをシャットダウン"""
        self.shutdown_event.set()
        if self.worker_thread and self.worker_thread.is_alive():
            self.log_queue.put(None)  # シャットダウンシグナル
            self.worker_thread.join(timeout=5.0)
            
        # ハンドラーをクローズ
        for handler in self.handlers.values():
            handler.close()


# グローバルインスタンス
def get_logger(name: str = "gait_analysis") -> AdvancedLogger:
    """ログインスタンスを取得"""
    return AdvancedLogger(name)


# デフォルトロガー
logger = get_logger()


# 便利関数
def set_global_context(**kwargs) -> None:
    """グローバルログコンテキストを設定"""
    logger.set_context(**kwargs)


def clear_global_context() -> None:
    """グローバルログコンテキストをクリア"""
    logger.clear_context()


# セットアップ関数
def setup_advanced_logging() -> None:
    """高機能ログシステムを初期化"""
    # 既存のログハンドラーを無効化
    logging.getLogger().handlers.clear()
    
    # MediaPipeなどの外部ライブラリのログレベルを調整
    logging.getLogger("mediapipe").setLevel(logging.WARNING)
    logging.getLogger("opencv").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    logger.info("Advanced logging system initialized")


# 使用例とテスト用関数
def demo_advanced_logger():
    """Advanced Loggerのデモンストレーション"""
    demo_logger = get_logger("demo")
    
    # コンテキスト設定
    demo_logger.set_context(
        user_id="demo_user_123",
        session_id="session_456",
        request_id="req_789"
    )
    
    # 各種ログレベルのテスト
    demo_logger.trace("This is a trace message")
    demo_logger.debug("This is a debug message")
    demo_logger.info("This is an info message")
    demo_logger.warning("This is a warning message")
    demo_logger.error("This is an error message")
    demo_logger.critical("This is a critical message")
    
    # カテゴリ別ログ
    demo_logger.api("API request processed", endpoint="/test", method="GET", status_code=200)
    demo_logger.database("Database query executed", query="SELECT * FROM users", duration_ms=45)
    demo_logger.auth("User authenticated successfully", method="jwt")
    demo_logger.gait_analysis("Gait analysis completed", cycles_detected=3, processing_time=2.5)
    
    # セキュリティログ
    demo_logger.security.login_attempt("demo_user_123", True, "192.168.1.100")
    demo_logger.security.data_access("demo_user_123", "gait_analysis", "analysis_456", "read")
    
    # パフォーマンス測定
    with demo_logger.performance_timer("test_operation"):
        time.sleep(0.1)  # 処理のシミュレーション
    
    # 統計情報表示
    stats = demo_logger.get_performance_stats("test_operation")
    print(f"Performance stats: {stats}")
    
    demo_logger.info("Logger demonstration completed")


if __name__ == "__main__":
    setup_advanced_logging()
    demo_advanced_logger()