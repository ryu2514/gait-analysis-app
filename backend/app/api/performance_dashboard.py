"""
Performance Monitoring Dashboard API
パフォーマンス監視ダッシュボードAPI
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import json
import psutil
import asyncio

from app.core.advanced_logger import get_logger
from app.core.performance_config import cache_manager, performance_monitor, task_queue
from app.services.optimized_video_service import optimized_video_processor
from app.core.auth import get_current_user
from app.models.user_models import UserResponse

router = APIRouter()
logger = get_logger("performance_dashboard")


@router.get("/metrics/system")
async def get_system_metrics():
    """システムメトリクスを取得"""
    try:
        # CPU情報
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # メモリ情報
        memory = psutil.virtual_memory()
        
        # ディスク情報
        disk = psutil.disk_usage('/')
        
        # ネットワーク情報
        network = psutil.net_io_counters()
        
        # プロセス情報
        process = psutil.Process()
        process_memory = process.memory_info()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "cpu": {
                "usage_percent": cpu_percent,
                "count": cpu_count,
                "freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
            },
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "percent": memory.percent,
                "process_mb": round(process_memory.rss / (1024**2), 2)
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "percent": round((disk.used / disk.total) * 100, 2)
            },
            "network": {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            } if network else None,
            "process": {
                "threads": process.num_threads(),
                "connections": len(process.connections()),
                "open_files": len(process.open_files())
            }
        }
        
    except Exception as e:
        logger.error("Failed to get system metrics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get system metrics")


@router.get("/metrics/performance")
async def get_performance_metrics(
    metric_name: Optional[str] = Query(None, description="特定のメトリクス名"),
    hours: int = Query(1, description="取得する時間範囲（時間）")
):
    """パフォーマンスメトリクスを取得"""
    try:
        if metric_name:
            # 特定のメトリクス
            summary = performance_monitor.get_metrics_summary(metric_name, hours)
            return {
                "metric_name": metric_name,
                "summary": summary,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            # 全メトリクスの要約
            all_metrics = {}
            for name in performance_monitor.metrics.keys():
                all_metrics[name] = performance_monitor.get_metrics_summary(name, hours)
            
            return {
                "all_metrics": all_metrics,
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error("Failed to get performance metrics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get performance metrics")


@router.get("/metrics/cache")
async def get_cache_metrics():
    """キャッシュメトリクスを取得"""
    try:
        cache_stats = cache_manager.get_stats()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "cache_stats": cache_stats,
            "recommendations": _generate_cache_recommendations(cache_stats)
        }
        
    except Exception as e:
        logger.error("Failed to get cache metrics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get cache metrics")


@router.get("/metrics/tasks")
async def get_task_metrics():
    """タスクキューメトリクスを取得"""
    try:
        task_stats = task_queue.get_stats()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "task_stats": task_stats,
            "recommendations": _generate_task_recommendations(task_stats)
        }
        
    except Exception as e:
        logger.error("Failed to get task metrics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get task metrics")


@router.get("/metrics/video_processing")
async def get_video_processing_metrics():
    """動画処理メトリクスを取得"""
    try:
        video_stats = optimized_video_processor.get_optimization_stats()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "video_processing_stats": video_stats
        }
        
    except Exception as e:
        logger.error("Failed to get video processing metrics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get video processing metrics")


@router.get("/alerts")
async def get_performance_alerts(
    hours: int = Query(24, description="取得する時間範囲（時間）"),
    severity: Optional[str] = Query(None, description="アラートの重要度フィルタ")
):
    """パフォーマンスアラートを取得"""
    try:
        alerts = performance_monitor.get_active_alerts(hours)
        
        if severity:
            alerts = [a for a in alerts if a["severity"] == severity]
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "alerts": alerts,
            "total_count": len(alerts),
            "severity_breakdown": _count_alerts_by_severity(alerts)
        }
        
    except Exception as e:
        logger.error("Failed to get performance alerts", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get performance alerts")


@router.get("/optimization/suggestions")
async def get_optimization_suggestions():
    """最適化提案を取得"""
    try:
        # システムメトリクス取得
        system_metrics = await get_system_metrics()
        cache_stats = cache_manager.get_stats()
        task_stats = task_queue.get_stats()
        
        suggestions = []
        
        # CPU使用率チェック
        if system_metrics["cpu"]["usage_percent"] > 80:
            suggestions.append({
                "category": "cpu",
                "priority": "high",
                "title": "High CPU Usage Detected",
                "description": f"CPU usage is {system_metrics['cpu']['usage_percent']:.1f}%. Consider optimizing CPU-intensive operations.",
                "actions": [
                    "Reduce MediaPipe model complexity",
                    "Implement frame skipping",
                    "Use batch processing"
                ]
            })
        
        # メモリ使用率チェック
        if system_metrics["memory"]["percent"] > 85:
            suggestions.append({
                "category": "memory",
                "priority": "high",
                "title": "High Memory Usage Detected",
                "description": f"Memory usage is {system_metrics['memory']['percent']:.1f}%. Consider memory optimization.",
                "actions": [
                    "Force garbage collection",
                    "Optimize NumPy array usage",
                    "Clear unused caches"
                ]
            })
        
        # キャッシュヒット率チェック
        if cache_stats["hit_rate_percent"] < 70:
            suggestions.append({
                "category": "cache",
                "priority": "medium",
                "title": "Low Cache Hit Rate",
                "description": f"Cache hit rate is {cache_stats['hit_rate_percent']:.1f}%. Consider cache optimization.",
                "actions": [
                    "Increase cache TTL for stable data",
                    "Pre-warm frequently accessed data",
                    "Review cache key strategies"
                ]
            })
        
        # タスクキューサイズチェック
        if task_stats["queue_size"] > 50:
            suggestions.append({
                "category": "tasks",
                "priority": "medium",
                "title": "Large Task Queue",
                "description": f"Task queue has {task_stats['queue_size']} pending tasks.",
                "actions": [
                    "Increase worker count",
                    "Optimize task processing time",
                    "Implement task prioritization"
                ]
            })
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "suggestions": suggestions,
            "total_count": len(suggestions),
            "priority_breakdown": _count_suggestions_by_priority(suggestions)
        }
        
    except Exception as e:
        logger.error("Failed to generate optimization suggestions", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to generate optimization suggestions")


@router.post("/optimization/apply")
async def apply_optimization(
    optimization_type: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """最適化を適用"""
    if current_user.user_type not in ["admin", "professional"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        result = {"applied": False, "message": ""}
        
        if optimization_type == "force_gc":
            # ガベージコレクション強制実行
            import gc
            collected = gc.collect()
            result = {
                "applied": True,
                "message": f"Garbage collection completed. {collected} objects collected."
            }
            
        elif optimization_type == "clear_cache":
            # キャッシュクリア
            cache_manager.local_cache.clear()
            result = {
                "applied": True,
                "message": "Local cache cleared successfully."
            }
            
        elif optimization_type == "restart_workers":
            # ワーカー再起動
            await task_queue.stop_workers()
            await task_queue.start_workers()
            result = {
                "applied": True,
                "message": "Task queue workers restarted successfully."
            }
            
        else:
            raise HTTPException(status_code=400, detail="Unknown optimization type")
        
        logger.info("Optimization applied",
                   type=optimization_type,
                   user_id=current_user.id,
                   result=result)
        
        return result
        
    except Exception as e:
        logger.error("Failed to apply optimization", 
                    type=optimization_type, 
                    error=str(e))
        raise HTTPException(status_code=500, detail="Failed to apply optimization")


@router.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard_html():
    """パフォーマンスダッシュボードのHTML"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Gait Analysis Performance Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .metric-card { 
                border: 1px solid #ddd; 
                border-radius: 8px; 
                padding: 16px; 
                margin: 10px 0; 
                background: #f9f9f9; 
            }
            .metric-value { font-size: 2em; font-weight: bold; color: #333; }
            .metric-label { color: #666; margin-top: 5px; }
            .alert-high { border-left: 4px solid #ff4444; }
            .alert-medium { border-left: 4px solid #ffaa00; }
            .alert-low { border-left: 4px solid #44ff44; }
            .chart-container { width: 100%; height: 300px; margin: 20px 0; }
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        </style>
    </head>
    <body>
        <h1>🚀 Gait Analysis Performance Dashboard</h1>
        
        <div class="grid" id="metrics-grid">
            <!-- メトリクスカードがここに動的に追加される -->
        </div>
        
        <div class="chart-container">
            <canvas id="performance-chart"></canvas>
        </div>
        
        <div id="alerts-section">
            <h2>🚨 Active Alerts</h2>
            <div id="alerts-list">
                <!-- アラートがここに表示される -->
            </div>
        </div>
        
        <div id="suggestions-section">
            <h2>💡 Optimization Suggestions</h2>
            <div id="suggestions-list">
                <!-- 提案がここに表示される -->
            </div>
        </div>
        
        <script>
            // ダッシュボード更新関数
            async function updateDashboard() {
                try {
                    // システムメトリクス取得
                    const systemResponse = await fetch('/api/v1/performance/metrics/system');
                    const systemData = await systemResponse.json();
                    
                    // キャッシュメトリクス取得
                    const cacheResponse = await fetch('/api/v1/performance/metrics/cache');
                    const cacheData = await cacheResponse.json();
                    
                    // アラート取得
                    const alertsResponse = await fetch('/api/v1/performance/alerts');
                    const alertsData = await alertsResponse.json();
                    
                    // 提案取得
                    const suggestionsResponse = await fetch('/api/v1/performance/optimization/suggestions');
                    const suggestionsData = await suggestionsResponse.json();
                    
                    // メトリクス表示更新
                    updateMetricsDisplay(systemData, cacheData);
                    
                    // アラート表示更新
                    updateAlertsDisplay(alertsData.alerts);
                    
                    // 提案表示更新
                    updateSuggestionsDisplay(suggestionsData.suggestions);
                    
                } catch (error) {
                    console.error('Dashboard update failed:', error);
                }
            }
            
            function updateMetricsDisplay(systemData, cacheData) {
                const grid = document.getElementById('metrics-grid');
                grid.innerHTML = `
                    <div class="metric-card">
                        <div class="metric-value">${systemData.cpu.usage_percent.toFixed(1)}%</div>
                        <div class="metric-label">CPU Usage</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${systemData.memory.percent.toFixed(1)}%</div>
                        <div class="metric-label">Memory Usage</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${systemData.process.process_mb.toFixed(0)} MB</div>
                        <div class="metric-label">Process Memory</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${cacheData.cache_stats.hit_rate_percent.toFixed(1)}%</div>
                        <div class="metric-label">Cache Hit Rate</div>
                    </div>
                `;
            }
            
            function updateAlertsDisplay(alerts) {
                const alertsList = document.getElementById('alerts-list');
                if (alerts.length === 0) {
                    alertsList.innerHTML = '<p>✅ No active alerts</p>';
                } else {
                    alertsList.innerHTML = alerts.map(alert => `
                        <div class="metric-card alert-${alert.severity}">
                            <strong>${alert.metric}</strong>: ${alert.value} (threshold: ${alert.threshold})
                            <br><small>${new Date(alert.timestamp).toLocaleString()}</small>
                        </div>
                    `).join('');
                }
            }
            
            function updateSuggestionsDisplay(suggestions) {
                const suggestionsList = document.getElementById('suggestions-list');
                if (suggestions.length === 0) {
                    suggestionsList.innerHTML = '<p>✅ No optimization suggestions</p>';
                } else {
                    suggestionsList.innerHTML = suggestions.map(suggestion => `
                        <div class="metric-card alert-${suggestion.priority}">
                            <strong>${suggestion.title}</strong>
                            <p>${suggestion.description}</p>
                            <ul>
                                ${suggestion.actions.map(action => `<li>${action}</li>`).join('')}
                            </ul>
                        </div>
                    `).join('');
                }
            }
            
            // 初期ロードとタイマー設定
            updateDashboard();
            setInterval(updateDashboard, 30000); // 30秒ごとに更新
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)


def _generate_cache_recommendations(cache_stats: Dict[str, Any]) -> List[str]:
    """キャッシュの推奨事項を生成"""
    recommendations = []
    
    if cache_stats["hit_rate_percent"] < 70:
        recommendations.append("キャッシュヒット率が低いです。TTLの調整を検討してください")
    
    if cache_stats["local_cache_size"] > 1000:
        recommendations.append("ローカルキャッシュサイズが大きいです。定期的なクリーンアップを実行してください")
    
    if not cache_stats["redis_available"]:
        recommendations.append("Redisが利用できません。分散キャッシュの設定を確認してください")
    
    return recommendations


def _generate_task_recommendations(task_stats: Dict[str, Any]) -> List[str]:
    """タスクキューの推奨事項を生成"""
    recommendations = []
    
    if task_stats["queue_size"] > 50:
        recommendations.append("タスクキューのサイズが大きいです。ワーカー数の増加を検討してください")
    
    if task_stats["average_processing_time"] > 5.0:
        recommendations.append("平均処理時間が長いです。タスクの最適化を検討してください")
    
    if task_stats["tasks_failed"] > task_stats["tasks_processed"] * 0.05:
        recommendations.append("タスク失敗率が高いです。エラーハンドリングの改善を検討してください")
    
    return recommendations


def _count_alerts_by_severity(alerts: List[Dict[str, Any]]) -> Dict[str, int]:
    """重要度別のアラート数をカウント"""
    counts = {"critical": 0, "warning": 0}
    for alert in alerts:
        severity = alert.get("severity", "warning")
        counts[severity] = counts.get(severity, 0) + 1
    return counts


def _count_suggestions_by_priority(suggestions: List[Dict[str, Any]]) -> Dict[str, int]:
    """優先度別の提案数をカウント"""
    counts = {"high": 0, "medium": 0, "low": 0}
    for suggestion in suggestions:
        priority = suggestion.get("priority", "low")
        counts[priority] = counts.get(priority, 0) + 1
    return counts