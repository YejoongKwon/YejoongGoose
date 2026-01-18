---
name: kis-tools
description: >
  한국투자증권 MCP 도구를 래핑해 LangGraph 노드에서 쉽게 쓸 수 있는 스킬.
  시세 조회, 주문 실행, 잔고 조회 등 KIS API 호출을 담당한다.
version: 1.0.0
dependencies:
  - claude-mcp-client (또는 직접 MCP 프로토콜 사용)
---

# KIS Tools Skill

## 역할

이 스킬은 한국투자증권 Open Trading API를 MCP를 통해 호출하는 래퍼 함수들을 제공합니다.
LangGraph 노드에서 간단하게 `get_current_price("005930")`처럼 호출할 수 있습니다.

## 구조

```
kis-tools/
├── SKILL.md                          # 이 파일
└── mcp_wrappers/
    ├── __init__.py
    ├── kis_price.py                  # 시세 조회
    ├── kis_order.py                  # 주문 실행
    └── kis_balance.py                # 잔고 조회
```

## 주요 컴포넌트

### 1. 시세 조회 (mcp_wrappers/kis_price.py)

```python
class KISPriceAPI:
    """KIS 시세 조회 API 래퍼"""

    def __init__(self, env_mode: str = "demo"):
        self.env_mode = env_mode

    def get_current_price(self, symbol: str) -> dict:
        """
        현재가 조회

        Returns:
            {
                'current_price': float,
                'open': float,
                'high': float,
                'low': float,
                'volume': int
            }
        """

    def get_daily_chart(self, symbol: str, days: int = 2) -> list:
        """
        일봉 차트 조회

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

    def get_yesterday_ohlc(self, symbol: str) -> dict:
        """
        전일 OHLC 조회

        Returns:
            {
                'open': float,
                'high': float,
                'low': float,
                'close': float
            }
        """
```

### 2. 주문 실행 (mcp_wrappers/kis_order.py)

```python
class KISOrderAPI:
    """KIS 주문 실행 API 래퍼"""

    def __init__(self, env_mode: str = "demo"):
        self.env_mode = env_mode

    def buy_market_order(self, symbol: str, qty: int) -> dict:
        """
        시장가 매수 주문

        Returns:
            {
                'success': bool,
                'order_no': str,
                'message': str
            }
        """

    def sell_market_order(self, symbol: str, qty: int) -> dict:
        """
        시장가 매도 주문

        Returns:
            {
                'success': bool,
                'order_no': str,
                'message': str
            }
        """

    def check_order_status(self, order_no: str) -> dict:
        """
        주문 상태 확인

        Returns:
            {
                'status': str,  # "체결" | "미체결" | "취소"
                'filled_qty': int,
                'filled_price': float
            }
        """

    def get_unfilled_orders(self) -> list:
        """
        미체결 주문 조회

        Returns:
            [
                {
                    'order_no': str,
                    'symbol': str,
                    'qty': int,
                    'price': float
                },
                ...
            ]
        """
```

### 3. 잔고 조회 (mcp_wrappers/kis_balance.py)

```python
class KISBalanceAPI:
    """KIS 잔고 조회 API 래퍼"""

    def __init__(self, env_mode: str = "demo"):
        self.env_mode = env_mode

    def get_cash_balance(self) -> float:
        """주문 가능 현금 조회"""

    def get_positions(self) -> list:
        """
        보유 종목 조회

        Returns:
            [
                {
                    'symbol': str,
                    'name': str,
                    'qty': int,
                    'avg_price': float,
                    'current_price': float,
                    'eval_amount': float,
                    'pnl': float,
                    'pnl_pct': float
                },
                ...
            ]
        """

    def get_position_by_symbol(self, symbol: str) -> dict:
        """특정 종목 포지션 조회"""

    def get_account_summary(self) -> dict:
        """
        계좌 요약 정보

        Returns:
            {
                'total_asset': float,
                'cash': float,
                'stock_value': float,
                'total_pnl': float,
                'total_pnl_pct': float
            }
        """
```

## MCP 호출 방식

각 래퍼 함수는 내부적으로 Claude MCP를 통해 `domestic_stock` 도구를 호출합니다:

