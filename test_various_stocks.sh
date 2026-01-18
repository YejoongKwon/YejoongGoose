#!/bin/bash
# 다양한 종목으로 fetch_market_data_node 테스트

source venv/bin/activate

echo "========================================="
echo "다양한 종목 테스트 시작"
echo "========================================="
echo ""

# ETF - KODEX 200
echo "1. KODEX 200 (069500)"
echo "-----------------------------------------"
python3 tests/test_fetch_market_data.py --symbol 069500
echo ""

# 대형주 - 삼성전자
echo "2. 삼성전자 (005930)"
echo "-----------------------------------------"
python3 tests/test_fetch_market_data.py --symbol 005930
echo ""

# 대형주 - SK하이닉스
echo "3. SK하이닉스 (000660)"
echo "-----------------------------------------"
python3 tests/test_fetch_market_data.py --symbol 000660
echo ""

# IT - NAVER
echo "4. NAVER (035420)"
echo "-----------------------------------------"
python3 tests/test_fetch_market_data.py --symbol 035420
echo ""

echo "========================================="
echo "모든 테스트 완료!"
echo "========================================="
