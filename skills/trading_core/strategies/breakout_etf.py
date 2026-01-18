"""
변동성 돌파 ETF 전략

래리 윌리엄스의 변동성 돌파 전략을 ETF에 적용
"""

import logging
from typing import Tuple, Optional
from datetime import datetime, time

logger = logging.getLogger(__name__)


class BreakoutStrategy:
    """변동성 돌파 전략 클래스"""

    def __init__(self):
        self.entry_time_start = time(9, 5)  # 진입 시작 시간
        self.entry_time_end = time(15, 0)  # 진입 종료 시간
        self.exit_time = time(15, 20)  # 청산 시간

    def calculate_target_price(
        self,
        open_price: float,
        prev_high: float,
        prev_low: float,
        k: float = 0.5
    ) -> float:
        """
        목표가 계산

        목표가 = 당일 시가 + (전일 고가 - 전일 저가) × k

        Args:
            open_price: 당일 시가
            prev_high: 전일 고가
            prev_low: 전일 저가
            k: 변동성 계수 (기본값: 0.5)

        Returns:
            목표가
        """
        volatility = prev_high - prev_low
        target = open_price + (volatility * k)

        logger.debug(
            f"목표가 계산: "
            f"시가={open_price:,.0f}, "
            f"전일고가={prev_high:,.0f}, "
            f"전일저가={prev_low:,.0f}, "
            f"변동폭={volatility:,.0f}, "
            f"k={k}, "
            f"목표가={target:,.0f}"
        )

        return target

    def should_enter(
        self,
        current_price: float,
        target_price: float,
        current_time: Optional[datetime] = None,
        skip_time_check: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        진입 조건 확인

        Args:
            current_price: 현재가
            target_price: 목표가
            current_time: 현재 시각 (None이면 현재 시각 사용)
            skip_time_check: 시간 체크 스킵 여부 (테스트용)

        Returns:
            (진입 여부, 사유)
        """
        if current_time is None:
            current_time = datetime.now()

        current_time_only = current_time.time()

        # 시간 체크 (skip_time_check=True면 스킵)
        if not skip_time_check:
            if not (self.entry_time_start <= current_time_only <= self.entry_time_end):
                return False, "진입 시간이 아님"

        # 목표가 돌파 확인
        if current_price >= target_price:
            reason = (
                f"목표가 돌파 "
                f"(현재가: {current_price:,.0f}원, "
                f"목표가: {target_price:,.0f}원, "
                f"돌파폭: {(current_price - target_price):,.0f}원)"
            )
            logger.info(f"진입 조건 충족: {reason}")
            return True, reason

        return False, None

    def should_exit(
        self,
        entry_price: float,
        current_price: float,
        stop_loss_pct: float = -0.03,
        take_profit_pct: float = 0.05,
        current_time: Optional[datetime] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        청산 조건 확인

        Args:
            entry_price: 진입가
            current_price: 현재가
            stop_loss_pct: 손절매 비율
            take_profit_pct: 익절 비율
            current_time: 현재 시각

        Returns:
            (청산 여부, 사유)
        """
        if current_time is None:
            current_time = datetime.now()

        # 손익률 계산
        pnl_pct = (current_price - entry_price) / entry_price

        # 손절매
        if pnl_pct <= stop_loss_pct:
            reason = (
                f"손절매 "
                f"(진입가: {entry_price:,.0f}원, "
                f"현재가: {current_price:,.0f}원, "
                f"수익률: {pnl_pct*100:.2f}%)"
            )
            logger.info(f"청산 조건 충족: {reason}")
            return True, reason

        # 익절
        if pnl_pct >= take_profit_pct:
            reason = (
                f"익절 "
                f"(진입가: {entry_price:,.0f}원, "
                f"현재가: {current_price:,.0f}원, "
                f"수익률: {pnl_pct*100:.2f}%)"
            )
            logger.info(f"청산 조건 충족: {reason}")
            return True, reason

        # 장 마감 시간
        if current_time.time() >= self.exit_time:
            reason = (
                f"장 마감 청산 "
                f"(진입가: {entry_price:,.0f}원, "
                f"현재가: {current_price:,.0f}원, "
                f"수익률: {pnl_pct*100:.2f}%)"
            )
            logger.info(f"청산 조건 충족: {reason}")
            return True, reason

        return False, None

    def calculate_position_size(
        self,
        capital: float,
        current_price: float,
        position_ratio: float = 0.1
    ) -> int:
        """
        포지션 크기 계산

        Args:
            capital: 총 자본
            current_price: 현재가
            position_ratio: 투자 비율 (기본값: 10%)

        Returns:
            매수 수량
        """
        investment_amount = capital * position_ratio
        qty = int(investment_amount / current_price)

        logger.debug(
            f"포지션 크기 계산: "
            f"자본={capital:,.0f}, "
            f"현재가={current_price:,.0f}, "
            f"투자비율={position_ratio*100:.1f}%, "
            f"투자금액={investment_amount:,.0f}, "
            f"수량={qty}"
        )

        return qty

    def validate_breakout(
        self,
        current_price: float,
        target_price: float,
        volume: int,
        min_volume: int = 100000
    ) -> Tuple[bool, Optional[str]]:
        """
        돌파 유효성 검증

        Args:
            current_price: 현재가
            target_price: 목표가
            volume: 거래량
            min_volume: 최소 거래량

        Returns:
            (유효 여부, 사유)
        """
        # 목표가 돌파 확인
        if current_price < target_price:
            return False, "목표가 미돌파"

        # 거래량 확인
        if volume < min_volume:
            return False, f"거래량 부족 (현재: {volume:,}, 최소: {min_volume:,})"

        # 돌파 강도 확인 (목표가 대비 1% 이상 초과)
        breakout_strength = (current_price - target_price) / target_price
        if breakout_strength < 0.01:
            return False, f"돌파 강도 약함 ({breakout_strength*100:.2f}%)"

        return True, "유효한 돌파"
