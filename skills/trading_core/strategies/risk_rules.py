"""
리스크 관리 규칙

포트폴리오 리스크를 관리하고 안전한 거래를 보장
"""

import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class RiskRules:
    """리스크 관리 규칙 클래스"""

    def check_daily_loss_limit(
        self,
        daily_pnl: float,
        initial_capital: float,
        max_daily_loss: float = -0.05
    ) -> bool:
        """
        일일 손실 한도 확인

        Args:
            daily_pnl: 일일 손익 (원)
            initial_capital: 초기 자본
            max_daily_loss: 최대 일일 손실 비율 (기본값: -5%)

        Returns:
            한도 초과 여부 (True: 초과, False: 정상)
        """
        if initial_capital == 0:
            return False

        daily_loss_pct = daily_pnl / initial_capital

        if daily_loss_pct <= max_daily_loss:
            logger.warning(
                f"일일 손실 한도 초과! "
                f"손실: {daily_pnl:,.0f}원, "
                f"손실률: {daily_loss_pct*100:.2f}%, "
                f"한도: {max_daily_loss*100:.1f}%"
            )
            return True

        return False

    def check_position_size(
        self,
        position_value: float,
        total_asset: float,
        max_position_size: float = 0.15
    ) -> Tuple[bool, Optional[str]]:
        """
        포지션 크기 확인

        Args:
            position_value: 포지션 가치 (원)
            total_asset: 총 자산
            max_position_size: 최대 포지션 크기 비율

        Returns:
            (유효 여부, 사유)
        """
        if total_asset == 0:
            return False, "총 자산이 0입니다"

        position_ratio = position_value / total_asset

        if position_ratio > max_position_size:
            reason = (
                f"포지션 크기 초과 "
                f"({position_ratio*100:.1f}% > {max_position_size*100:.1f}%)"
            )
            logger.warning(reason)
            return False, reason

        return True, None

    def check_monthly_loss_limit(
        self,
        monthly_pnl: float,
        initial_capital: float,
        max_monthly_loss: float = -0.15
    ) -> bool:
        """
        월간 손실 한도 확인

        Args:
            monthly_pnl: 월간 손익
            initial_capital: 초기 자본
            max_monthly_loss: 최대 월간 손실 비율

        Returns:
            한도 초과 여부
        """
        if initial_capital == 0:
            return False

        monthly_loss_pct = monthly_pnl / initial_capital

        if monthly_loss_pct <= max_monthly_loss:
            logger.warning(
                f"월간 손실 한도 초과! "
                f"손실: {monthly_pnl:,.0f}원, "
                f"손실률: {monthly_loss_pct*100:.2f}%, "
                f"한도: {max_monthly_loss*100:.1f}%"
            )
            return True

        return False

    def calculate_risk_adjusted_position(
        self,
        capital: float,
        volatility: float,
        base_position_ratio: float = 0.1,
        volatility_adjustment: bool = True
    ) -> float:
        """
        리스크 조정 포지션 크기 계산

        변동성에 따라 포지션 크기를 조정합니다.
        변동성이 클수록 포지션을 줄입니다.

        Args:
            capital: 총 자본
            volatility: 변동성 (예: 0.03 = 3%)
            base_position_ratio: 기본 투자 비율
            volatility_adjustment: 변동성 조정 사용 여부

        Returns:
            조정된 투자 금액
        """
        if not volatility_adjustment:
            return capital * base_position_ratio

        # 변동성이 클수록 포지션 축소
        # 변동성 3% 이하: 100% 투자
        # 변동성 5%: 60% 투자
        # 변동성 10%: 30% 투자
        if volatility <= 0.03:
            adjustment = 1.0
        elif volatility <= 0.05:
            adjustment = 0.6
        elif volatility <= 0.10:
            adjustment = 0.3
        else:
            adjustment = 0.1

        adjusted_amount = capital * base_position_ratio * adjustment

        logger.debug(
            f"리스크 조정 포지션: "
            f"변동성={volatility*100:.2f}%, "
            f"조정계수={adjustment:.2f}, "
            f"투자금액={adjusted_amount:,.0f}원"
        )

        return adjusted_amount

    def check_max_drawdown(
        self,
        current_asset: float,
        peak_asset: float,
        max_drawdown: float = -0.20
    ) -> bool:
        """
        최대 낙폭(MDD) 확인

        Args:
            current_asset: 현재 자산
            peak_asset: 최고 자산
            max_drawdown: 최대 허용 낙폭 비율

        Returns:
            MDD 초과 여부
        """
        if peak_asset == 0:
            return False

        drawdown = (current_asset - peak_asset) / peak_asset

        if drawdown <= max_drawdown:
            logger.warning(
                f"최대 낙폭 초과! "
                f"현재자산: {current_asset:,.0f}원, "
                f"최고자산: {peak_asset:,.0f}원, "
                f"낙폭: {drawdown*100:.2f}%, "
                f"한도: {max_drawdown*100:.1f}%"
            )
            return True

        return False

    def validate_trading_conditions(
        self,
        daily_pnl: float,
        monthly_pnl: float,
        initial_capital: float,
        max_daily_loss: float = -0.05,
        max_monthly_loss: float = -0.15
    ) -> Tuple[bool, Optional[str]]:
        """
        거래 조건 종합 검증

        Args:
            daily_pnl: 일일 손익
            monthly_pnl: 월간 손익
            initial_capital: 초기 자본
            max_daily_loss: 최대 일일 손실
            max_monthly_loss: 최대 월간 손실

        Returns:
            (거래 가능 여부, 사유)
        """
        # 일일 손실 한도 체크
        if self.check_daily_loss_limit(daily_pnl, initial_capital, max_daily_loss):
            return False, "일일 손실 한도 초과"

        # 월간 손실 한도 체크
        if self.check_monthly_loss_limit(monthly_pnl, initial_capital, max_monthly_loss):
            return False, "월간 손실 한도 초과"

        return True, None
