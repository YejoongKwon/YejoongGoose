"""
TradingState: LangGraph 상태 정의
"""

from typing import TypedDict, Optional, Literal
from datetime import datetime
from pathlib import Path
import yaml
import logging

logger = logging.getLogger(__name__)


class TradingState(TypedDict):
    """
    변동성 돌파 자동매매 LangGraph 상태

    이 상태는 LangGraph의 모든 노드 간에 전달되며,
    매매 의사결정에 필요한 모든 정보를 담고 있습니다.
    """

    # ========== 메타 정보 ==========
    timestamp: str  # 현재 시각 (ISO format)
    iteration: int  # 현재 반복 횟수

    # ========== 시장 데이터 ==========
    symbol: str  # 종목 코드 (예: "069500")
    symbol_name: str  # 종목 명 (예: "KODEX 200")

    current_price: float  # 현재가
    today_open: float  # 당일 시가
    today_high: float  # 당일 고가
    today_low: float  # 당일 저가
    today_volume: int  # 당일 거래량

    yesterday_open: float  # 전일 시가
    yesterday_high: float  # 전일 고가
    yesterday_low: float  # 전일 저가
    yesterday_close: float  # 전일 종가
    yesterday_volume: int  # 전일 거래량

    # ========== 전략 파라미터 ==========
    k_value: float  # 변동성 계수 (기본값: 0.5)
    target_price: float  # 목표가 (돌파 기준)

    stop_loss_pct: float  # 손절매 비율 (예: -0.03)
    take_profit_pct: float  # 익절 비율 (예: 0.05)
    trailing_stop: bool  # 트레일링 스탑 사용 여부
    trailing_stop_pct: float  # 트레일링 스탑 비율

    # ========== 포지션 정보 ==========
    position_status: Literal["IDLE", "IN_POSITION"]  # 포지션 상태

    entry_price: Optional[float]  # 진입가
    entry_time: Optional[str]  # 진입 시각
    position_qty: int  # 보유 수량

    highest_price: Optional[float]  # 진입 후 최고가 (트레일링 스탑용)
    lowest_price: Optional[float]  # 진입 후 최저가

    # ========== 손익 정보 ==========
    unrealized_pnl: float  # 미실현 손익 (원)
    unrealized_pnl_pct: float  # 미실현 손익률 (%)

    realized_pnl: float  # 실현 손익 (원)
    realized_pnl_pct: float  # 실현 손익률 (%)

    daily_pnl: float  # 일일 손익 (원)
    daily_pnl_pct: float  # 일일 손익률 (%)

    total_trades: int  # 총 거래 횟수
    winning_trades: int  # 수익 거래 횟수
    losing_trades: int  # 손실 거래 횟수

    # ========== 계좌 정보 ==========
    cash_balance: float  # 주문 가능 현금
    total_asset: float  # 총 자산 (현금 + 주식)
    initial_capital: float  # 초기 자본

    # ========== 리스크 관리 ==========
    max_daily_loss: float  # 일일 최대 손실 한도 (예: -0.05)
    max_position_size: float  # 최대 포지션 크기 비율 (예: 0.1)

    trading_stopped: bool  # 거래 중단 플래그
    stop_reason: Optional[str]  # 중단 사유

    # ========== 매매 신호 ==========
    should_buy: bool  # 매수 신호
    should_sell: bool  # 매도 신호

    buy_reason: Optional[str]  # 매수 사유
    sell_reason: Optional[str]  # 매도 사유

    # ========== 주문 정보 ==========
    last_order_no: Optional[str]  # 마지막 주문번호
    last_order_status: Optional[str]  # 마지막 주문 상태
    last_order_message: Optional[str]  # 마지막 주문 메시지

    # ========== 환경 설정 ==========
    env_mode: Literal["demo", "real"]  # 실행 모드
    debug_mode: bool  # 디버그 모드


def load_trading_config() -> dict:
    """
    trading_config.yaml 로드

    Returns:
        설정 딕셔너리
    """
    # 프로젝트 루트 찾기
    current_file = Path(__file__)
    project_root = current_file.parent.parent.parent.parent
    config_path = project_root / "config" / "trading_config.yaml"

    if not config_path.exists():
        logger.warning(f"설정 파일을 찾을 수 없습니다: {config_path}")
        logger.warning("기본값을 사용합니다")
        return {}

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logger.info(f"설정 파일 로드 완료: {config_path}")
        return config
    except Exception as e:
        logger.error(f"설정 파일 로드 실패: {e}")
        return {}


