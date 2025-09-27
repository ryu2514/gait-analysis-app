"""
Performance Configuration
パフォーマンス最適化設定
"""

import os
import asyncio
import redis
from typing import Dict, Any, Optional, Union, List
from functools import wraps
import hashlib
import json
import time
from datetime import datetime, timedelta

from app.core.advanced_logger import get_logger
from app.core.config import settings

logger = get_logger("performance_config")


class CacheManager:
    """高性能キャッシュマネージャー"""
    
    def __init__(self):
        self.redis_client = None
        self.local_cache = {}
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0
        }
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Redis接続初期化"""
        try:
            redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
            self.redis_client = redis.from_url(redis_url)
            self.redis_client.ping()
            logger.info("Redis cache initialized successfully")
        except Exception as e:
            logger.warning("Redis not available, using local cache only", error=str(e))
            self.redis_client = None
    
    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """キャッシュキーを生成"""
        key_data = f"{prefix}:{args}:{kwargs}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get(self, key: str) -> Optional[Any]:
        """キャッシュから値を取得"""
        try:
            # まずローカルキャッシュをチェック
            if key in self.local_cache:
                item = self.local_cache[key]
                if item['expires_at'] > time.time():
                    self.cache_stats["hits"] += 1
                    return item['value']
                else:
                    del self.local_cache[key]
            
            # Redisキャッシュをチェック
            if self.redis_client:
                value = await asyncio.to_thread(self.redis_client.get, key)
                if value:
                    self.cache_stats["hits"] += 1
                    return json.loads(value)
            
            self.cache_stats["misses"] += 1
            return None
            
        except Exception as e:
            logger.error("Cache get error", key=key, error=str(e))
            self.cache_stats["misses"] += 1
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        """キャッシュに値を設定"""
        try:
            expires_at = time.time() + ttl
            
            # ローカルキャッシュに保存
            self.local_cache[key] = {
                'value': value,
                'expires_at': expires_at
            }
            
            # Redisキャッシュに保存
            if self.redis_client:
                await asyncio.to_thread(
                    self.redis_client.setex, 
                    key, 
                    ttl, 
                    json.dumps(value, default=str)
                )
            
            self.cache_stats["sets"] += 1
            logger.debug("Cache set", key=key, ttl=ttl)
            
        except Exception as e:
            logger.error("Cache set error", key=key, error=str(e))
    
    async def delete(self, key: str):
        """キャッシュから削除"""
        try:
            # ローカルキャッシュから削除
            if key in self.local_cache:
                del self.local_cache[key]
            
            # Redisキャッシュから削除
            if self.redis_client:
                await asyncio.to_thread(self.redis_client.delete, key)
            
            self.cache_stats["deletes"] += 1
            logger.debug("Cache delete", key=key)
            
        except Exception as e:
            logger.error("Cache delete error", key=key, error=str(e))
    
    def get_stats(self) -> Dict[str, Any]:
        """キャッシュ統計を取得"""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.cache_stats,
            "hit_rate_percent": hit_rate,
            "local_cache_size": len(self.local_cache),
            "redis_available": self.redis_client is not None
        }


# グローバルキャッシュマネージャー
cache_manager = CacheManager()


def cache_result(ttl: int = 3600, key_prefix: str = "default"):
    """結果キャッシュデコレータ"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # キャッシュキー生成
            cache_key = cache_manager._generate_cache_key(
                f"{key_prefix}:{func.__name__}", 
                *args, **kwargs
            )
            
            # キャッシュから取得試行
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug("Cache hit", function=func.__name__, key=cache_key[:8])
                return cached_result
            
            # 関数実行
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            
            # 結果をキャッシュ
            await cache_manager.set(cache_key, result, ttl)
            logger.debug("Cache miss - result cached", function=func.__name__, key=cache_key[:8])
            
            return result
        return wrapper
    return decorator


