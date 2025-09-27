"""
Real-time Monitoring Dashboard
リアルタイム監視ダッシュボード
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.responses import HTMLResponse
from typing import Dict, List, Any, Optional
import asyncio
import json
import time
from datetime import datetime
import psutil

from app.core.advanced_logger import get_logger
from app.core.performance_config import cache_manager, performance_monitor, task_queue
from app.core.auth import get_current_user
from app.models.user_models import UserResponse

router = APIRouter()
logger = get_logger("monitoring_dashboard")


class ConnectionManager:
    """WebSocket接続管理クラス"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.client_info: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, client_info: Dict[str, Any] = None):
        """新しい接続を受け入れ"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.client_info[websocket] = client_info or {}
        logger.info(f"WebSocket connection established. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """接続を切断"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.client_info:
            del self.client_info[websocket]
        logger.info(f"WebSocket connection closed. Total connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """特定の接続にメッセージを送信"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: str):
        """すべての接続にブロードキャスト"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Failed to broadcast to connection: {e}")
                disconnected.append(connection)
        
        # 切断された接続を削除
        for connection in disconnected:
            self.disconnect(connection)


# グローバル接続マネージャー
manager = ConnectionManager()


async def get_real_time_metrics() -> Dict[str, Any]:
    """リアルタイムメトリクスを取得"""
    try:
        # システムメトリクス
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # プロセスメトリクス
        process = psutil.Process()
        process_memory = process.memory_info()
        
        # キャッシュメトリクス
        cache_stats = cache_manager.get_stats()
        
        # タスクキューメトリクス
        task_stats = task_queue.get_stats()
        
        # パフォーマンスメトリクス（最新値）
        perf_metrics = {}
        for metric_name in performance_monitor.metrics.keys():
            summary = performance_monitor.get_metrics_summary(metric_name, hours=0.1)
            if summary:
                perf_metrics[metric_name] = summary.get("latest", 0)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_gb": round(memory.used / (1024**3), 2),
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_percent": round((disk.used / disk.total) * 100, 2),
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "process_memory_mb": round(process_memory.rss / (1024**2), 2),
                "process_threads": process.num_threads()
            },
            "cache": {
                "hit_rate": cache_stats.get("hit_rate_percent", 0),
                "local_size": cache_stats.get("local_cache_size", 0),
                "redis_available": cache_stats.get("redis_available", False),
                "total_hits": cache_stats.get("hits", 0),
                "total_misses": cache_stats.get("misses", 0)
            },
            "tasks": {
                "queue_size": task_stats.get("queue_size", 0),
                "active_workers": task_stats.get("active_workers", 0),
                "processed": task_stats.get("tasks_processed", 0),
                "failed": task_stats.get("tasks_failed", 0),
                "avg_processing_time": task_stats.get("average_processing_time", 0)
            },
            "performance": perf_metrics,
            "alerts": len(performance_monitor.get_active_alerts(hours=1)),
            "connections": len(manager.active_connections)
        }
        
    except Exception as e:
        logger.error(f"Failed to get real-time metrics: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


async def monitor_system():
    """システム監視バックグラウンドタスク"""
    while True:
        try:
            if manager.active_connections:
                metrics = await get_real_time_metrics()
                message = json.dumps({
                    "type": "metrics_update",
                    "data": metrics
                })
                await manager.broadcast(message)
            
            await asyncio.sleep(5)  # 5秒ごとに更新
            
        except Exception as e:
            logger.error(f"System monitoring error: {e}")
            await asyncio.sleep(10)  # エラー時は10秒待機


# バックグラウンド監視タスクを開始
monitor_task = None


@router.on_event("startup")
async def start_monitoring():
    """監視タスクを開始"""
    global monitor_task
    monitor_task = asyncio.create_task(monitor_system())
    logger.info("Real-time monitoring started")


@router.on_event("shutdown")
async def stop_monitoring():
    """監視タスクを停止"""
    global monitor_task
    if monitor_task:
        monitor_task.cancel()
        try:
            await monitor_task
        except asyncio.CancelledError:
            pass
    logger.info("Real-time monitoring stopped")


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocketエンドポイント"""
    client_ip = websocket.client.host if websocket.client else "unknown"
    
    await manager.connect(websocket, {
        "client_ip": client_ip,
        "connected_at": datetime.utcnow().isoformat()
    })
    
    try:
        # 初期データを送信
        initial_metrics = await get_real_time_metrics()
        await manager.send_personal_message(
            json.dumps({
                "type": "initial_data",
                "data": initial_metrics
            }),
            websocket
        )
        
        # クライアントからのメッセージを待機
        while True:
            try:
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                data = json.loads(message)
                
                # メッセージタイプに応じて処理
                if data.get("type") == "ping":
                    await manager.send_personal_message(
                        json.dumps({"type": "pong", "timestamp": datetime.utcnow().isoformat()}),
                        websocket
                    )
                elif data.get("type") == "request_metrics":
                    metrics = await get_real_time_metrics()
                    await manager.send_personal_message(
                        json.dumps({"type": "metrics_update", "data": metrics}),
                        websocket
                    )
                
            except asyncio.TimeoutError:
                # タイムアウト時はping送信
                await manager.send_personal_message(
                    json.dumps({"type": "ping", "timestamp": datetime.utcnow().isoformat()}),
                    websocket
                )
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@router.get("/", response_class=HTMLResponse)
async def get_monitoring_dashboard():
    """リアルタイム監視ダッシュボードのHTML"""
    
    html_content = """
    <!DOCTYPE html>
    <html lang="ja">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🔍 Real-time Monitoring Dashboard</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
                min-height: 100vh;
                padding: 20px;
            }
            
            .dashboard-header {
                text-align: center;
                color: white;
                margin-bottom: 30px;
            }
            
            .dashboard-header h1 {
                font-size: 2.5rem;
                margin-bottom: 10px;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }
            
            .status-bar {
                display: flex;
                justify-content: center;
                align-items: center;
                gap: 20px;
                margin-bottom: 20px;
                flex-wrap: wrap;
            }
            
            .status-item {
                background: rgba(255, 255, 255, 0.2);
                padding: 10px 20px;
                border-radius: 25px;
                color: white;
                font-weight: bold;
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
            
            .status-connected { border-color: #4CAF50; }
            .status-disconnected { border-color: #f44336; }
            
            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            
            .metric-card {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 15px;
                padding: 20px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.2);
                transition: transform 0.3s ease;
            }
            
            .metric-card:hover {
                transform: translateY(-5px);
            }
            
            .metric-card h3 {
                color: #333;
                margin-bottom: 15px;
                font-size: 1.2rem;
                border-bottom: 2px solid #667eea;
                padding-bottom: 10px;
            }
            
            .metric-value {
                font-size: 2rem;
                font-weight: bold;
                margin-bottom: 5px;
            }
            
            .metric-label {
                color: #666;
                font-size: 0.9rem;
            }
            
            .metric-row {
                display: flex;
                justify-content: space-between;
                margin-bottom: 10px;
                padding: 8px 0;
                border-bottom: 1px solid #eee;
            }
            
            .chart-container {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 15px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            }
            
            .chart-container h3 {
                margin-bottom: 20px;
                color: #333;
                border-bottom: 2px solid #667eea;
                padding-bottom: 10px;
            }
            
            .alerts-section {
                background: rgba(255, 255, 255, 0.95);
                border-radius: 15px;
                padding: 20px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            }
            
            .alert-item {
                padding: 10px;
                margin-bottom: 10px;
                border-radius: 8px;
                border-left: 4px solid;
            }
            
            .alert-high { border-color: #f44336; background: #ffebee; }
            .alert-medium { border-color: #ff9800; background: #fff3e0; }
            .alert-low { border-color: #4caf50; background: #e8f5e8; }
            
            .loading {
                text-align: center;
                padding: 40px;
                color: white;
                font-size: 1.2rem;
            }
            
            .error {
                background: rgba(244, 67, 54, 0.9);
                color: white;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
                text-align: center;
            }
            
            @keyframes pulse {
                0% { opacity: 1; }
                50% { opacity: 0.7; }
                100% { opacity: 1; }
            }
            
            .pulse {
                animation: pulse 2s infinite;
            }
            
            .footer {
                text-align: center;
                color: rgba(255, 255, 255, 0.8);
                margin-top: 30px;
                font-size: 0.9rem;
            }
        </style>
    </head>
    <body>
        <div class="dashboard-header">
            <h1>🔍 Real-time Monitoring Dashboard</h1>
            <p>Gait Analysis API System Monitor</p>
        </div>
        
        <div class="status-bar">
            <div id="connection-status" class="status-item status-disconnected">
                🔴 Disconnected
            </div>
            <div id="last-update" class="status-item">
                ⏱️ Last Update: Never
            </div>
            <div id="active-connections" class="status-item">
                👥 Connections: 0
            </div>
        </div>
        
        <div id="error-container"></div>
        <div id="loading" class="loading">🔄 Connecting to monitoring service...</div>
        
        <div id="dashboard-content" style="display: none;">
            <div class="metrics-grid">
                <!-- System Metrics -->
                <div class="metric-card">
                    <h3>🖥️ System Resources</h3>
                    <div class="metric-row">
                        <span>CPU Usage</span>
                        <span id="cpu-usage" class="metric-value">0%</span>
                    </div>
                    <div class="metric-row">
                        <span>Memory Usage</span>
                        <span id="memory-usage" class="metric-value">0%</span>
                    </div>
                    <div class="metric-row">
                        <span>Disk Usage</span>
                        <span id="disk-usage" class="metric-value">0%</span>
                    </div>
                    <div class="metric-row">
                        <span>Process Memory</span>
                        <span id="process-memory" class="metric-value">0 MB</span>
                    </div>
                </div>
                
                <!-- Cache Metrics -->
                <div class="metric-card">
                    <h3>🗄️ Cache Performance</h3>
                    <div class="metric-row">
                        <span>Hit Rate</span>
                        <span id="cache-hit-rate" class="metric-value">0%</span>
                    </div>
                    <div class="metric-row">
                        <span>Local Cache Size</span>
                        <span id="cache-size" class="metric-value">0</span>
                    </div>
                    <div class="metric-row">
                        <span>Redis Status</span>
                        <span id="redis-status" class="metric-value">❌</span>
                    </div>
                    <div class="metric-row">
                        <span>Total Hits</span>
                        <span id="cache-hits" class="metric-value">0</span>
                    </div>
                </div>
                
                <!-- Task Queue Metrics -->
                <div class="metric-card">
                    <h3>⚙️ Task Queue</h3>
                    <div class="metric-row">
                        <span>Queue Size</span>
                        <span id="queue-size" class="metric-value">0</span>
                    </div>
                    <div class="metric-row">
                        <span>Active Workers</span>
                        <span id="active-workers" class="metric-value">0</span>
                    </div>
                    <div class="metric-row">
                        <span>Processed</span>
                        <span id="tasks-processed" class="metric-value">0</span>
                    </div>
                    <div class="metric-row">
                        <span>Failed</span>
                        <span id="tasks-failed" class="metric-value">0</span>
                    </div>
                </div>
                
                <!-- Performance Metrics -->
                <div class="metric-card">
                    <h3>📊 Performance</h3>
                    <div class="metric-row">
                        <span>Active Alerts</span>
                        <span id="active-alerts" class="metric-value">0</span>
                    </div>
                    <div class="metric-row">
                        <span>Avg Processing Time</span>
                        <span id="avg-processing-time" class="metric-value">0ms</span>
                    </div>
                    <div class="metric-row">
                        <span>Connected Clients</span>
                        <span id="connected-clients" class="metric-value">0</span>
                    </div>
                </div>
            </div>
            
            <!-- Charts -->
            <div class="chart-container">
                <h3>📈 Real-time System Metrics</h3>
                <canvas id="system-chart" width="400" height="200"></canvas>
            </div>
            
            <!-- Alerts -->
            <div class="alerts-section">
                <h3>🚨 System Alerts</h3>
                <div id="alerts-list">
                    <div class="alert-item alert-low">✅ No active alerts</div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>Real-time monitoring powered by WebSocket | Updates every 5 seconds</p>
            <p>© 2024 Gait Analysis API</p>
        </div>
        
        <script>
            class MonitoringDashboard {
                constructor() {
                    this.ws = null;
                    this.reconnectAttempts = 0;
                    this.maxReconnectAttempts = 5;
                    this.reconnectDelay = 1000;
                    this.chart = null;
                    this.chartData = {
                        labels: [],
                        datasets: [
                            {
                                label: 'CPU %',
                                data: [],
                                borderColor: '#ff6384',
                                tension: 0.1
                            },
                            {
                                label: 'Memory %',
                                data: [],
                                borderColor: '#36a2eb',
                                tension: 0.1
                            },
                            {
                                label: 'Cache Hit Rate %',
                                data: [],
                                borderColor: '#4bc0c0',
                                tension: 0.1
                            }
                        ]
                    };
                    
                    this.initChart();
                    this.connect();
                }
                
                initChart() {
                    const ctx = document.getElementById('system-chart').getContext('2d');
                    this.chart = new Chart(ctx, {
                        type: 'line',
                        data: this.chartData,
                        options: {
                            responsive: true,
                            scales: {
                                y: {
                                    beginAtZero: true,
                                    max: 100
                                }
                            },
                            plugins: {
                                legend: {
                                    display: true
                                }
                            }
                        }
                    });
                }
                
                connect() {
                    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                    const wsUrl = `${protocol}//${window.location.host}/api/v1/monitoring/ws`;
                    
                    try {
                        this.ws = new WebSocket(wsUrl);
                        
                        this.ws.onopen = () => {
                            console.log('WebSocket connected');
                            this.updateConnectionStatus(true);
                            this.reconnectAttempts = 0;
                            document.getElementById('loading').style.display = 'none';
                            document.getElementById('dashboard-content').style.display = 'block';
                        };
                        
                        this.ws.onmessage = (event) => {
                            try {
                                const message = JSON.parse(event.data);
                                this.handleMessage(message);
                            } catch (error) {
                                console.error('Failed to parse message:', error);
                            }
                        };
                        
                        this.ws.onclose = () => {
                            console.log('WebSocket disconnected');
                            this.updateConnectionStatus(false);
                            this.attemptReconnect();
                        };
                        
                        this.ws.onerror = (error) => {
                            console.error('WebSocket error:', error);
                            this.showError('WebSocket connection error');
                        };
                        
                    } catch (error) {
                        console.error('Failed to create WebSocket:', error);
                        this.showError('Failed to establish connection');
                    }
                }
                
                handleMessage(message) {
                    switch (message.type) {
                        case 'initial_data':
                        case 'metrics_update':
                            this.updateMetrics(message.data);
                            break;
                        case 'pong':
                            console.log('Received pong');
                            break;
                        default:
                            console.log('Unknown message type:', message.type);
                    }
                }
                
                updateMetrics(data) {
                    if (data.error) {
                        this.showError(`Metrics error: ${data.error}`);
                        return;
                    }
                    
                    // Update last update time
                    document.getElementById('last-update').textContent = 
                        `⏱️ Last Update: ${new Date(data.timestamp).toLocaleTimeString()}`;
                    
                    // Update system metrics
                    if (data.system) {
                        document.getElementById('cpu-usage').textContent = `${data.system.cpu_percent.toFixed(1)}%`;
                        document.getElementById('memory-usage').textContent = `${data.system.memory_percent.toFixed(1)}%`;
                        document.getElementById('disk-usage').textContent = `${data.system.disk_percent.toFixed(1)}%`;
                        document.getElementById('process-memory').textContent = `${data.system.process_memory_mb} MB`;
                        
                        // Update CPU color based on usage
                        const cpuElement = document.getElementById('cpu-usage');
                        if (data.system.cpu_percent > 80) {
                            cpuElement.style.color = '#f44336';
                        } else if (data.system.cpu_percent > 60) {
                            cpuElement.style.color = '#ff9800';
                        } else {
                            cpuElement.style.color = '#4caf50';
                        }
                    }
                    
                    // Update cache metrics
                    if (data.cache) {
                        document.getElementById('cache-hit-rate').textContent = `${data.cache.hit_rate.toFixed(1)}%`;
                        document.getElementById('cache-size').textContent = data.cache.local_size;
                        document.getElementById('redis-status').textContent = data.cache.redis_available ? '✅' : '❌';
                        document.getElementById('cache-hits').textContent = data.cache.total_hits;
                    }
                    
                    // Update task queue metrics
                    if (data.tasks) {
                        document.getElementById('queue-size').textContent = data.tasks.queue_size;
                        document.getElementById('active-workers').textContent = data.tasks.active_workers;
                        document.getElementById('tasks-processed').textContent = data.tasks.processed;
                        document.getElementById('tasks-failed').textContent = data.tasks.failed;
                        document.getElementById('avg-processing-time').textContent = 
                            `${(data.tasks.avg_processing_time * 1000).toFixed(0)}ms`;
                    }
                    
                    // Update performance metrics
                    document.getElementById('active-alerts').textContent = data.alerts || 0;
                    document.getElementById('connected-clients').textContent = data.connections || 0;
                    document.getElementById('active-connections').textContent = `👥 Connections: ${data.connections || 0}`;
                    
                    // Update chart
                    this.updateChart(data);
                    
                    // Clear any errors
                    this.clearError();
                }
                
                updateChart(data) {
                    const now = new Date().toLocaleTimeString();
                    
                    // Add new data point
                    this.chartData.labels.push(now);
                    this.chartData.datasets[0].data.push(data.system?.cpu_percent || 0);
                    this.chartData.datasets[1].data.push(data.system?.memory_percent || 0);
                    this.chartData.datasets[2].data.push(data.cache?.hit_rate || 0);
                    
                    // Keep only last 20 data points
                    if (this.chartData.labels.length > 20) {
                        this.chartData.labels.shift();
                        this.chartData.datasets.forEach(dataset => dataset.data.shift());
                    }
                    
                    this.chart.update('none');
                }
                
                updateConnectionStatus(connected) {
                    const statusElement = document.getElementById('connection-status');
                    if (connected) {
                        statusElement.textContent = '🟢 Connected';
                        statusElement.className = 'status-item status-connected';
                    } else {
                        statusElement.textContent = '🔴 Disconnected';
                        statusElement.className = 'status-item status-disconnected';
                    }
                }
                
                showError(message) {
                    const errorContainer = document.getElementById('error-container');
                    errorContainer.innerHTML = `<div class="error">❌ ${message}</div>`;
                }
                
                clearError() {
                    document.getElementById('error-container').innerHTML = '';
                }
                
                attemptReconnect() {
                    if (this.reconnectAttempts < this.maxReconnectAttempts) {
                        this.reconnectAttempts++;
                        setTimeout(() => {
                            console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
                            this.connect();
                        }, this.reconnectDelay * this.reconnectAttempts);
                    } else {
                        this.showError('Maximum reconnection attempts reached. Please refresh the page.');
                    }
                }
                
                sendPing() {
                    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                        this.ws.send(JSON.stringify({type: 'ping'}));
                    }
                }
            }
            
            // Initialize dashboard when page loads
            document.addEventListener('DOMContentLoaded', () => {
                const dashboard = new MonitoringDashboard();
                
                // Send ping every 30 seconds to keep connection alive
                setInterval(() => dashboard.sendPing(), 30000);
            });
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)


@router.get("/status")
async def get_monitoring_status():
    """監視システムの状態を取得"""
    try:
        current_metrics = await get_real_time_metrics()
        
        return {
            "monitoring_active": True,
            "active_connections": len(manager.active_connections),
            "last_metrics_timestamp": current_metrics.get("timestamp"),
            "system_health": {
                "cpu_ok": current_metrics.get("system", {}).get("cpu_percent", 0) < 80,
                "memory_ok": current_metrics.get("system", {}).get("memory_percent", 0) < 85,
                "cache_ok": current_metrics.get("cache", {}).get("hit_rate", 0) > 50,
                "tasks_ok": current_metrics.get("tasks", {}).get("queue_size", 0) < 50
            },
            "alerts_count": current_metrics.get("alerts", 0)
        }
        
    except Exception as e:
        logger.error(f"Failed to get monitoring status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get monitoring status")


@router.get("/metrics/current")
async def get_current_metrics():
    """現在のメトリクスを取得（REST API）"""
    try:
        return await get_real_time_metrics()
    except Exception as e:
        logger.error(f"Failed to get current metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get current metrics")


@router.post("/alerts/clear")
async def clear_alerts(current_user: UserResponse = Depends(get_current_user)):
    """アラートをクリア（管理者のみ）"""
    if current_user.user_type != "admin":
        raise HTTPException(status_code=403, detail="Admin privileges required")
    
    try:
        # アラートリストをクリア
        performance_monitor.alerts.clear()
        
        logger.info("Alerts cleared", user_id=current_user.id)
        return {"message": "All alerts cleared successfully"}
        
    except Exception as e:
        logger.error(f"Failed to clear alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear alerts")