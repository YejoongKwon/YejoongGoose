#!/usr/bin/env python3
"""
Flask 기반 자동매매 웹 앱

LangGraph 상태를 웹 UI로 모니터링하고 제어
"""

import sys
from pathlib import Path
from datetime import datetime
import logging

from flask import Flask, jsonify, request, render_template_string
from dotenv import load_dotenv

# 프로젝트 루트
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 환경 변수 로드
env_file = project_root / "config" / ".env"
if env_file.exists():
    load_dotenv(env_file)
else:
    load_dotenv(project_root / "config" / "settings.example.env")

from skills.trading_core.graph.graph_builder import build_trading_graph
from skills.trading_core.graph.state import create_initial_state

# Flask 앱 생성
app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 전역 상태 (실제로는 Redis나 DB 사용 권장)
current_state = None
trading_graph = None


# ========== HTML 템플릿 ==========

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>변동성 돌파 자동매매 봇</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #333; border-bottom: 3px solid #007bff; padding-bottom: 10px; }
        .status-card { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007bff; }
        .metric { display: inline-block; margin: 10px 20px 10px 0; }
        .metric-label { font-size: 12px; color: #666; }
        .metric-value { font-size: 24px; font-weight: bold; color: #333; }
        .positive { color: #28a745; }
        .negative { color: #dc3545; }
        .btn { padding: 10px 20px; margin: 5px; border: none; border-radius: 5px; cursor: pointer; font-size: 14px; }
        .btn-primary { background: #007bff; color: white; }
        .btn-danger { background: #dc3545; color: white; }
        .btn-success { background: #28a745; color: white; }
        .btn:hover { opacity: 0.8; }
        .timestamp { color: #999; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 변동성 돌파 자동매매 봇</h1>

        <div class="status-card">
            <h2>📊 현재 상태</h2>
            <div class="metric">
                <div class="metric-label">종목</div>
                <div class="metric-value">{{ state.symbol }} ({{ state.symbol_name or '로딩중' }})</div>
            </div>
            <div class="metric">
                <div class="metric-label">현재가</div>
                <div class="metric-value">{{ "{:,.0f}".format(state.current_price) }}원</div>
            </div>
            <div class="metric">
                <div class="metric-label">목표가</div>
                <div class="metric-value">{{ "{:,.0f}".format(state.target_price) }}원</div>
            </div>
            <div class="metric">
                <div class="metric-label">포지션</div>
                <div class="metric-value">{{ state.position_status }}</div>
            </div>
        </div>

        <div class="status-card">
            <h2>💰 손익 현황</h2>
            <div class="metric">
                <div class="metric-label">일일 손익</div>
                <div class="metric-value {{ 'positive' if state.daily_pnl > 0 else 'negative' }}">
                    {{ "{:,.0f}".format(state.daily_pnl) }}원 ({{ "{:.2f}".format(state.daily_pnl_pct * 100) }}%)
                </div>
            </div>
            <div class="metric">
                <div class="metric-label">미실현 손익</div>
                <div class="metric-value {{ 'positive' if state.unrealized_pnl > 0 else 'negative' }}">
                    {{ "{:,.0f}".format(state.unrealized_pnl) }}원 ({{ "{:.2f}".format(state.unrealized_pnl_pct * 100) }}%)
                </div>
            </div>
            <div class="metric">
                <div class="metric-label">총 자산</div>
                <div class="metric-value">{{ "{:,.0f}".format(state.total_asset) }}원</div>
            </div>
        </div>

        <div class="status-card">
            <h2>📈 거래 통계</h2>
            <div class="metric">
                <div class="metric-label">총 거래</div>
                <div class="metric-value">{{ state.total_trades }}회</div>
            </div>
            <div class="metric">
                <div class="metric-label">승리</div>
                <div class="metric-value positive">{{ state.winning_trades }}회</div>
            </div>
            <div class="metric">
                <div class="metric-label">패배</div>
                <div class="metric-value negative">{{ state.losing_trades }}회</div>
            </div>
            <div class="metric">
                <div class="metric-label">승률</div>
                <div class="metric-value">
                    {{ "{:.1f}".format((state.winning_trades / state.total_trades * 100) if state.total_trades > 0 else 0) }}%
                </div>
            </div>
        </div>

        <div class="status-card">
            <h2>⚙️ 제어</h2>
            <button class="btn btn-success" onclick="runOnce()">1회 실행</button>
            <button class="btn btn-primary" onclick="startAuto()">자동 실행 시작</button>
            <button class="btn btn-danger" onclick="stopAuto()">자동 실행 중단</button>
            <button class="btn btn-primary" onclick="location.reload()">새로고침</button>
        </div>

        <p class="timestamp">마지막 업데이트: {{ state.timestamp }}</p>
    </div>

    <script>
        function runOnce() {
            fetch('/api/run', { method: 'POST' })
                .then(r => r.json())
                .then(data => {
                    alert('실행 완료!');
                    location.reload();
                });
        }

        function startAuto() {
            alert('자동 실행 기능은 아직 구현되지 않았습니다.');
        }

        function stopAuto() {
            alert('자동 실행 중단 기능은 아직 구현되지 않았습니다.');
        }

        // 30초마다 자동 새로고침
        setInterval(() => location.reload(), 30000);
    </script>
</body>
</html>
"""


# ========== API 엔드포인트 ==========

@app.route('/')
def dashboard():
    """대시보드 페이지"""
    global current_state

    if current_state is None:
        # 초기 상태 생성 (trading_config.yaml에서 자동 로드)
        import os
        env_mode = os.getenv('ENV_MODE', None)  # None이면 YAML에서 읽음
        current_state = create_initial_state(
            symbol="069500",
            env_mode=env_mode
        )
        current_state['symbol_name'] = 'KODEX 200'

    return render_template_string(DASHBOARD_HTML, state=current_state)


@app.route('/api/status')
def get_status():
    """현재 상태 조회 API"""
    global current_state

    if current_state is None:
        return jsonify({"error": "상태가 초기화되지 않았습니다"}), 400

    return jsonify(current_state)


@app.route('/api/run', methods=['POST'])
def run_once():
    """1회 실행 API"""
    global current_state, trading_graph

    try:
        # 그래프 빌드 (처음 한 번만)
        if trading_graph is None:
            logger.info("LangGraph 빌드...")
            trading_graph = build_trading_graph()

        # 초기 상태가 없으면 생성 (trading_config.yaml에서 자동 로드)
        if current_state is None:
            current_state = create_initial_state(
                symbol="069500"
            )

        # 실행
        logger.info("LangGraph 실행...")
        result = trading_graph.invoke(current_state)

        # 상태 업데이트
        current_state = result

        return jsonify({
            "success": True,
            "message": "실행 완료",
            "state": current_state
        })

    except Exception as e:
        logger.error(f"실행 중 오류: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/reset', methods=['POST'])
def reset_state():
    """상태 초기화 API"""
    global current_state

    # trading_config.yaml에서 자동 로드
    current_state = create_initial_state(
        symbol="069500"
    )

    return jsonify({
        "success": True,
        "message": "상태가 초기화되었습니다"
    })


if __name__ == '__main__':
    import os

    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

    logger.info("=" * 80)
    logger.info("변동성 돌파 자동매매 봇 (LangGraph) 시작")
    logger.info("=" * 80)
    logger.info(f"Flask 앱: http://{host}:{port}")
    logger.info(f"모드: {os.getenv('ENV_MODE', 'demo')}")
    logger.info("=" * 80)

    app.run(host=host, port=port, debug=debug)
