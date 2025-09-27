#!/usr/bin/env python3
"""
Advanced Logger移行スクリプト
既存のログシステムから新しいAdvanced Loggerシステムへの移行
"""

import os
import re
import shutil
from pathlib import Path
from typing import List, Dict, Any


class LoggerMigrator:
    """ログシステム移行クラス"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.backup_dir = self.project_root / "backup_logs"
        self.migration_log = []
        
    def create_backup(self) -> None:
        """現在のログファイルをバックアップ"""
        print("🔄 Creating backup of existing log files...")
        
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
        # 既存のログファイルをバックアップ
        log_files = [
            self.project_root / "app" / "core" / "logging.py"
        ]
        
        for log_file in log_files:
            if log_file.exists():
                backup_file = self.backup_dir / log_file.name
                shutil.copy2(log_file, backup_file)
                print(f"   ✅ Backed up: {log_file.name}")
        
        print("✅ Backup completed")
    
    def update_imports(self) -> None:
        """importステートメントを更新"""
        print("🔄 Updating import statements...")
        
        # 更新対象のPythonファイルを検索
        python_files = list(self.project_root.glob("**/*.py"))
        
        old_imports = [
            r"from app\.core\.logging import StructuredLogger",
            r"from app\.core\.logging import get_logger",
            r"from app\.core\.logging import setup_logging",
            r"import app\.core\.logging",
        ]
        
        new_imports = [
            "from app.core.advanced_logger import get_logger",
            "from app.core.advanced_logger import get_logger", 
            "from app.core.advanced_logger import setup_advanced_logging",
            "from app.core import advanced_logger",
        ]
        
        for py_file in python_files:
            if py_file.name.startswith("migrate_") or py_file.name.startswith("backup_"):
                continue
                
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # import文を更新
                for old_pattern, new_import in zip(old_imports, new_imports):
                    content = re.sub(old_pattern, new_import, content)
                
                # StructuredLoggerクラスの使用を更新
                content = re.sub(r"StructuredLogger\(['\"]([^'\"]+)['\"]\)", r"get_logger('\\1')", content)
                content = re.sub(r"logger = StructuredLogger\(__name__\)", "logger = get_logger(__name__)", content)
                
                # setup_logging -> setup_advanced_logging
                content = re.sub(r"setup_logging\(\)", "setup_advanced_logging()", content)
                
                if content != original_content:
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(content)
                    self.migration_log.append(f"Updated imports in: {py_file.relative_to(self.project_root)}")
                    print(f"   ✅ Updated: {py_file.relative_to(self.project_root)}")
                    
            except Exception as e:
                print(f"   ❌ Error updating {py_file}: {e}")
        
        print("✅ Import statements updated")
    
    def create_logger_config(self) -> None:
        """新しいロガー設定ファイルを作成"""
        print("🔄 Creating logger configuration...")
        
        config_content = '''"""
Advanced Logger Configuration
高機能ログシステムの設定
"""

from app.core.advanced_logger import get_logger, setup_advanced_logging, set_global_context
from app.core.config import settings

# メインアプリケーションロガー
main_logger = get_logger("gait_analysis")

# モジュール別ロガー
api_logger = get_logger("api")
database_logger = get_logger("database") 
auth_logger = get_logger("auth")
gait_logger = get_logger("gait")
mediapipe_logger = get_logger("mediapipe")
report_logger = get_logger("report")

def initialize_logging():
    """ログシステムを初期化"""
    setup_advanced_logging()
    
    # グローバル設定
    set_global_context(
        application="gait_analysis",
        version=getattr(settings, "APP_VERSION", "1.0.0"),
        environment=getattr(settings, "ENVIRONMENT", "development")
    )
    
    main_logger.info("Advanced logging system initialized successfully")

def get_module_logger(module_name: str):
    """モジュール名からロガーを取得"""
    return get_logger(module_name)

# 後方互換性のため
StructuredLogger = get_logger  # 既存コードとの互換性
setup_logging = setup_advanced_logging  # 既存関数との互換性
'''
        
        config_file = self.project_root / "app" / "core" / "logger_config.py"
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        print(f"   ✅ Created: {config_file.relative_to(self.project_root)}")
        print("✅ Logger configuration created")
    
    def update_main_app(self) -> None:
        """メインアプリケーションを更新"""
        print("🔄 Updating main application...")
        
        main_py = self.project_root / "main.py"
        if main_py.exists():
            with open(main_py, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # setup_logging を setup_advanced_logging に変更
            content = re.sub(
                r"from app\.core\.logging import setup_logging",
                "from app.core.logger_config import initialize_logging",
                content
            )
            content = re.sub(r"setup_logging\(\)", "initialize_logging()", content)
            
            with open(main_py, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"   ✅ Updated: {main_py.name}")
        
        print("✅ Main application updated")
    
    def create_usage_examples(self) -> None:
        """使用例ファイルを作成"""
        print("🔄 Creating usage examples...")
        
        examples_content = '''"""
