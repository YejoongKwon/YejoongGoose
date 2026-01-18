#!/usr/bin/env python3
"""
노드 단독/체인 테스트

Usage:
    python tests/test_all_nodes.py fetch_market_data
    python tests/test_all_nodes.py fetch_market_data,calculate_target  # 체인
    python tests/test_all_nodes.py --list
"""

import sys
import argparse
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from skills.trading_core.graph.state import create_initial_state
from skills.trading_core.graph.nodes import (
    fetch_market_data_node,
    calculate_target_node,
    generate_signal_node,
    risk_check_node,
    execute_order_node,
    monitor_position_node,
    update_account_node,
)

NODES = {
    "fetch_market_data": fetch_market_data_node,
    "calculate_target": calculate_target_node,
    "generate_signal": generate_signal_node,
    "risk_check": risk_check_node,
    "execute_order": execute_order_node,
    "monitor_position": monitor_position_node,
    "update_account": update_account_node,
}


def main():
    parser = argparse.ArgumentParser(description="노드 테스트")
    parser.add_argument("nodes", nargs="?", help="노드 이름 (콤마로 체인 가능)")
    parser.add_argument("--list", action="store_true", help="노드 목록")
    parser.add_argument("--symbol", default="069500")
    parser.add_argument("--mode", choices=["demo", "real"], default="demo")
    args = parser.parse_args()

    if args.list:
        print("노드 목록:", ", ".join(NODES.keys()))
        return 0

    if not args.nodes:
        print(f"사용: python test_all_nodes.py <{' | '.join(NODES.keys())}>")
        return 1

    node_names = [n.strip() for n in args.nodes.split(",")]
    for name in node_names:
        if name not in NODES:
            print(f"❌ 알 수 없는 노드: {name}")
            return 1

    state = create_initial_state(symbol=args.symbol, env_mode=args.mode)
    state["debug_mode"] = True  # 테스트 시 시간 체크 스킵

    print(f"\n🧪 테스트: {' → '.join(node_names)} (symbol={args.symbol}, mode={args.mode})\n")

    for name in node_names:
        result = NODES[name](state)
        state.update(result)  # 다음 노드로 전달
        print(f"📤 {name}:")
        for k, v in result.items():
            print(f"    {k}: {v}")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())