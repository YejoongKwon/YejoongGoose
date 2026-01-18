#!/bin/bash
# fetch_market_data_node 테스트 스크립트

# 가상환경 활성화
source venv/bin/activate

# 테스트 실행
python3 tests/test_all_nodes.py "$@"
