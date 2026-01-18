#!/usr/bin/env python3
"""
노드 에러 처리 테스트

KIS API 사용 불가 시 에러가 제대로 발생하는지 테스트
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# KIS API를 강제로 사용 불가능하게 만들기
import skills.trading_core.graph.nodes as nodes
nodes.KIS_AVAILABLE = False

from skills.trading_core.graph.state import TradingState
from datetime import datetime


def test_fetch_market_data_error():
    """fetch_market_data_node 에러 처리 테스트"""
    print("="*80)
    print("fetch_market_data_node 에러 처리 테스트")
    print("="*80)

    state: TradingState = {
        "symbol": "005930",
        "env_mode": "demo",
        "timestamp": datetime.now().isoformat(),
        "iteration": 0,
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
        "position_status": "IDLE",
        "entry_price": None,
        "entry_time": None,
        "position_qty": 0,
        "highest_price": None,
        "lowest_price": None,
        "should_buy": False,
        "should_sell": False,
        "buy_reason": None,
        "sell_reason": None,
        "order_qty": 0,
        "cash_balance": 1000000.0,
        "total_asset": 1000000.0,
        "initial_capital": 1000000.0,
        "realized_pnl": 0.0,
        "realized_pnl_pct": 0.0,
        "unrealized_pnl": 0.0,
        "unrealized_pnl_pct": 0.0,
        "daily_pnl": 0.0,
        "daily_pnl_pct": 0.0,
        "k_value": 0.5,
        "stop_loss_pct": -0.03,
        "take_profit_pct": 0.05,
        "max_position_size": 0.1,
        "max_daily_loss": -0.05,
        "total_trades": 0,
        "winning_trades": 0,
        "losing_trades": 0,
        "last_order_no": None,
        "last_order_status": None,
        "last_order_message": None,
        "trading_stopped": False,
        "stop_reason": None,
    }

    try:
        result = nodes.fetch_market_data_node(state)
        print("❌ 테스트 실패: 에러가 발생하지 않았습니다")
        return False
    except RuntimeError as e:
        print("✅ 예상된 RuntimeError 발생:")
        print(f"\n{e}\n")
        return True
    except Exception as e:
        print(f"❌ 예상치 못한 에러: {type(e).__name__}: {e}")
        return False


def test_execute_order_error():
    """execute_order_node 에러 처리 테스트"""
    print("="*80)
    print("execute_order_node 에러 처리 테스트")
    print("="*80)

    state: TradingState = {
        "symbol": "005930",
        "env_mode": "demo",
        "should_buy": True,
        "should_sell": False,
        "order_qty": 10,
        "current_price": 50000.0,
        "cash_balance": 1000000.0,
        "trading_stopped": False,
    }

    try:
        result = nodes.execute_order_node(state)
        print("❌ 테스트 실패: 에러가 발생하지 않았습니다")
        return False
    except RuntimeError as e:
        print("✅ 예상된 RuntimeError 발생:")
        print(f"\n{e}\n")
        return True
    except Exception as e:
        print(f"❌ 예상치 못한 에러: {type(e).__name__}: {e}")
        return False


def test_update_account_error():
    """update_account_node 에러 처리 테스트"""
    print("="*80)
    print("update_account_node 에러 처리 테스트")
    print("="*80)

    state: TradingState = {
        "env_mode": "demo",
        "current_price": 50000.0,
        "position_qty": 10,
        "position_status": "IN_POSITION",
        "cash_balance": 500000.0,
        "initial_capital": 1000000.0,
    }

    try:
        result = nodes.update_account_node(state)
        print("❌ 테스트 실패: 에러가 발생하지 않았습니다")
        return False
    except RuntimeError as e:
        print("✅ 예상된 RuntimeError 발생:")
        print(f"\n{e}\n")
        return True
    except Exception as e:
        print(f"❌ 예상치 못한 에러: {type(e).__name__}: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "="*80)
    print("KIS API 에러 처리 테스트 시작")
    print("="*80 + "\n")

    results = []

    # 각 노드 테스트
    results.append(("fetch_market_data_node", test_fetch_market_data_error()))
    print()
    results.append(("execute_order_node", test_execute_order_error()))
    print()
    results.append(("update_account_node", test_update_account_error()))
    print()

    # 결과 요약
    print("="*80)
    print("테스트 결과 요약")
    print("="*80)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")

    all_passed = all(passed for _, passed in results)
    print("="*80)

    if all_passed:
        print("\n✅ 모든 테스트 통과!")
        sys.exit(0)
    else:
        print("\n❌ 일부 테스트 실패")
        sys.exit(1)
