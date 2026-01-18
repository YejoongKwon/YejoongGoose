"""
LangGraph 그래프 빌더

노드들을 연결하여 상태 머신을 구성합니다.
"""

import logging
from typing import Literal

from langgraph.graph import StateGraph, START, END

from .state import TradingState
from .nodes import (
    fetch_market_data_node,
    calculate_target_node,
    generate_signal_node,
    risk_check_node,
    execute_order_node,
    monitor_position_node,
    update_account_node
)

logger = logging.getLogger(__name__)


def should_continue_trading(state: TradingState) -> Literal["continue", "end"]:
    """
    거래 계속 여부 결정

    거래 중단 플래그가 True이면 종료, 아니면 계속
    """
    if state["trading_stopped"]:
        logger.info(f"거래 중단: {state['stop_reason']}")
        return "end"

    return "continue"


def has_signal(state: TradingState) -> Literal["execute", "monitor"]:
    """
    매매 신호 확인

    매수 또는 매도 신호가 있으면 주문 실행, 없으면 모니터링
    """
    if state["should_buy"] or state["should_sell"]:
        return "execute"

    return "monitor"


def build_trading_graph() -> StateGraph:
    """
    자동매매 LangGraph 구축

    Returns:
        컴파일된 StateGraph 인스턴스
    """
    logger.info("LangGraph 빌드 시작")

    # 그래프 생성
    graph = StateGraph(TradingState)

    # ========== 노드 추가 ==========
    graph.add_node("fetch_data", fetch_market_data_node)
    graph.add_node("calculate_target", calculate_target_node)
    graph.add_node("generate_signal", generate_signal_node)
    graph.add_node("risk_check", risk_check_node)
    graph.add_node("execute_order", execute_order_node)
    graph.add_node("monitor", monitor_position_node)
    graph.add_node("update_account", update_account_node)

    # ========== 엣지 연결 ==========

    # 시작 → 데이터 수집
    graph.add_edge(START, "fetch_data")

    # 데이터 수집 → 목표가 계산
    graph.add_edge("fetch_data", "calculate_target")

    # 목표가 계산 → 신호 생성
    graph.add_edge("calculate_target", "generate_signal")

    # 신호 생성 → 리스크 체크
    graph.add_edge("generate_signal", "risk_check")

    # 리스크 체크 → 조건부 분기
    graph.add_conditional_edges(
        "risk_check",
        should_continue_trading,
        {
            "continue": "check_signal",
            "end": END
        }
    )

    # 신호 확인 노드 (임시)
    graph.add_node("check_signal", lambda state: state)

    # 신호 확인 → 주문 실행 or 모니터링
    graph.add_conditional_edges(
        "check_signal",
        has_signal,
        {
            "execute": "execute_order",
            "monitor": "monitor"
        }
    )

    # 주문 실행 → 모니터링
    graph.add_edge("execute_order", "monitor")

    # 모니터링 → 계좌 업데이트
    graph.add_edge("monitor", "update_account")

    # 계좌 업데이트 → 종료 (단일 반복의 경우)
    # 실제로는 루프를 돌려야 하지만, 기본 구조에서는 종료
    graph.add_edge("update_account", END)

    # ========== 그래프 컴파일 ==========
    compiled_graph = graph.compile()

    logger.info("LangGraph 빌드 완료")

    return compiled_graph


def build_continuous_trading_graph() -> StateGraph:
    """
    연속 거래 LangGraph 구축

    일정 시간마다 반복 실행되는 버전

    Returns:
        컴파일된 StateGraph 인스턴스
    """
    logger.info("연속 거래 LangGraph 빌드 시작")

    graph = StateGraph(TradingState)

    # 노드 추가
    graph.add_node("fetch_data", fetch_market_data_node)
    graph.add_node("calculate_target", calculate_target_node)
    graph.add_node("generate_signal", generate_signal_node)
    graph.add_node("risk_check", risk_check_node)
    graph.add_node("execute_order", execute_order_node)
    graph.add_node("monitor", monitor_position_node)
    graph.add_node("update_account", update_account_node)

    # 엣지 연결
    graph.add_edge(START, "fetch_data")
    graph.add_edge("fetch_data", "calculate_target")
    graph.add_edge("calculate_target", "generate_signal")
    graph.add_edge("generate_signal", "risk_check")

    # 리스크 체크 후 분기
    graph.add_conditional_edges(
        "risk_check",
        should_continue_trading,
        {
            "continue": "check_signal",
            "end": END
        }
    )

    graph.add_node("check_signal", lambda state: state)

    graph.add_conditional_edges(
        "check_signal",
        has_signal,
        {
            "execute": "execute_order",
            "monitor": "monitor"
        }
    )

    graph.add_edge("execute_order", "monitor")
    graph.add_edge("monitor", "update_account")

    # 계좌 업데이트 후 다시 데이터 수집으로 (루프)
    # 실제 종료는 외부에서 제어
    graph.add_edge("update_account", "fetch_data")

    compiled_graph = graph.compile()

    logger.info("연속 거래 LangGraph 빌드 완료")

    return compiled_graph


if __name__ == "__main__":
    # 테스트용 코드
    logging.basicConfig(level=logging.INFO)

    from .state import create_initial_state

    # 그래프 생성
    graph = build_trading_graph()

    # 초기 상태 (trading_config.yaml에서 자동 로드)
    initial_state = create_initial_state(
        symbol="069500"
    )

    # 실행
    print("=" * 80)
    print("LangGraph 테스트 실행")
    print("=" * 80)

    result = graph.invoke(initial_state)

    print("\n최종 상태:")
    print(f"포지션: {result['position_status']}")
    print(f"현재가: {result['current_price']:,.0f}원")
    print(f"목표가: {result['target_price']:,.0f}원")
    print(f"총 자산: {result['total_asset']:,.0f}원")
