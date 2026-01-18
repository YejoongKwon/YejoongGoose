# 변동성 돌파 자동매매 봇 (LangGraph 기반)

한국투자증권 Open Trading API와 LangGraph를 활용한 변동성 돌파 전략 기반 자동매매 봇입니다.

## 목차

- [프로젝트 개요](#프로젝트-개요)
- [주요 기능](#주요-기능)
- [프로젝트 구조](#프로젝트-구조)
- [설치 및 설정](#설치-및-설정)
- [LangGraph 아키텍처](#langgraph-아키텍처)
- [백테스팅 가이드](#백테스팅-가이드)
- [실행 방법](#실행-방법)
- [변동성 돌파 전략](#변동성-돌파-전략)
- [리스크 관리](#리스크-관리)
- [성과 측정](#성과-측정)

## 프로젝트 개요

### 목표
- **월 수익 목표**: 10만원 (월 10% 수익률)
- **초기 자본**: 100만원
- **전략**: 변동성 돌파 (Volatility Breakout)
- **AI 지원**: LangGraph를 통한 상태 기반 자동화

### 특징
- LangGraph 기반 상태 머신으로 매매 로직 구현
- 백테스팅을 통한 전략 검증
- 실시간 리스크 관리

## 주요 기능

1. 자동매매: 변동성 돌파 시 자동 진입/청산
2. 리스크 관리: 손절매, 익절, 일일 손실 한도
3. 백테스팅: 과거 데이터를 이용한 전략 검증
4. 모니터링: 실시간 성과 추적 및 로깅
5. LangGraph 워크플로: 상태 전이 기반 매매

## 프로젝트 구조

```
trading_bot/
├── README.md                           # 프로젝트 문서
├── requirements.txt                    # Python 패키지 의존성
├── pyproject.toml                      # 프로젝트 설정
│
├── config/                             # 설정 파일
│   ├── strategy.breakout.yaml          # 변동성 돌파 전략 설정
│   ├── symbols.yaml                    # 거래 종목 목록
│   └── trading_config.yaml             # 전체 거래 설정
│
├── apps/                               # 실행 애플리케이션
│   ├── daily_breakout_app.py           # 일간 매매 실행 CLI
│   └── flask_app.py                    # 웹 대시보드 (선택)
│
├── skills/                             # 기능 모듈
│   ├── kis_tools/                      # 한투 API 래퍼
│   │   ├── SKILL.md
│   │   ├── __init__.py
│   │   └── mcp_wrappers/               # MCP 래퍼
│   │       ├── kis_price.py            # 시세 조회
│   │       └── __init__.py
│   │
│   └── trading_core/                   # 거래 핵심 로직
│       ├── SKILL.md
│       ├── __init__.py
│       ├── graph/                      # LangGraph 정의
│       │   ├── graph_builder.py        # 그래프 빌더
│       │   ├── nodes.py                # 노드 함수들
│       │   └── state.py                # 상태 정의
│       └── strategies/                 # 전략 구현
│           ├── breakout_etf.py         # 변동성 돌파 전략
│           └── risk_rules.py           # 리스크 관리 규칙
│
├── lib/                                # 라이브러리
│   └── kis/                            # KIS API 모듈
│       ├── __init__.py
│       └── kis_auth.py                 # KIS 인증 및 API 호출
│
├── data/                               # 데이터 저장
│   ├── trades/                         # 거래 기록
│   └── logs/                           # 로그 파일
│
├── docs/                               # 문서
│   ├── skills.md                       # 스킬 가이드
│   └── what_I_can_use.md               # API 참조
│
├── memory/                             # Claude 메모리 (선택)
│
└── tests/                              # 테스트 코드
```

## 설치 및 설정

### 1. 패키지 설치

```bash
cd ~/trading_bot

# 가상환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 2. KIS API 설정

한국투자증권 API를 사용하기 위한 설정 파일을 생성합니다:

```bash
# 설정 파일 복사
cp config/kis_devlp.yaml.example config/kis_devlp.yaml

# 에디터로 열어서 실제 값으로 변경
vim config/kis_devlp.yaml  # 또는 nano, code 등
```

`config/kis_devlp.yaml` 파일에 다음 정보를 입력하세요:

```yaml
# 실전투자 설정
my_app: "YOUR_REAL_APP_KEY"           # 한투 실전 앱키
my_sec: "YOUR_REAL_APP_SECRET"        # 한투 실전 앱시크리트
my_acct_stock: "12345678"             # 실전 계좌번호 (8자리)

# 모의투자 설정
paper_app: "YOUR_PAPER_APP_KEY"       # 한투 모의 앱키
paper_sec: "YOUR_PAPER_APP_SECRET"    # 한투 모의 앱시크리트
my_paper_stock: "50000000"            # 모의 계좌번호 (8자리)

# 공통 설정
my_htsid: "@YOUR_HTS_ID"              # HTS ID
my_prod: "01"                         # 계좌 상품 코드
```

**주의**: `kis_devlp.yaml` 파일은 민감한 정보를 포함하므로 절대 Git에 커밋하지 마세요! (이미 .gitignore에 포함됨)

### 3. 전략 설정

`config/strategy.breakout.yaml` 파일에서 전략 파라미터를 조정하세요:

```yaml
strategy:
  k_value: 0.5              # 변동성 계수 (0.3~0.6 권장)
  stop_loss_pct: -0.03      # 손절매 -3%
  take_profit_pct: 0.05     # 익절 +5%
  position_ratio: 0.1       # 투자 비율 10%

capital:
  initial_capital: 1000000  # 초기 자본 1000만원

risk:
  max_daily_loss: -0.05     # 일일 최대 손실 -5%
```

## LangGraph 아키텍처

이 프로젝트는 **LangGraph**를 사용하여 매매 로직을 상태 머신으로 구현합니다.

### LangGraph란?

LangGraph는 LangChain 생태계의 일부로, **상태 기반 워크플로**를 그래프로 정의하고 실행할 수 있는 프레임워크입니다. 복잡한 의사결정 로직을 노드(Node)와 엣지(Edge)로 명확하게 표현할 수 있습니다.

### 매매 워크플로

```
START
  ↓
[시장 데이터 수집] → [목표가 계산] → [매매 신호 생성]
  ↓
[리스크 체크] ─┬─ 거래 중단? → END
              │
              └─ 계속
                 ↓
              [신호 확인] ─┬─ 매수/매도 신호? → [주문 실행]
                          │                        ↓
                          └─ 신호 없음 ──────────→ [포지션 모니터링]
                                                    ↓
                                                 [계좌 업데이트]
                                                    ↓
                                                   END
```

### 노드(Nodes) 설명

각 노드는 특정 작업을 수행하고 상태를 업데이트합니다:

| 노드 | 역할 | 위치 |
|------|------|------|
| `fetch_market_data_node` | 현재가, 시가, 전일 데이터 조회 | `skills/trading_core/graph/nodes.py` |
| `calculate_target_node` | 목표가 = 시가 + (전일고가 - 전일저가) × k | `skills/trading_core/graph/nodes.py` |
| `generate_signal_node` | 매수/매도 신호 생성 | `skills/trading_core/graph/nodes.py` |
| `risk_check_node` | 일일 손실 한도, 최대 낙폭 체크 | `skills/trading_core/graph/nodes.py` |
| `execute_order_node` | 실제 주문 실행 (매수/매도) | `skills/trading_core/graph/nodes.py` |
| `monitor_position_node` | 포지션 모니터링, 손익 계산 | `skills/trading_core/graph/nodes.py` |
| `update_account_node` | 계좌 정보 업데이트 | `skills/trading_core/graph/nodes.py` |

### 상태(State) 정의

`TradingState`는 모든 노드 간에 공유되는 상태 객체입니다:

```python
from skills.trading_core.graph.state import TradingState

# 주요 필드:
- symbol: str                    # 종목 코드
- current_price: float           # 현재가
- target_price: float            # 목표가
- position_status: "IDLE" | "IN_POSITION"
- entry_price: Optional[float]   # 진입가
- position_qty: int              # 보유 수량
- should_buy: bool               # 매수 신호
- should_sell: bool              # 매도 신호
- cash_balance: float            # 현금 잔고
- total_asset: float             # 총 자산
- trading_stopped: bool          # 거래 중단 플래그
```

전체 상태 정의: `skills/trading_core/graph/state.py:9`

### 그래프 빌드 방법

```python
from skills.trading_core.graph.graph_builder import build_trading_graph
from skills.trading_core.graph.state import create_initial_state

# 1. 그래프 빌드
graph = build_trading_graph()

# 2. 초기 상태 생성
initial_state = create_initial_state(
    symbol="069500",           # KODEX 200
    initial_capital=10000000,   # 1000만원
    k_value=0.5,
    stop_loss_pct=-0.03,
    take_profit_pct=0.05,
    env_mode="demo"            # 또는 "real"
)

# 3. 그래프 실행
result = graph.invoke(initial_state)

# 4. 결과 확인
print(f"포지션: {result['position_status']}")
print(f"현재가: {result['current_price']:,.0f}원")
print(f"총자산: {result['total_asset']:,.0f}원")
```

### LangGraph 사용 예시

#### 연속 거래 (루프 실행)

```python
from skills.trading_core.graph.graph_builder import build_continuous_trading_graph
import time

# 연속 거래 그래프 빌드 (update_account → fetch_data로 루프)
graph = build_continuous_trading_graph()

initial_state = create_initial_state(symbol="069500", env_mode="demo")

# 배경: 외부에서 종료 조건 제어
for iteration in range(100):  # 100회 반복
    result = graph.invoke(initial_state)

    if result['trading_stopped']:
        print(f"거래 중단: {result['stop_reason']}")
        break

    # 다음 반복을 위한 상태 업데이트
    initial_state = result
    initial_state['iteration'] += 1

    time.sleep(60)  # 1분 대기
```

### 커스텀 노드 추가

새로운 노드를 추가하려면 `skills/trading_core/graph/nodes.py`에 함수를 정의하고 `graph_builder.py`에서 연결하세요:

```python
# nodes.py
def my_custom_node(state: TradingState) -> TradingState:
    """커스텀 노드 예시"""
    logger.info("커스텀 노드 실행")

    # 상태 업데이트
    state["custom_field"] = "some_value"

    return state

# graph_builder.py
def build_trading_graph():
    graph = StateGraph(TradingState)

    # 노드 추가
    graph.add_node("my_custom", my_custom_node)

    # 엣지 연결
    graph.add_edge("fetch_data", "my_custom")
    graph.add_edge("my_custom", "calculate_target")

    # ...
```

## 백테스팅 가이드

백테스팅을 통해 과거 데이터로 전략의 수익성을 검증할 수 있습니다.

### 방법 1: Python 스크립트로 백테스팅

`tests/backtest_example.py` 파일을 생성하여 백테스팅을 실행하세요:

```python
#!/usr/bin/env python3
"""
변동성 돌파 전략 백테스팅
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import yaml

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from skills.trading_core.strategies.breakout_etf import BreakoutStrategy


def load_historical_data(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    과거 데이터 로드

    실제로는 KIS API 또는 CSV 파일에서 로드
    """
    # 예시: CSV 파일에서 로드
    # df = pd.read_csv(f"data/historical/{symbol}.csv")
    # df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]

    # 임시 더미 데이터 (실제로는 위 코드 사용)
    dates = pd.date_range(start_date, end_date, freq='D')
    df = pd.DataFrame({
        'date': dates,
        'open': 30000 + (dates.dayofyear * 10),
        'high': 30500 + (dates.dayofyear * 10),
        'low': 29500 + (dates.dayofyear * 10),
        'close': 30000 + (dates.dayofyear * 10),
        'volume': 1000000
    })

    return df


def backtest(symbol: str, config: dict, start_date: str, end_date: str):
    """
    백테스팅 실행
    """
    print("=" * 80)
    print(f"백테스팅 시작: {symbol} ({start_date} ~ {end_date})")
    print("=" * 80)

    # 전략 초기화
    strategy = BreakoutStrategy()

    # 데이터 로드
    df = load_historical_data(symbol, start_date, end_date)
    print(f"데이터 로드 완료: {len(df)}일")

    # 초기 설정
    initial_capital = config['capital']['initial_capital']
    cash = initial_capital
    position_qty = 0
    entry_price = None

    trades = []
    daily_pnl = []

    k_value = config['strategy']['k_value']
    stop_loss_pct = config['strategy']['stop_loss_pct']
    take_profit_pct = config['strategy']['take_profit_pct']
    position_ratio = config['strategy']['position_ratio']

    # 일별 시뮬레이션
    for i in range(1, len(df)):
        prev_day = df.iloc[i - 1]
        today = df.iloc[i]

        date = today['date']
        open_price = today['open']
        high_price = today['high']
        low_price = today['low']
        close_price = today['close']

        # 목표가 계산
        target_price = strategy.calculate_target_price(
            open_price=open_price,
            prev_high=prev_day['high'],
            prev_low=prev_day['low'],
            k=k_value
        )

        # 포지션 없는 경우: 매수 신호 확인
        if position_qty == 0:
            # 당일 고가가 목표가를 돌파했는지 확인
            if high_price >= target_price:
                # 매수
                qty = strategy.calculate_position_size(
                    capital=cash,
                    current_price=target_price,
                    position_ratio=position_ratio
                )

                if qty > 0:
                    entry_price = target_price
                    position_qty = qty
                    cash -= entry_price * qty

                    trades.append({
                        'date': date,
                        'action': 'BUY',
                        'price': entry_price,
                        'qty': qty,
                        'reason': '목표가 돌파'
                    })

                    print(f"{date.date()} 매수: {entry_price:,.0f}원 x {qty}주")

        # 포지션 있는 경우: 매도 신호 확인
        else:
            current_price = close_price

            should_exit, reason = strategy.should_exit(
                entry_price=entry_price,
                current_price=current_price,
                stop_loss_pct=stop_loss_pct,
                take_profit_pct=take_profit_pct,
                current_time=datetime.combine(date.date(), datetime.min.time())
            )

            if should_exit:
                # 매도
                exit_price = current_price
                pnl = (exit_price - entry_price) * position_qty
                pnl_pct = (exit_price - entry_price) / entry_price

                cash += exit_price * position_qty

                trades.append({
                    'date': date,
                    'action': 'SELL',
                    'price': exit_price,
                    'qty': position_qty,
                    'pnl': pnl,
                    'pnl_pct': pnl_pct,
                    'reason': reason
                })

                print(f"{date.date()} 매도: {exit_price:,.0f}원 x {position_qty}주, "
                      f"손익: {pnl:,.0f}원 ({pnl_pct*100:.2f}%), {reason}")

                position_qty = 0
                entry_price = None

        # 일일 손익 계산
        total_asset = cash + (position_qty * close_price if position_qty > 0 else 0)
        daily_pnl.append({
            'date': date,
            'total_asset': total_asset,
            'cash': cash,
            'position_value': position_qty * close_price if position_qty > 0 else 0
        })

    # 백테스팅 결과
    print("\n" + "=" * 80)
    print("백테스팅 결과")
    print("=" * 80)

    final_asset = daily_pnl[-1]['total_asset']
    total_return = (final_asset - initial_capital) / initial_capital

    winning_trades = [t for t in trades if t.get('pnl', 0) > 0]
    losing_trades = [t for t in trades if t.get('pnl', 0) < 0]

    print(f"초기 자본: {initial_capital:,.0f}원")
    print(f"최종 자산: {final_asset:,.0f}원")
    print(f"총 수익: {final_asset - initial_capital:,.0f}원")
    print(f"수익률: {total_return*100:.2f}%")
    print(f"총 거래 횟수: {len([t for t in trades if t['action'] == 'BUY'])}회")
    print(f"승리: {len(winning_trades)}회, 패배: {len(losing_trades)}회")

    if len(winning_trades) + len(losing_trades) > 0:
        win_rate = len(winning_trades) / (len(winning_trades) + len(losing_trades))
        print(f"승률: {win_rate*100:.1f}%")

    if winning_trades:
        avg_win = sum(t['pnl'] for t in winning_trades) / len(winning_trades)
        print(f"평균 이익: {avg_win:,.0f}원")

    if losing_trades:
        avg_loss = sum(t['pnl'] for t in losing_trades) / len(losing_trades)
        print(f"평균 손실: {avg_loss:,.0f}원")

    # MDD 계산
    df_pnl = pd.DataFrame(daily_pnl)
    df_pnl['peak'] = df_pnl['total_asset'].cummax()
    df_pnl['drawdown'] = (df_pnl['total_asset'] - df_pnl['peak']) / df_pnl['peak']
    max_drawdown = df_pnl['drawdown'].min()
    print(f"최대 낙폭 (MDD): {max_drawdown*100:.2f}%")

    print("=" * 80)

    return {
        'trades': trades,
        'daily_pnl': daily_pnl,
        'final_asset': final_asset,
        'total_return': total_return,
        'max_drawdown': max_drawdown
    }


if __name__ == "__main__":
    # 설정 로드
    config_path = project_root / "config" / "strategy.breakout.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 백테스팅 실행
    result = backtest(
        symbol="069500",
        config=config,
        start_date="2024-01-01",
        end_date="2024-12-31"
    )
```

실행:

```bash
python tests/backtest_example.py
```

### 방법 2: LangGraph로 백테스팅

LangGraph의 상태 머신을 그대로 활용하여 백테스팅할 수 있습니다:

```python
#!/usr/bin/env python3
"""
LangGraph 기반 백테스팅
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd
import yaml

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from skills.trading_core.graph.graph_builder import build_trading_graph
from skills.trading_core.graph.state import create_initial_state


def backtest_with_langgraph(symbol: str, config: dict, historical_data: pd.DataFrame):
    """
    LangGraph를 사용한 백테스팅

    historical_data: 과거 데이터 DataFrame (columns: date, open, high, low, close, volume)
    """
    print("=" * 80)
    print("LangGraph 백테스팅 시작")
    print("=" * 80)

    # 그래프 빌드
    graph = build_trading_graph()

    # 초기 상태
    initial_state = create_initial_state(
        symbol=symbol,
        initial_capital=config['capital']['initial_capital'],
        k_value=config['strategy']['k_value'],
        stop_loss_pct=config['strategy']['stop_loss_pct'],
        take_profit_pct=config['strategy']['take_profit_pct'],
        env_mode="demo"
    )

    results = []

    # 일별 시뮬레이션
    for i in range(1, len(historical_data)):
        prev_day = historical_data.iloc[i - 1]
        today = historical_data.iloc[i]

        # 상태에 시장 데이터 주입 (노드 대신 직접 설정)
        state = initial_state.copy()
        state['timestamp'] = today['date'].isoformat()
        state['today_open'] = today['open']
        state['today_high'] = today['high']
        state['today_low'] = today['low']
        state['current_price'] = today['close']
        state['today_volume'] = today['volume']
        state['yesterday_high'] = prev_day['high']
        state['yesterday_low'] = prev_day['low']
        state['yesterday_close'] = prev_day['close']

        # 그래프 실행
        result = graph.invoke(state)

        # 결과 저장
        results.append({
            'date': today['date'],
            'position_status': result['position_status'],
            'total_asset': result['total_asset'],
            'daily_pnl': result['daily_pnl']
        })

        # 다음 반복을 위한 상태 업데이트
        initial_state = result

        if result['trading_stopped']:
            print(f"거래 중단: {result['stop_reason']}")
            break

    # 결과 분석
    df_results = pd.DataFrame(results)
    print(f"\n최종 자산: {df_results.iloc[-1]['total_asset']:,.0f}원")
    print(f"총 수익률: {(df_results.iloc[-1]['total_asset'] / config['capital']['initial_capital'] - 1) * 100:.2f}%")

    return df_results


if __name__ == "__main__":
    # 설정 및 데이터 로드
    config_path = project_root / "config" / "strategy.breakout.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 과거 데이터 로드 (CSV 파일 또는 API에서)
    # historical_data = pd.read_csv("data/historical/069500.csv")

    # 예시 데이터
    dates = pd.date_range("2024-01-01", "2024-12-31", freq='D')
    historical_data = pd.DataFrame({
        'date': dates,
        'open': 30000,
        'high': 30500,
        'low': 29500,
        'close': 30000,
        'volume': 1000000
    })

    # 백테스팅 실행
    results = backtest_with_langgraph(
        symbol="069500",
        config=config,
        historical_data=historical_data
    )
```

### 백테스팅 팁

1. **데이터 수집**: 과거 데이터를 CSV 파일이나 데이터베이스에 저장
2. **슬리피지와 수수료**: 실제 거래와 유사하게 반영
3. **파라미터 최적화**: k_value, 손절매/익절 비율 등을 변경하며 테스트
4. **검증 기간**: 과적합 방지를 위해 학습 기간과 검증 기간을 분리

## 실행 방법

### 모의투자 모드 (권장)

```bash
# CLI로 일간 실행
python apps/daily_breakout_app.py --mode demo --symbol 069500

# 특정 설정 파일 사용
python apps/daily_breakout_app.py \
  --mode demo \
  --config config/strategy.breakout.yaml \
  --symbol 069500

# 드라이런 (실제 주문 없이 시뮬레이션)
python apps/daily_breakout_app.py --mode demo --dry-run
```

### 실전투자 모드

**주의**: 충분한 백테스팅과 모의투자 테스트 후 사용하세요!

```bash
python apps/daily_breakout_app.py --mode real --symbol 069500
```

### 웹 대시보드 실행 (선택)

```bash
python apps/flask_app.py
# 브라우저에서 http://localhost:5000 접속
```

### 로그 확인

```bash
# 실시간 로그 확인
tail -f data/logs/trading_$(date +%Y%m%d).log

# 최근 100줄 확인
tail -n 100 data/logs/trading_$(date +%Y%m%d).log
```

## 변동성 돌파 전략

### 기본 원리

래리 윌리엄스(Larry Williams)가 개발한 전략으로, 시장의 변동성을 이용합니다.

**목표가 공식**:
```
목표가 = 당일 시가 + (전일 고가 - 전일 저가) × k
```

- `k`: 변동성 계수 (일반적으로 0.5)
- 현재가가 목표가를 돌파하면 매수

### 진입 조건

1. 현재가 >= 목표가 (돌파)
2. 진입 시간: 09:05 ~ 15:00
3. 거래량 충분 (설정된 최소 거래량 이상)

### 청산 조건

다음 중 하나를 만족하면 청산:

1. **손절매**: 손실 -3% (기본값)
2. **익절**: 이익 +5% (기본값)
3. **장 마감**: 15:20 시장가 청산

### 포지션 크기

```python
투자금액 = 총 자본 × position_ratio (기본값: 10%)
매수 수량 = 투자금액 ÷ 현재가
```

### 전략 파라미터 최적화

`config/strategy.breakout.yaml`에서 조정 가능:

- `k_value`: 0.3 (공격적) ~ 0.6 (보수적)
- `stop_loss_pct`: -0.02 ~ -0.05
- `take_profit_pct`: 0.03 ~ 0.10
- `position_ratio`: 0.05 ~ 0.20

## 리스크 관리

### 자동 리스크 체크

LangGraph의 `risk_check_node`에서 다음을 확인합니다:

1. **일일 손실 한도**: 당일 손실이 -5%를 초과하면 거래 중단
2. **최대 낙폭 (MDD)**: 누적 최대 낙폭이 -20%를 초과하면 경고
3. **포지션 크기**: 단일 종목 최대 투자 비율 제한
4. **현금 비율**: 최소 현금 보유 비율 유지

### 안전 장치

1. **모의투자 우선**: 충분한 테스트 없이 실전투자 금지
2. **손절매**: 자동 손절매 설정 필수
3. **긴급 정지**: `Ctrl+C`로 언제든 중단 가능
4. **알림**: 중요 이벤트 발생 시 알림 (설정 시)

## 성과 측정

### 목표 달성 기준

**월 10만원 수익 달성 시나리오**:
- 초기 자본: 100만원
- 목표 수익률: 10%/월
- 거래 빈도: 주 3-5회
- 평균 수익률: 2-3%/거래

### 주요 지표

실행 결과에서 다음 지표를 확인할 수 있습니다:

- **총 수익률**: (최종 자산 - 초기 자본) / 초기 자본
- **승률**: 수익 거래 / 총 거래
- **평균 수익/손실**: 거래당 평균 손익
- **최대 낙폭 (MDD)**: 최고점 대비 최대 하락폭
- **샤프 비율**: 위험 대비 수익률

### 성과 리포트

거래 기록은 다음 위치에 저장됩니다:

```
data/trades/
  ├── trades_YYYYMMDD.json        # 일별 거래 기록
  └── performance_YYYYMM.json     # 월별 성과 리포트
```

## 문제 해결

### 자주 발생하는 오류

1. **API 인증 실패**: 환경 변수 확인
2. **데이터 조회 오류**: 종목 코드 확인
3. **주문 실패**: 계좌 잔고 확인

### 디버그 모드

```bash
python apps/daily_breakout_app.py --mode demo --log-level DEBUG
```

## 라이센스

이 프로젝트는 개인 사용 목적으로 제작되었습니다.

## 면책 조항

이 봇은 교육 및 연구 목적으로 제작되었습니다. 실제 투자 손실에 대한 책임은 사용자에게 있습니다. 충분한 백테스팅과 모의투자 테스트 후 사용하세요.

---

**Happy Trading! 📈**


# nodes.py 수정사항

  주요 변경 사항

  1. KIS API Import 및 인증

  - kis_auth.py를 동적으로 import하여 KIS API 사용 가능 여부 확인
  - _init_kis_auth() 함수로 모의투자(vps) / 실전투자 인증 처리
  - KIS API 사용 불가 시 자동으로 모의 데이터로 fallback

  2. fetch_market_data_node (시장 데이터 수집)

  실제 구현:
  - _call_inquire_price(): 현재가 조회 API (inquire_price)
    - 현재가, 시가, 고가, 저가, 거래량 조회
  - _call_inquire_daily_chart(): 일봉 차트 조회 API (inquire_daily_itemchartprice)
    - 전일 OHLC 데이터 조회

  API 응답 필드 매핑:
  'stck_prpr' → current_price  # 현재가
  'stck_oprc' → open           # 시가
  'stck_hgpr' → high           # 고가
  'stck_lwpr' → low            # 저가
  'acml_vol' → volume          # 누적거래량

  3. execute_order_node (주문 실행)

  실제 구현:
  - _call_order_cash(): 현금 주문 API (order_cash)
    - 매수/매도 시장가 주문 실행
    - TR ID 자동 설정: 모의투자(VTTC), 실전투자(TTTC)
    - 주문번호, 체결시각 반환

  주문 파라미터:
  "CANO": ka._TRENV.my_acct           # 계좌번호 앞 8자리
  "ACNT_PRDT_CD": ka._TRENV.my_prod  # 계좌번호 뒤 2자리
  "ORD_DVSN": "01"                    # 01:시장가
  "EXCG_ID_DVSN_CD": "KRX"           # 거래소ID

  4. update_account_node (계좌 정보 업데이트)

  실제 구현:
  - _call_inquire_balance(): 잔고 조회 API (inquire_balance)
    - output1: 종목별 잔고
    - output2: 계좌 총평가금액

  응답 필드:
  output2[0]['tot_evlu_amt']  # 총평가금액

  5. 안전 장치

  모든 노드에 3단계 fallback 구조:
  1. KIS API 사용 가능 → 실제 API 호출
  2. KIS API 인증 실패 → 경고 후 모의 데이터 사용
  3. API 호출 오류 → 로그 후 모의 데이터 사용

  6. KIS API 사용 방법

  전제 조건:
  1. open-trading-api 디렉토리가 프로젝트 상위에 위치
  2. kis_auth.py가 설정되어 있음 (계좌정보, API 키 등)

  실행:
  # 모의투자 모드
  python apps/daily_breakout_app.py --mode demo --symbol 069500

  # 실전투자 모드
  python apps/daily_breakout_app.py --mode real --symbol 069500

  7. API 호출 흐름

  fetch_market_data_node
    ↓
  _init_kis_auth("demo")  # 모의투자 인증
    ↓
  _call_inquire_price()   # 현재가 조회
    ↓
  _call_inquire_daily_chart()  # 일봉 조회 (전일 데이터)
    ↓
  상태 업데이트

  execute_order_node
    ↓
  _init_kis_auth("demo")
    ↓
  _call_order_cash("buy", symbol, qty)  # 매수 주문
    ↓
  체결 확인 및 상태 업데이트

  update_account_node
    ↓
  _init_kis_auth("demo")
    ↓
  _call_inquire_balance()  # 잔고 조회
    ↓
  총자산 업데이트

  이제 실제 한국투자증권 API를 통해 시세 조회, 주문 실행, 잔고 조회가 가능합니다!
