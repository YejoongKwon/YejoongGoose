"""
KIS 시세 조회 API 래퍼

한국투자증권 MCP를 통한 시세 조회 기능
"""

import logging
from typing import Dict, List, Optional
from functools import wraps
import time

logger = logging.getLogger(__name__)


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """재시도 데코레이터"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"{func.__name__} 실패 (최대 재시도 초과): {e}")
                        raise
                    logger.warning(f"{func.__name__} 실패 (재시도 {attempt + 1}/{max_retries}): {e}")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator


class KISPriceAPI:
    """
    KIS 시세 조회 API 래퍼

    MCP domestic_stock 도구를 통해 시세 데이터를 조회합니다.
    """

    def __init__(self, env_mode: str = "demo"):
        """
        초기화

        Args:
            env_mode: 실행 모드 ("demo" | "real")
        """
        self.env_mode = env_mode
        logger.info(f"KISPriceAPI 초기화: {env_mode} 모드")

    @retry_on_failure(max_retries=3, delay=1.0)
    def get_current_price(self, symbol: str) -> Dict:
        """
        현재가 조회

        Args:
            symbol: 종목 코드 (예: "069500")

        Returns:
            {
                'current_price': float,
                'open': float,
                'high': float,
                'low': float,
                'volume': int,
                'change': float,
                'change_pct': float
            }
        """
        logger.debug(f"현재가 조회: {symbol}")

        # TODO: 실제 MCP 호출 구현
        # result = call_mcp_tool(
        #     "domestic_stock",
        #     {
        #         "api_type": "inquire_price",
        #         "params": {
        #             "env_dv": self.env_mode,
        #             "fid_cond_mrkt_div_code": "J",
        #             "fid_input_iscd": symbol
        #         }
        #     }
        # )
        #
        # return {
        #     'current_price': float(result['output1'][0]['stck_prpr']),
        #     'open': float(result['output1'][0]['stck_oprc']),
        #     'high': float(result['output1'][0]['stck_hgpr']),
        #     'low': float(result['output1'][0]['stck_lwpr']),
        #     'volume': int(result['output1'][0]['acml_vol']),
        #     'change': float(result['output1'][0]['prdy_vrss']),
        #     'change_pct': float(result['output1'][0]['prdy_ctrt'])
        # }

        # 임시 모의 데이터
        logger.warning("MCP 호출 미구현 - 모의 데이터 반환")
        return {
            'current_price': 30000.0,
            'open': 29500.0,
            'high': 30500.0,
            'low': 29000.0,
            'volume': 1500000,
            'change': 200.0,
            'change_pct': 0.67
        }

    @retry_on_failure(max_retries=3, delay=1.0)
    def get_daily_chart(
        self,
        symbol: str,
        days: int = 10,
        period: str = "D"
    ) -> List[Dict]:
        """
        일봉 차트 조회

        Args:
            symbol: 종목 코드
            days: 조회 일수
            period: 기간 구분 ("D": 일봉, "W": 주봉, "M": 월봉)

        Returns:
            [
                {
                    'date': str,
                    'open': float,
                    'high': float,
                    'low': float,
                    'close': float,
                    'volume': int
                },
                ...
            ]
        """
        logger.debug(f"일봉 차트 조회: {symbol}, {days}일")

        # TODO: 실제 MCP 호출 구현
        # result = call_mcp_tool(
        #     "domestic_stock",
        #     {
        #         "api_type": "inquire_daily_itemchartprice",
        #         "params": {
        #             "env_dv": self.env_mode,
        #             "fid_cond_mrkt_div_code": "J",
        #             "fid_input_iscd": symbol,
        #             "fid_period_div_code": period
        #         }
        #     }
        # )
        #
        # chart_data = []
        # for item in result['output2'][:days]:
        #     chart_data.append({
        #         'date': item['stck_bsop_date'],
        #         'open': float(item['stck_oprc']),
        #         'high': float(item['stck_hgpr']),
        #         'low': float(item['stck_lwpr']),
        #         'close': float(item['stck_clpr']),
        #         'volume': int(item['acml_vol'])
        #     })
        #
        # return chart_data

        # 임시 모의 데이터
        logger.warning("MCP 호출 미구현 - 모의 데이터 반환")
        return [
            {
                'date': '20240101',
                'open': 29500.0,
                'high': 30500.0,
                'low': 29000.0,
                'close': 29800.0,
                'volume': 1200000
            }
        ]

    def get_yesterday_ohlc(self, symbol: str) -> Dict:
        """
        전일 OHLC 조회

        Args:
            symbol: 종목 코드

        Returns:
            {
                'open': float,
                'high': float,
                'low': float,
                'close': float,
                'volume': int
            }
        """
        logger.debug(f"전일 OHLC 조회: {symbol}")

        # 일봉 데이터에서 전일 데이터 추출
        chart_data = self.get_daily_chart(symbol, days=2)

        if len(chart_data) >= 2:
            yesterday = chart_data[1]  # 두 번째 데이터가 전일
            return {
                'open': yesterday['open'],
                'high': yesterday['high'],
                'low': yesterday['low'],
                'close': yesterday['close'],
                'volume': yesterday['volume']
            }

        # 데이터 부족 시 첫 번째 데이터 반환
        if chart_data:
            today = chart_data[0]
            return {
                'open': today['open'],
                'high': today['high'],
                'low': today['low'],
                'close': today['close'],
                'volume': today['volume']
            }

        raise ValueError(f"전일 데이터를 조회할 수 없습니다: {symbol}")
