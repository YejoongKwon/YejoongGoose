#!/usr/bin/env python3
"""
fetch_market_data_node 단독 테스트

Usage:
    python tests/test_fetch_market_data.py
    python tests/test_fetch_market_data.py --symbol 005930  # 삼성전자
    python tests/test_fetch_market_data.py --mode real      # 실전투자
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from skills.trading_core.graph.nodes import fetch_market_data_node
from skills.trading_core.graph.state import TradingState

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_test_state(symbol: str = "069500", env_mode: str = "demo") -> TradingState:
    """
    테스트용 TradingState 생성

    Args:
        symbol: 종목 코드 (기본값: KODEX 200)
        env_mode: 실행 모드 (demo | real)

    Returns:
        TradingState 초기 상태
    """
    state: TradingState = {
        # 기본 정보
        "symbol": symbol,
        "env_mode": env_mode,
        "timestamp": datetime.now().isoformat(),
        "iteration": 0,

        # 가격 정보 (초기값)
        "current_price": 0.0,
        "target_price": 0.0,
        "today_open": 0.0,
        "today_high": 0.0,
        "today_low": 0.0,
        "today_volume": 0,
        "yesterday_open": 0.0,
        "yesterday_high": 0.0,
        "yesterday_low": 0.0,
        "yesterday_close": 0.0,
        "yesterday_volume": 0,

        # 포지션 정보
        "position_status": "IDLE",
        "entry_price": None,
        "entry_time": None,
        "position_qty": 0,
        "highest_price": None,
        "lowest_price": None,

        # 매매 신호
        "should_buy": False,
        "should_sell": False,
        "buy_reason": None,
        "sell_reason": None,
        "order_qty": 0,

        # 계좌 정보
        "cash_balance": 1000000.0,
        "total_asset": 1000000.0,
        "initial_capital": 1000000.0,

        # 손익 정보
        "realized_pnl": 0.0,
        "realized_pnl_pct": 0.0,
        "unrealized_pnl": 0.0,
        "unrealized_pnl_pct": 0.0,
        "daily_pnl": 0.0,
        "daily_pnl_pct": 0.0,

        # 전략 파라미터
        "k_value": 0.5,
        "stop_loss_pct": -0.03,
        "take_profit_pct": 0.05,
        "max_position_size": 0.1,
        "max_daily_loss": -0.05,

        # 거래 통계
        "total_trades": 0,
        "winning_trades": 0,
        "losing_trades": 0,

        # 주문 상태
        "last_order_no": None,
        "last_order_status": None,
        "last_order_message": None,

        # 중단 플래그
        "trading_stopped": False,
        "stop_reason": None,
    }

    return state


def print_result(result: dict):
    """
    결과를 보기 좋게 출력

    Args:
        result: fetch_market_data_node 실행 결과
    """
    print("\n" + "="*80)
    print("fetch_market_data_node 테스트 결과")
    print("="*80)

    print("\n📊 기본 정보:")
    print(f"  - Timestamp: {result.get('timestamp', 'N/A')}")
    print(f"  - Iteration: {result.get('iteration', 0)}")

    print("\n💰 당일 시세:")
    print(f"  - 현재가: {result.get('current_price', 0):,.0f}원")
    print(f"  - 시가: {result.get('today_open', 0):,.0f}원")
    print(f"  - 고가: {result.get('today_high', 0):,.0f}원")
    print(f"  - 저가: {result.get('today_low', 0):,.0f}원")
    print(f"  - 거래량: {result.get('today_volume', 0):,}주")

    print("\n📈 전일 시세:")
    print(f"  - 시가: {result.get('yesterday_open', 0):,.0f}원")
    print(f"  - 고가: {result.get('yesterday_high', 0):,.0f}원")
    print(f"  - 저가: {result.get('yesterday_low', 0):,.0f}원")
    print(f"  - 종가: {result.get('yesterday_close', 0):,.0f}원")
    print(f"  - 거래량: {result.get('yesterday_volume', 0):,}주")

    # 전일 대비 계산
    if result.get('current_price', 0) > 0 and result.get('yesterday_close', 0) > 0:
        change = result['current_price'] - result['yesterday_close']
        change_pct = (change / result['yesterday_close']) * 100

        print(f"\n📊 전일 대비:")
        print(f"  - 변화: {change:,.0f}원 ({change_pct:+.2f}%)")

    # 변동성 계산 (목표가 계산용)
    if result.get('yesterday_high', 0) > 0 and result.get('yesterday_low', 0) > 0:
        volatility = result['yesterday_high'] - result['yesterday_low']
        print(f"\n📉 변동성 정보:")
        print(f"  - 전일 변동폭: {volatility:,.0f}원")
        print(f"  - 예상 목표가 (k=0.5): {result.get('today_open', 0) + (volatility * 0.5):,.0f}원")

    print("\n" + "="*80)


def main():
    """메인 테스트 함수"""
    parser = argparse.ArgumentParser(description='fetch_market_data_node 테스트')
    parser.add_argument(
        '--symbol',
        type=str,
        default='069500',
        help='종목 코드 (기본값: 069500 = KODEX 200)'
    )
    parser.add_argument(
        '--mode',
        type=str,
        choices=['demo', 'real'],
        default='demo',
        help='실행 모드 (기본값: demo)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='디버그 모드 활성화'
    )

    args = parser.parse_args()

    # 디버그 모드 설정
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    print("\n" + "="*80)
    print("fetch_market_data_node 단독 테스트")
    print("="*80)
    print(f"종목 코드: {args.symbol}")
    print(f"실행 모드: {args.mode}")
    print("="*80 + "\n")

    try:
        # 1. 테스트 상태 생성
        logger.info("테스트 상태 생성 중...")
        state = create_test_state(symbol=args.symbol, env_mode=args.mode)

        # 2. fetch_market_data_node 실행
        logger.info(f"fetch_market_data_node 실행 중 (종목: {args.symbol})...")
        result = fetch_market_data_node(state)

        # 3. 결과 출력
        print_result(result)

        # 4. 성공 메시지
        print("\n✅ 테스트 완료!")

        # 5. 실제 API 호출 여부 확인
        if result.get('current_price', 0) == 30000.0:
            print("\n⚠️  주의: 모의 데이터를 사용했습니다.")
            print("   KIS API가 정상적으로 설정되지 않았거나 API 호출이 실패했습니다.")
            print("   config/kis_devlp.yaml 파일을 확인하세요.")
        else:
            print("\n✅ 실제 KIS API 데이터 조회 성공!")

        return 0

    except Exception as e:
        logger.error(f"테스트 실패: {e}", exc_info=True)
        print(f"\n❌ 테스트 실패: {e}")

        print("\n💡 문제 해결 방법:")
        print("1. config/kis_devlp.yaml 파일이 존재하는지 확인")
        print("2. kis_devlp.yaml에 올바른 API 키가 설정되어 있는지 확인")
        print("3. 가상환경이 활성화되어 있는지 확인")
        print("4. 필요한 패키지가 설치되어 있는지 확인 (pip install -r requirements.txt)")

        return 1


if __name__ == "__main__":
    sys.exit(main())