class PerformanceConfig:
    """パフォーマンス設定クラス"""
    
    # MediaPipe最適化設定
    MEDIAPIPE_OPTIMIZED = {
        "model_complexity": 0,  # 最高速度
        "min_detection_confidence": 0.7,  # 精度重視
        "min_tracking_confidence": 0.5,
        "enable_segmentation": False,  # セグメンテーション無効
        "smooth_landmarks": True,
        "static_image_mode": False
    }
    
    # 動画処理最適化設定
    VIDEO_PROCESSING_OPTIMIZED = {
        "target_fps": 15,  # フレームレート削減
        "max_resolution_height": 720,  # 解像度制限
        "compression_quality": 85,  # 圧縮率
        "enable_gpu_acceleration": True,
        "batch_size": 4,  # バッチ処理
        "skip_frame_ratio": 2  # フレームスキップ
    }
    
    # データベース最適化設定
    DATABASE_OPTIMIZED = {
        "pool_size": 20,  # 接続プール
        "max_overflow": 30,
        "pool_timeout": 30,
        "pool_recycle": 3600,
        "pool_pre_ping": True,
        "echo": False,  # ログ無効
        "query_cache_size": 1000,
        "enable_query_cache": True
    }
    
    # API最適化設定
    API_OPTIMIZED = {
        "worker_processes": min(4, os.cpu_count()),
        "worker_connections": 1000,
        "keepalive_timeout": 2,
        "max_requests": 1000,
        "max_requests_jitter": 100,
        "preload_app": True,
        "enable_compression": True,
        "compression_level": 6
    }
    
    # メモリ最適化設定
    MEMORY_OPTIMIZED = {
        "numpy_dtype": "float32",  # メモリ使用量削減
        "gc_threshold": (700, 10, 10),  # ガベージコレクション閾値
        "gc_collect_interval": 100,  # 定期的GC
        "max_cache_size": 1000,
        "enable_memory_profiling": False,
        "large_object_threshold": 1024 * 1024  # 1MB
    }
    
    @classmethod
    def get_optimized_settings(cls) -> Dict[str, Any]:
        """最適化された設定を取得"""
        return {
            "mediapipe": cls.MEDIAPIPE_OPTIMIZED,
            "video_processing": cls.VIDEO_PROCESSING_OPTIMIZED,
            "database": cls.DATABASE_OPTIMIZED,
            "api": cls.API_OPTIMIZED,
            "memory": cls.MEMORY_OPTIMIZED
        }
    
    @classmethod
    def apply_optimizations(cls):
        """最適化設定を適用"""
        logger.info("Applying performance optimizations")
        
        # MediaPipe設定適用
        for key, value in cls.MEDIAPIPE_OPTIMIZED.items():
            attr = f"MEDIAPIPE_{key.upper()}"
            if hasattr(settings, attr):
                setattr(settings, attr, value)
            else:
                logger.debug("Skipping unknown MEDIAPIPE setting", key=attr)
        
        # 動画処理設定適用
        for key, value in cls.VIDEO_PROCESSING_OPTIMIZED.items():
            attr = key.upper()
            if hasattr(settings, attr):
                setattr(settings, attr, value)
            else:
                logger.debug("Skipping unknown VIDEO setting", key=attr)
        
        # メモリ最適化適用
        import gc
        gc.set_threshold(*cls.MEMORY_OPTIMIZED["gc_threshold"])
        
        logger.info("Performance optimizations applied successfully")


