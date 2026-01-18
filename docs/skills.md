--- 
name: trading-core
description: >
  LangGraph로 국내 ETF 변동성 돌파 자동매매 플로우를 구성하는 스킬.
  전략 로직, 상태 정의, 노드 구성을 담당한다.
---

# Trading Core Skill

## Structure
- graph/state.py      # 포지션/손익/플래그를 담는 LangGraph State
- graph/nodes.py      # 데이터 수집, 시그널, 주문결정 노드
- graph/graph_builder.py  # LangGraph 그래프 생성 함수
- strategies/breakout_etf.py  # 변동성 돌파 진입/청산 규칙
- strategies/risk_rules.py    # 일/월 손실 제한 등 리스크 규칙