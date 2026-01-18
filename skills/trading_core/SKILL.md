---
name: trading-core
description: >
  LangGraph로 국내 ETF 변동성 돌파 자동매매 플로우를 구성하는 스킬.
  전략 로직, 상태 정의, 노드 구성을 담당한다.
version: 1.0.0
dependencies:
  - langgraph
  - pydantic
  - pyyaml
---

# Trading Core Skill

## 역할

이 스킬은 변동성 돌파 전략 기반의 자동매매 로직을 LangGraph 상태 머신으로 구현합니다.

## 구조

```
trading-core/
├── SKILL.md                          # 이 파일
├── graph/
│   ├── __init__.py
│   ├── state.py                      # TradingState 정의
│   ├── nodes.py                      # 각 노드 함수들
│   └── graph_builder.py              # LangGraph 그래프 빌더
└── strategies/
    ├── __init__.py
    ├── breakout_etf.py               # 변동성 돌파 전략 로직
    └── risk_rules.py                 # 리스크 관리 규칙
```

## 주요 컴포넌트

### 1. TradingState (graph/state.py)

LangGraph가 사용하는 상태 객체:

```python
class TradingState(TypedDict):
    # 시장 데이터
    symbol: str
    current_price: float
    yesterday_high: float
    yesterday_low: float
    today_open: float

    # 포지션
    position_status: str  # "IDLE" | "IN_POSITION"
    entry_price: Optional[float]
    position_qty: int

    # 손익
    unrealized_pnl: float
    realized_pnl: float
    daily_pnl: float

    # 전략 파라미터
    k_value: float
    target_price: float
    stop_loss_pct: float
    take_profit_pct: float

    # 플래그
    should_buy: bool
    should_sell: bool
    trading_stopped: bool
```

### 2. Nodes (graph/nodes.py)

각 단계를 처리하는 노드 함수들:

- `fetch_market_data_node`: 시세 데이터 수집
- `calculate_target_node`: 목표가 계산
- `generate_signal_node`: 매매 신호 생성
- `risk_check_node`: 리스크 체크
- `execute_order_node`: 주문 실행
- `update_position_node`: 포지션 업데이트
- `monitor_position_node`: 포지션 모니터링

### 3. Graph Builder (graph/graph_builder.py)

노드들을 연결하여 상태 머신 구성:

```python
def build_trading_graph() -> StateGraph:
    graph = StateGraph(TradingState)

    # 노드 추가
    graph.add_node("fetch_data", fetch_market_data_node)
    graph.add_node("calculate_target", calculate_target_node)
    graph.add_node("generate_signal", generate_signal_node)
    graph.add_node("risk_check", risk_check_node)
    graph.add_node("execute_order", execute_order_node)
    graph.add_node("monitor", monitor_position_node)

    # 엣지 연결
    graph.add_edge(START, "fetch_data")
    graph.add_edge("fetch_data", "calculate_target")
    # ... 추가 엣지 ...

    return graph.compile()
```

### 4. Breakout Strategy (strategies/breakout_etf.py)

변동성 돌파 전략 구현:

```python
class BreakoutStrategy:
    def calculate_target_price(self, open_price, prev_high, prev_low, k):
        volatility = prev_high - prev_low
        return open_price + (volatility * k)

    def should_enter(self, current_price, target_price):
        return current_price >= target_price

    def should_exit(self, entry_price, current_price, stop_loss, take_profit):
        pnl_pct = (current_price - entry_price) / entry_price
        return pnl_pct <= stop_loss or pnl_pct >= take_profit
```

### 5. Risk Rules (strategies/risk_rules.py)

리스크 관리 규칙:

```python
class RiskRules:
    def check_daily_loss_limit(self, daily_pnl, capital, max_daily_loss):
        return (daily_pnl / capital) <= max_daily_loss

    def check_position_limit(self, current_positions, max_positions):
        return len(current_positions) < max_positions
```

## 상태 전이 플로우

```
START
  ↓
fetch_market_data
  ↓
calculate_target
  ↓
generate_signal
  ↓
risk_check
  ↓ (if should_buy)
execute_order
  ↓
monitor_position
  ↓ (loop or END)
```

## 사용 예시

```python
from trading_core.graph.graph_builder import build_trading_graph

# 그래프 생성
graph = build_trading_graph()

# 초기 상태
initial_state = {
    "symbol": "069500",  # KODEX 200
    "position_status": "IDLE",
    "k_value": 0.5,
    "stop_loss_pct": -0.03,
    "take_profit_pct": 0.05,
}

# 실행
result = graph.invoke(initial_state)
```

## Claude 바이브코딩 가이드

### 전략 파라미터 조정

```
"breakout_etf.py에서 k 값을 0.5에서 0.6으로 변경해줘"
"risk_rules.py에서 일일 손실 한도를 -5%에서 -3%로 강화해줘"
```

### 노드 추가/수정

```
"nodes.py에 손절매 트레일링 스탑 노드를 추가해줘"
"generate_signal_node에 거래량 확인 로직을 추가해줘"
```

### 상태 확장

```
"state.py에 최대 낙폭(MDD) 추적 필드를 추가해줘"
"TradingState에 실시간 손익률 계산 메서드를 추가해줘"
```

## 테스트

```bash
# 유닛 테스트
pytest tests/test_breakout_strategy.py

# 상태 전이 테스트
pytest tests/test_state_transitions.py
```

## 의존성

- `langgraph`: 상태 머신 프레임워크
- `pydantic`: 상태 검증
- `pyyaml`: 설정 파일 로드

## 참고 자료

- [LangGraph 공식 문서](https://langchain-ai.github.io/langgraph/)
- [변동성 돌파 전략 설명](../../memory/strategy_context.md)