Advanced Logger Usage Examples
高機能ログシステムの使用例
"""

from app.core.advanced_logger import get_logger, set_global_context

# ロガーの取得
logger = get_logger("example")

def example_basic_logging():
    """基本的なログ使用例"""
    logger.info("Application started")
    logger.debug("Debug information", variable_value=42)
    logger.warning("Warning message", threshold_exceeded=True)
    logger.error("Error occurred", error_code=500)

def example_contextual_logging():
    """コンテキスト付きログ使用例"""
    # グローバルコンテキスト設定
    set_global_context(user_id="user123", session_id="session456")
    
    # 一時的なコンテキスト
    with logger.context_manager(request_id="req789"):
        logger.api("API request processed", endpoint="/analyze", status=200)

def example_category_logging():
    """カテゴリ別ログ使用例"""
    # API関連
    logger.api("Request received", method="POST", endpoint="/gait/analyze")
    
    # データベース関連
    logger.database("Query executed", table="analyses", duration_ms=25)
    
    # 認証関連
    logger.auth("User authenticated", user_id="user123", method="jwt")
    
    # 歩行分析関連
    logger.gait_analysis("Analysis completed", cycles=3, processing_time=2.5)
    
    # セキュリティ関連
    logger.security.login_attempt("user123", True, "192.168.1.100")

def example_performance_monitoring():
    """パフォーマンス監視使用例"""
    # コンテキストマネージャ
    with logger.performance_timer("video_processing"):
        # 処理のシミュレーション
        pass
    
    # デコレータ
    @logger.performance_decorator("gait_analysis")
    def analyze_gait(video_path):
        # 歩行分析処理
        return "analysis_result"

def example_exception_handling():
    """例外処理使用例"""
    @logger.exception_handler
    def risky_operation():
        # 危険な処理
        raise ValueError("Something went wrong")
    
    try:
        risky_operation()
    except ValueError:
        logger.error("Operation failed", operation="risky_operation")

def example_audit_logging():
    """監査ログ使用例"""
    logger.audit("User created", 
                user_id="new_user", 
                created_by="admin",
                permissions=["read", "write"])
    
    logger.audit("Data exported",
                analysis_id="ana123",
                exported_by="user456", 
                format="PDF")

# 実行例
if __name__ == "__main__":
    from app.core.logger_config import initialize_logging
    
    initialize_logging()
    
    example_basic_logging()
    example_contextual_logging()
    example_category_logging()
    example_performance_monitoring()
    example_audit_logging()
'''
        
        examples_file = self.project_root / "app" / "core" / "logger_examples.py"
        with open(examples_file, 'w', encoding='utf-8') as f:
            f.write(examples_content)
        
        print(f"   ✅ Created: {examples_file.relative_to(self.project_root)}")
        print("✅ Usage examples created")
    
    def create_migration_guide(self) -> None:
        """移行ガイドを作成"""
        print("🔄 Creating migration guide...")
        
        guide_content = '''# Advanced Logger Migration Guide

## 移行概要

既存の `StructuredLogger` から新しい `AdvancedLogger` システムへの移行が完了しました。

## 主な変更点

### 1. Import文の変更

**変更前:**
```python
from app.core.logging import StructuredLogger
logger = StructuredLogger(__name__)
```

**変更後:**
```python
from app.core.advanced_logger import get_logger
logger = get_logger(__name__)
```

### 2. 初期化の変更

**変更前:**
```python
from app.core.logging import setup_logging
setup_logging()
```

**変更後:**
```python
from app.core.logger_config import initialize_logging
initialize_logging()
```

## 新機能

### 1. カテゴリ別ログ
```python
logger.api("API request", endpoint="/test")
logger.database("Query executed", duration_ms=25)
logger.auth("User login", user_id="123")
logger.gait_analysis("Analysis completed", cycles=3)
logger.security("Security event", event_type="login_attempt")
```

### 2. コンテキスト管理
```python
# グローバルコンテキスト
set_global_context(user_id="123", session_id="abc")

# 一時的なコンテキスト
with logger.context_manager(request_id="xyz"):
    logger.info("Request processed")
```

### 3. パフォーマンス監視
```python
# コンテキストマネージャ
with logger.performance_timer("operation"):
    # 処理

# デコレータ
@logger.performance_decorator()
def my_function():
    pass
```

### 4. セキュリティログ
```python
logger.security.login_attempt("user123", True, "192.168.1.1")
logger.security.data_access("user123", "analysis", "ana456", "read")
logger.security.suspicious_activity("Multiple failed logins")
```

### 5. 監査ログ
```python
logger.audit("User created", user_id="new_user", created_by="admin")
```

## 設定ファイル

- `app/core/advanced_logger.py` - メインのロガークラス
- `app/core/logger_config.py` - 設定とユーティリティ
- `app/core/logger_examples.py` - 使用例

## ログファイル

ログは以下のファイルに分けて出力されます：

- `logs/info.log` - 一般的な情報ログ
- `logs/warning.log` - 警告ログ
- `logs/error.log` - エラーログ
- `logs/debug.log` - デバッグログ
- `logs/security.log` - セキュリティ関連ログ
- `logs/audit.log` - 監査ログ

## パフォーマンス統計

```python
stats = logger.get_performance_stats("operation_name")
print(f"Average: {stats['avg']}s, Count: {stats['count']}")
```

## 後方互換性

既存のコードは以下の方法で引き続き動作します：

```python
# これらの使い方は引き続きサポート
logger.info("message")
logger.warning("message", extra_param="value")
logger.error("message", error_code=500)
```

## トラブルシューティング

### ログが出力されない場合
1. `initialize_logging()` が呼ばれているか確認
2. ログディレクトリ (`logs/`) の権限を確認
3. ログレベル設定を確認

### パフォーマンスが低下した場合
1. ログレベルを `INFO` 以上に設定
2. 不要なデバッグログを削除
3. ログキューのサイズを調整

### メモリ使用量が増加した場合
1. ログローテーション設定を確認
2. パフォーマンス測定の履歴サイズを調整
3. 古いログファイルを削除

## サポート

問題が発生した場合は、`app/core/logger_examples.py` の使用例を参照してください。
'''
        
        guide_file = self.project_root / "LOGGER_MIGRATION_GUIDE.md"
        with open(guide_file, 'w', encoding='utf-8') as f:
            f.write(guide_content)
        
        print(f"   ✅ Created: {guide_file.name}")
        print("✅ Migration guide created")
    
    def run_migration(self) -> None:
        """完全な移行を実行"""
        print("🚀 Starting Advanced Logger Migration")
        print("=" * 50)
        
        self.create_backup()
        print()
        
        self.update_imports()
        print()
        
        self.create_logger_config()
        print()
        
        self.update_main_app()
        print()
        
        self.create_usage_examples()
        print()
        
        self.create_migration_guide()
        print()
        
        print("=" * 50)
        print("📊 Migration Summary")
        print("=" * 50)
        
        if self.migration_log:
            print("Files updated:")
            for log_entry in self.migration_log:
                print(f"  ✅ {log_entry}")
        else:
            print("No files required updates")
        
        print()
        print("🎉 Advanced Logger migration completed successfully!")
        print()
        print("Next steps:")
        print("1. Test the application: python3 main.py")
        print("2. Run logger examples: python3 app/core/logger_examples.py")
        print("3. Review the migration guide: LOGGER_MIGRATION_GUIDE.md")
        print("4. Update any custom logging code as needed")


def main():
    """メイン関数"""
    import sys
    
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = os.getcwd()
    
    migrator = LoggerMigrator(project_root)
    migrator.run_migration()


if __name__ == "__main__":
    main()