```python
def get_current_price(self, symbol: str) -> dict:
    # MCP 호출
    result = call_mcp_tool(
        "domestic_stock",
        {
            "api_type": "inquire_price",
            "params": {
                "env_dv": self.env_mode,
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": symbol
            }
        }
    )

    # 결과 파싱 및 반환
    return {
        'current_price': float(result['output1'][0]['stck_prpr']),
        'open': float(result['output1'][0]['stck_oprc']),
        'high': float(result['output1'][0]['stck_hgpr']),
        'low': float(result['output1'][0]['stck_lwpr']),
        'volume': int(result['output1'][0]['acml_vol'])
    }
```

## LangGraph 노드에서 사용

```python
from kis_tools.mcp_wrappers.kis_price import KISPriceAPI
from kis_tools.mcp_wrappers.kis_order import KISOrderAPI

price_api = KISPriceAPI(env_mode="demo")
order_api = KISOrderAPI(env_mode="demo")

def fetch_market_data_node(state: TradingState) -> TradingState:
    """시장 데이터 수집 노드"""
    symbol = state["symbol"]

    # 현재가 조회
    current_data = price_api.get_current_price(symbol)

    # 전일 데이터 조회
    yesterday_data = price_api.get_yesterday_ohlc(symbol)

    # 상태 업데이트
    return {
        **state,
        "current_price": current_data["current_price"],
        "today_open": current_data["open"],
        "yesterday_high": yesterday_data["high"],
        "yesterday_low": yesterday_data["low"]
    }

def execute_order_node(state: TradingState) -> TradingState:
    """주문 실행 노드"""
    if state["should_buy"]:
        result = order_api.buy_market_order(
            symbol=state["symbol"],
            qty=state["order_qty"]
        )

        if result["success"]:
            return {
                **state,
                "position_status": "IN_POSITION",
                "entry_price": state["current_price"]
            }

    return state
```

## 오류 처리

모든 래퍼 함수는 오류 처리와 재시도 로직을 포함합니다:

```python
import time
from functools import wraps

def retry_on_failure(max_retries=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

class KISPriceAPI:
    @retry_on_failure(max_retries=3, delay=1)
    def get_current_price(self, symbol: str) -> dict:
        # ... 구현 ...
```

## 캐싱

동일한 데이터를 반복 조회하지 않도록 캐싱:

```python
from functools import lru_cache
from datetime import datetime, timedelta

class KISPriceAPI:
    def __init__(self):
        self._cache = {}
        self._cache_timeout = 60  # 60초

    def get_current_price(self, symbol: str) -> dict:
        cache_key = f"price_{symbol}"
        now = datetime.now()

        # 캐시 확인
        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if (now - cached_time).seconds < self._cache_timeout:
                return cached_data

        # API 호출
        data = self._fetch_price(symbol)

        # 캐시 저장
        self._cache[cache_key] = (data, now)

        return data
```

## Claude 바이브코딩 가이드

### 새 API 추가

```
"kis_price.py에 분봉 차트 조회 함수를 추가해줘"
"kis_order.py에 지정가 주문 함수를 추가해줘"
```

### 오류 처리 개선

```
"kis_balance.py의 모든 함수에 타임아웃 처리를 추가해줘"
"MCP 호출 실패 시 더 자세한 로그를 남기도록 개선해줘"
```

### 성능 최적화

```
"get_current_price 함수에 캐싱을 적용해줘 (60초)"
"배치 조회 함수를 추가해서 여러 종목을 한 번에 조회하도록 해줘"
```

## 테스트

```bash
# 유닛 테스트
pytest tests/test_kis_price.py
pytest tests/test_kis_order.py
pytest tests/test_kis_balance.py

# 통합 테스트 (실제 MCP 서버 필요)
pytest tests/integration/test_mcp_connection.py
```

## API 매핑 참조

각 래퍼 함수가 호출하는 실제 KIS API:

| 래퍼 함수 | KIS API | api_type |
|---------|---------|----------|
| get_current_price | 주식현재가 시세 | inquire_price |
| get_daily_chart | 국내주식기간별시세 | inquire_daily_itemchartprice |
| buy_market_order | 주식 주문(매수) | buy |
| sell_market_order | 주식 주문(매도) | sell |
| get_positions | 주식잔고조회 | inquire_balance |
| get_cash_balance | 주문가능금액조회 | inquire_psbl_order |

자세한 API 명세는 [../../what_I_can_use.md](../../what_I_can_use.md) 참조.
