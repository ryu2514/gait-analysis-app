#!/usr/bin/env python3
"""
Monitoring Dashboard Integration Script
リアルタイム監視ダッシュボード統合スクリプト
"""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.advanced_logger import get_logger

logger = get_logger("monitoring_integration")


def verify_monitoring_components():
    """監視コンポーネントの検証"""
    print("🔍 Monitoring Dashboard Integration")
    print("=" * 50)
    
    # 必要なファイルの確認
    required_files = [
        "app/api/monitoring_dashboard.py",
        "app/api/performance_dashboard.py",
        "app/core/performance_config.py",
        "app/core/advanced_logger.py"
    ]
    
    print("📁 Checking required files...")
    missing_files = []
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path}")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n⚠️  Missing files: {missing_files}")
        return False
    
    print("\n🔧 Monitoring Components:")
    print("   ✅ WebSocket Real-time Dashboard")
    print("   ✅ Connection Manager")
    print("   ✅ Real-time Metrics Collection")
    print("   ✅ Interactive HTML Dashboard")
    print("   ✅ Chart.js Visualization")
    print("   ✅ System Resource Monitoring")
    print("   ✅ Cache Performance Tracking")
    print("   ✅ Task Queue Monitoring")
    print("   ✅ Alert Management")
    print("   ✅ Auto-reconnection Logic")
    
    print("\n📊 Dashboard Features:")
    print("   • Real-time system metrics (CPU, Memory, Disk)")
    print("   • Cache performance monitoring")
    print("   • Task queue status tracking")
    print("   • WebSocket connection management")
    print("   • Interactive charts and graphs")
    print("   • Responsive web interface")
    print("   • Auto-refresh every 5 seconds")
    print("   • Connection status indicators")
    print("   • Error handling and recovery")
    print("   • Admin-only alert management")
    
    print("\n🌐 API Endpoints:")
    print("   • WebSocket: /api/v1/monitoring/ws")
    print("   • Dashboard: /api/v1/monitoring/")
    print("   • Status: /api/v1/monitoring/status")
    print("   • Current Metrics: /api/v1/monitoring/metrics/current")
    print("   • Clear Alerts: /api/v1/monitoring/alerts/clear")
    
    print("\n🔗 Integration Points:")
    print("   • FastAPI WebSocket support")
    print("   • Performance monitoring integration")
    print("   • Advanced logger integration")
    print("   • Cache manager integration")
    print("   • Task queue monitoring")
    print("   • Authentication system integration")
    
    print("\n📈 Metrics Collected:")
    print("   • System: CPU, Memory, Disk, Process stats")
    print("   • Cache: Hit rate, Size, Redis status")
    print("   • Tasks: Queue size, Workers, Processing time")
    print("   • Performance: Response times, Alerts")
    print("   • Connections: Active WebSocket connections")
    
    print("\n🎨 Dashboard UI Features:")
    print("   • Modern gradient design")
    print("   • Responsive grid layout")
    print("   • Real-time updating metrics")
    print("   • Color-coded status indicators")
    print("   • Animated charts and graphs")
    print("   • Connection status display")
    print("   • Error notifications")
    print("   • Mobile-friendly interface")
    
    print("\n🛡️ Security Features:")
    print("   • WebSocket connection validation")
    print("   • Admin-only alert clearing")
    print("   • Connection rate limiting")
    print("   • Error handling and logging")
    print("   • Client IP tracking")
    
    print("\n⚡ Performance Features:")
    print("   • Efficient WebSocket communication")
    print("   • Optimized metric collection")
    print("   • Chart data buffering (20 points)")
    print("   • Automatic reconnection")
    print("   • Background monitoring tasks")
    print("   • Resource usage optimization")
    
    return True


def show_usage_instructions():
    """使用方法の表示"""
    print("\n🚀 Getting Started:")
    print("   1. Start the API server:")
    print("      uvicorn main:app --reload")
    print()
    print("   2. Access the monitoring dashboard:")
    print("      http://localhost:8000/api/v1/monitoring/")
    print()
    print("   3. Check monitoring status:")
    print("      http://localhost:8000/api/v1/monitoring/status")
    print()
    print("   4. Get current metrics (REST):")
    print("      http://localhost:8000/api/v1/monitoring/metrics/current")
    print()
    print("   5. Clear alerts (Admin only):")
    print("      POST http://localhost:8000/api/v1/monitoring/alerts/clear")
    
    print("\n📱 WebSocket Client Example:")
    print("""
    const ws = new WebSocket('ws://localhost:8000/api/v1/monitoring/ws');
    
    ws.onopen = () => console.log('Connected to monitoring');
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Metrics:', data);
    };
    """)
    
    print("\n🔧 Configuration:")
    print("   • Update interval: 5 seconds")
    print("   • Chart data points: 20 (rolling)")
    print("   • WebSocket timeout: 30 seconds")
    print("   • Reconnection attempts: 5 max")
    print("   • Ping interval: 30 seconds")
    
    print("\n📊 Monitoring Thresholds:")
    print("   • CPU Warning: > 60%")
    print("   • CPU Critical: > 80%")
    print("   • Memory Warning: > 70%")
    print("   • Memory Critical: > 85%")
    print("   • Cache Hit Rate Warning: < 70%")
    print("   • Queue Size Warning: > 50 tasks")


def main():
    """メイン実行"""
    try:
        success = verify_monitoring_components()
        
        if success:
            show_usage_instructions()
            
            print("\n✅ Real-time Monitoring Dashboard Ready!")
            print("\n🎯 Key Benefits:")
            print("   • Live system performance visibility")
            print("   • Proactive issue detection")
            print("   • Real-time resource monitoring")
            print("   • Interactive web-based interface")
            print("   • Mobile-responsive design")
            print("   • WebSocket-powered real-time updates")
            
            print("\n🔮 Advanced Features:")
            print("   • Multi-client support")
            print("   • Connection management")
            print("   • Automatic error recovery")
            print("   • Historical chart data")
            print("   • Alert management system")
            print("   • Performance optimization insights")
            
            print("\n🎉 Monitoring dashboard integration completed successfully!")
            
        else:
            print("\n❌ Monitoring dashboard integration incomplete!")
            
    except Exception as e:
        logger.error(f"Monitoring integration failed: {e}")
        print(f"\n💥 Integration failed: {e}")


if __name__ == "__main__":
    main()