def create_initial_state(
    symbol: str,
    initial_capital: Optional[float] = None,
    k_value: Optional[float] = None,
    stop_loss_pct: Optional[float] = None,
    take_profit_pct: Optional[float] = None,
    env_mode: Optional[str] = None,
    max_position_size: Optional[float] = None,
    max_daily_loss: Optional[float] = None,
    trailing_stop: Optional[bool] = None,
    trailing_stop_pct: Optional[float] = None
) -> TradingState:
    """
    초기 상태 생성

    trading_config.yaml에서 기본값을 로드하고,
    파라미터로 전달된 값이 있으면 그것으로 오버라이드합니다.

    Args:
        symbol: 종목 코드
        initial_capital: 초기 자본 (None이면 YAML에서 로드)
        k_value: 변동성 계수 (None이면 YAML에서 로드)
        stop_loss_pct: 손절매 비율 (None이면 YAML에서 로드)
        take_profit_pct: 익절 비율 (None이면 YAML에서 로드)
        env_mode: 실행 모드 (None이면 YAML에서 로드)
        max_position_size: 최대 포지션 크기 (None이면 YAML에서 로드)
        max_daily_loss: 일일 최대 손실 (None이면 YAML에서 로드)
        trailing_stop: 트레일링 스탑 사용 여부 (None이면 YAML에서 로드)
        trailing_stop_pct: 트레일링 스탑 비율 (None이면 YAML에서 로드)

    Returns:
        초기화된 TradingState
    """
    # YAML 설정 로드
    config = load_trading_config()

    # 파라미터 우선, 없으면 YAML, 그것도 없으면 하드코딩 기본값
    final_initial_capital = initial_capital if initial_capital is not None else config.get('trading', {}).get('capital', 1000000.0)
    final_k_value = k_value if k_value is not None else config.get('volatility_breakout', {}).get('k_value', 0.5)
    final_stop_loss_pct = stop_loss_pct if stop_loss_pct is not None else config.get('risk', {}).get('stop_loss', -0.03)
    final_take_profit_pct = take_profit_pct if take_profit_pct is not None else config.get('risk', {}).get('take_profit', 0.05)
    final_env_mode = env_mode if env_mode is not None else config.get('env', {}).get('mode', 'demo')
    final_max_position_size = max_position_size if max_position_size is not None else config.get('trading', {}).get('position_size', 0.1)
    final_max_daily_loss = max_daily_loss if max_daily_loss is not None else config.get('risk', {}).get('max_daily_loss', -0.05)
    final_trailing_stop = trailing_stop if trailing_stop is not None else config.get('risk', {}).get('trailing_stop', False)
    final_trailing_stop_pct = trailing_stop_pct if trailing_stop_pct is not None else config.get('risk', {}).get('trailing_stop_ratio', 0.02)

    return TradingState(
        # 메타
        timestamp=datetime.now().isoformat(),
        iteration=0,

        # 시장 데이터
        symbol=symbol,
        symbol_name="",
        current_price=0.0,
        today_open=0.0,
        today_high=0.0,
        today_low=0.0,
        today_volume=0,
        yesterday_open=0.0,
        yesterday_high=0.0,
        yesterday_low=0.0,
        yesterday_close=0.0,
        yesterday_volume=0,

        # 전략
        k_value=final_k_value,
        target_price=0.0,
        stop_loss_pct=final_stop_loss_pct,
        take_profit_pct=final_take_profit_pct,
        trailing_stop=final_trailing_stop,
        trailing_stop_pct=final_trailing_stop_pct,

        # 포지션
        position_status="IDLE",
        entry_price=None,
        entry_time=None,
        position_qty=0,
        highest_price=None,
        lowest_price=None,

        # 손익
        unrealized_pnl=0.0,
        unrealized_pnl_pct=0.0,
        realized_pnl=0.0,
        realized_pnl_pct=0.0,
        daily_pnl=0.0,
        daily_pnl_pct=0.0,
        total_trades=0,
        winning_trades=0,
        losing_trades=0,

        # 계좌
        cash_balance=final_initial_capital,
        total_asset=final_initial_capital,
        initial_capital=final_initial_capital,

        # 리스크
        max_daily_loss=final_max_daily_loss,
        max_position_size=final_max_position_size,
        trading_stopped=False,
        stop_reason=None,

        # 신호
        should_buy=False,
        should_sell=False,
        buy_reason=None,
        sell_reason=None,

        # 주문
        last_order_no=None,
        last_order_status=None,
        last_order_message=None,

        # 환경
        env_mode=final_env_mode,  # type: ignore
        debug_mode=False
    )
