"""
한국 주식시장 호가 단위 설정
"""

from typing import List, Tuple


# 호가 단위 테이블 (가격 구간, 호가 단위)
TICK_SIZE_TABLE: List[Tuple[float, float, int]] = [
    (0, 2000, 1),           # ~2,000원 미만: 1원
    (2000, 5000, 5),        # 2,000~5,000원: 5원
    (5000, 20000, 10),      # 5,000~20,000원: 10원
    (20000, 50000, 50),     # 20,000~50,000원: 50원
    (50000, 200000, 100),   # 50,000~200,000원: 100원
    (200000, 500000, 500),  # 200,000~500,000원: 500원
    (500000, float('inf'), 1000)  # 500,000원 이상: 1,000원
]


def get_tick_size(price: float) -> int:
    """
    가격에 따른 호가 단위를 반환합니다.

    Args:
        price: 주식 가격

    Returns:
        해당 가격 구간의 호가 단위

    Example:
        >>> get_tick_size(1500)
        1
        >>> get_tick_size(3000)
        5
        >>> get_tick_size(10000)
        10
        >>> get_tick_size(600000)
        1000
    """
    for min_price, max_price, tick_size in TICK_SIZE_TABLE:
        if min_price <= price < max_price:
            return tick_size

    # 기본값 (500,000원 이상)
    return 1000


def adjust_price_to_tick(price: float) -> int:
    """
    가격을 호가 단위에 맞게 조정합니다.

    Args:
        price: 조정할 가격

    Returns:
        호가 단위에 맞춰진 가격 (정수)

    Example:
        >>> adjust_price_to_tick(1523.7)
        1524
        >>> adjust_price_to_tick(3007.2)
        3005
        >>> adjust_price_to_tick(10003.5)
        10000
    """
    tick_size = get_tick_size(price)

    # 호가 단위로 반올림
    adjusted = round(price / tick_size) * tick_size

    return int(adjusted)