class AsyncTaskQueue:
    """非同期タスクキュー"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.queue = asyncio.Queue()
        self.workers = []
        self.stats = {
            "tasks_processed": 0,
            "tasks_failed": 0,
            "average_processing_time": 0.0
        }
        self.processing_times = []
    
    async def start_workers(self):
        """ワーカーを開始"""
        for i in range(self.max_workers):
            worker = asyncio.create_task(self._worker(f"worker-{i}"))
            self.workers.append(worker)
        
        logger.info("Async task queue started", workers=self.max_workers)
    
    async def _worker(self, worker_name: str):
        """ワーカープロセス"""
        while True:
            try:
                task_func, args, kwargs = await self.queue.get()
                
                start_time = time.time()
                try:
                    if asyncio.iscoroutinefunction(task_func):
                        await task_func(*args, **kwargs)
                    else:
                        task_func(*args, **kwargs)
                    
                    processing_time = time.time() - start_time
                    self.processing_times.append(processing_time)
                    
                    # 最新100件のみ保持
                    if len(self.processing_times) > 100:
                        self.processing_times = self.processing_times[-100:]
                    
                    self.stats["tasks_processed"] += 1
                    self.stats["average_processing_time"] = sum(self.processing_times) / len(self.processing_times)
                    
                except Exception as e:
                    logger.error("Task processing failed", 
                               worker=worker_name, 
                               error=str(e))
                    self.stats["tasks_failed"] += 1
                
                finally:
                    self.queue.task_done()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Worker error", worker=worker_name, error=str(e))
    
    async def add_task(self, func, *args, **kwargs):
        """タスクを追加"""
        await self.queue.put((func, args, kwargs))
    
    async def stop_workers(self):
        """ワーカーを停止"""
        for worker in self.workers:
            worker.cancel()
        
        await asyncio.gather(*self.workers, return_exceptions=True)
        logger.info("Async task queue stopped")
    
    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        return {
            **self.stats,
            "queue_size": self.queue.qsize(),
            "active_workers": len([w for w in self.workers if not w.done()])
        }


# グローバルタスクキュー
task_queue = AsyncTaskQueue(max_workers=min(4, os.cpu_count()))


class PerformanceMonitor:
    """パフォーマンス監視"""
    
    def __init__(self):
        self.metrics = {}
        self.alerts = []
        
    def record_metric(self, name: str, value: float, tags: Dict[str, str] = None):
        """メトリクスを記録"""
        timestamp = datetime.utcnow()
        
        if name not in self.metrics:
            self.metrics[name] = []
        
        self.metrics[name].append({
            "timestamp": timestamp,
            "value": value,
            "tags": tags or {}
        })
        
        # 最新1000件のみ保持
        if len(self.metrics[name]) > 1000:
            self.metrics[name] = self.metrics[name][-1000:]
        
        # アラート条件チェック
        self._check_alerts(name, value)
    
    def _check_alerts(self, metric_name: str, value: float):
        """アラート条件をチェック"""
        alert_conditions = {
            "response_time_ms": 5000,  # 5秒以上
            "memory_usage_mb": 2000,   # 2GB以上
            "cpu_usage_percent": 80,   # 80%以上
            "error_rate_percent": 5    # 5%以上
        }
        
        if metric_name in alert_conditions:
            threshold = alert_conditions[metric_name]
            if value > threshold:
                alert = {
                    "timestamp": datetime.utcnow(),
                    "metric": metric_name,
                    "value": value,
                    "threshold": threshold,
                    "severity": "warning" if value < threshold * 1.5 else "critical"
                }
                self.alerts.append(alert)
                
                logger.warning("Performance alert triggered",
                             metric=metric_name,
                             value=value,
                             threshold=threshold)
    
    def get_metrics_summary(self, metric_name: str, hours: int = 1) -> Dict[str, Any]:
        """メトリクス要約を取得"""
        if metric_name not in self.metrics:
            return {}
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_metrics = [
            m for m in self.metrics[metric_name] 
            if m["timestamp"] > cutoff_time
        ]
        
        if not recent_metrics:
            return {}
        
        values = [m["value"] for m in recent_metrics]
        
        return {
            "count": len(values),
            "avg": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "p95": sorted(values)[int(len(values) * 0.95)] if len(values) > 0 else 0,
            "latest": values[-1] if values else 0
        }
    
    def get_active_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """アクティブなアラートを取得"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [
            alert for alert in self.alerts 
            if alert["timestamp"] > cutoff_time
        ]


# グローバルパフォーマンスモニター
performance_monitor = PerformanceMonitor()


def init_performance_systems():
    """パフォーマンスシステムを初期化"""
    logger.info("Initializing performance systems")
    
    # 最適化設定適用
    PerformanceConfig.apply_optimizations()
    
    # タスクキュー開始（軽量モード/無効化フラグ時はスキップ）
    if not getattr(settings, 'LIGHT_MODE', False) and not getattr(settings, 'DISABLE_TASK_QUEUE', False):
        asyncio.create_task(task_queue.start_workers())
    else:
        logger.info("Async task queue disabled (light mode or DISABLE_TASK_QUEUE)")
    
    logger.info("Performance systems initialized successfully")
