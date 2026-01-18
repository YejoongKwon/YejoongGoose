# 한국투자증권 Open Trading API - 사용 가능한 도구

## 개요

이 문서는 Claude MCP를 통해 사용 가능한 한국투자증권 Open Trading API 도구들을 정리한 문서입니다.
자동매매 봇 개발에 활용할 수 있는 모든 API를 카테고리별로 분류하여 설명합니다.

**총 166개 API 지원**

## MCP 서버 정보

- **서버 위치**: `/Users/yejoong_kwon_babitalk/open-trading-api/MCP/Kis Trading MCP`
- **실행 방식**: Docker 컨테이너 또는 로컬 Python
- **접근 방법**: Claude Desktop의 MCP 연동을 통해 자동으로 도구 사용 가능

## 카테고리별 도구 목록

### 1. 인증 (Auth) - 2개 API

**도구명**: `auth`

필수 인증 도구입니다. 모든 거래 전에 토큰을 발급받아야 합니다.

- auth_token: 접근토큰발급(P)
- auth_ws_token: 실시간 (웹소켓) 접속키 발급

### 2. 국내주식 (Domestic Stock) - 74개 API

**도구명**: `domestic_stock`

**주요 기능**:
- 실시간 시세 조회
- 호가 및 체결 정보
- 차트 데이터 (분봉, 일봉, 주봉, 월봉)
- 잔고 및 계좌 정보
- 주문 (매수/매도)
- 종목 검색 및 분석
- 순위 정보 (등락률, 거래량 등)
- 프로그램 매매 정보

**시세 조회 API** (16개):
- inquire_price: 주식현재가 시세
- inquire_elw_price: ELW 현재가 시세
- inquire_asking_price_exp_ccn: 주식현재가 호가/예상체결
- inquire_ccnl: 주식현재가 체결
- inquire_time_itemconclusion: 주식현재가 당일시간대별체결
- inquire_daily_price: 주식현재가 일자별
- inquire_investor: 주식현재가 투자자
- inquire_overtime_price: 국내주식 시간외현재가
- inquire_price_2: 주식현재가 시세2
- inquire_daily_overtimeprice: 주식현재가 시간외일자별주가
- inquire_time_overtimeconclusion: 주식현재가 시간외시간별체결
- inquire_member: 주식현재가 회원사
- inquire_overtime_asking_price: 국내주식 시간외호가
- inquire_member_daily: 주식현재가 회원사 종목매매동향
- intstock_multprice: 관심종목(멀티종목) 시세조회
- intstock_stocklist_by_group: 관심종목 그룹별 종목조회

**차트 데이터 API** (4개):
- inquire_time_itemchartprice: 주식당일분봉조회
- inquire_daily_itemchartprice: 국내주식기간별시세(일/주/월/년)
- inquire_time_dailychartprice: 주식일별분봉조회
- inquire_daily_indexchartprice: 국내주식일별지수시세

**잔고 및 주문 API** (8개):
- inquire_account_balance: 계좌의 주문 가능 금액 조회
- inquire_balance: 주식잔고조회
- inquire_balance_rlz_pl: 주식 잔고조회 - 실현손익
- inquire_ccnl: 주식주문(현금)_체결조회
- inquire_daily_ccld: 주식일별주문체결조회
- inquire_psbl_order: 주식주문(현금)_주문가능수량조회
- inquire_psbl_sell: 주식 주문(현금) - 매도가능수량 조회
- inquire_nccs: 주식 주문(현금) - 미체결 조회

**주문 실행 API** (4개):
- buy: 주식 주문(현금) - 매수
- sell: 주식 주문(현금) - 매도
- order: 주식 주문(통합주문)
- order_rvsecncl: 주식 주문정정취소(주문번호)

**순위 및 분석 API** (8개):
- fluctuation: 국내주식 등락률 순위
- volume_rank: 거래량순위
- market_cap: 국내주식 시가총액 상위
- volume_power: 국내주식 체결강도 상위
- investor_trend_estimate: 종목별 외인기관 추정가집계
- foreign_institution_total: 외국인기관종합
- frgnmem_pchs_trend: 외국인기관종목별매매추이(일별)
- frgnmem_trade_trend: 외국인기관종목별매매추이(시간별)

**종목 검색 API** (3개):
- psearch_result: 종목조건검색조회
- psearch_title: 종목조건검색 목록조회
- chk_holiday: 국내휴장일조회

**프로그램매매 API** (3개):
- comp_program_trade_daily: 프로그램매매 종합현황(일별)
- program_trade_by_stock_daily: 종목별 프로그램매매추이(일별)
- program_trade_time: 프로그램매매추이(시간별)

**신용/대차 API** (5개):
- inquire_credit_psamount: 신용 주문가능금액 상세 조회
- daily_loan_trans: 종목별신용융자/대주잔고일별추이
- daily_short_sale: 종목별공매도추이
- estimate_perform: 예상체결가등락율순위
- inquire_daily_trade_volume: 종목별일별매수매도체결량

**기타 API** (23개):
- inquire_investor_time_by_market: 시장별 투자자매매동향(시세)
- 그 외 다수

### 3. 국내채권 (Domestic Bond) - 14개 API

**도구명**: `domestic_bond`

**주요 기능**:
- 채권 시세 조회
- 호가 정보
- 발행 정보
- 잔고 조회
- 매수/매도 주문

**API 목록**:
- inquire_asking_price: 장내채권현재가(호가)
- issue_info: 장내채권 발행정보
- inquire_price: 장내채권현재가(시세)
- search_bond_info: 장내채권 기본조회
- inquire_ccnl: 장내채권현재가(체결)
- inquire_daily_price: 장내채권현재가(일별)
- avg_unit: 장내채권 평균단가조회
- inquire_daily_ccld: 장내채권 주문체결내역
- inquire_psbl_order: 장내채권 매수가능조회
- inquire_balance: 장내채권 잔고조회
- order_rvsecncl: 장내채권 정정취소주문
- buy: 장내채권 매수주문
- inquire_psbl_rvsecncl: 채권정정취소가능주문조회
- sell: 장내채권 매도주문

### 4. 국내선물옵션 (Domestic Future/Option) - 20개 API

**도구명**: `domestic_futureoption`

**주요 기능**:
- 선물/옵션 시세 조회
- 호가 정보
- 차트 데이터
- 잔고 및 증거금
- 주문 (일반/야간)
- 정산손익

**API 목록**:
- inquire_asking_price: 선물옵션 시세호가
- inquire_time_fuopchartprice: 선물옵션 분봉조회
- inquire_price: 선물옵션 시세
- inquire_daily_fuopchartprice: 선물옵션기간별시세(일/주/월/년)
- exp_price_trend: 선물옵션 일중예상체결추이
- display_board_top: 국내선물 기초자산 시세
- inquire_balance: 선물옵션 잔고현황
- inquire_ngt_balance: (야간)선물옵션 잔고현황
- inquire_ccnl: 선물옵션 주문체결내역조회
- inquire_ngt_ccnl: (야간)선물옵션 주문체결 내역조회
- order: 선물옵션 주문
- inquire_psbl_order: 선물옵션 주문가능
- inquire_ccnl_bstime: 선물옵션 기준일체결내역
- order_rvsecncl: 선물옵션 정정취소주문
- inquire_balance_valuation_pl: 선물옵션 잔고평가손익내역
- inquire_deposit: 선물옵션 총자산현황
- inquire_balance_settlement_pl: 선물옵션 잔고정산손익내역
- inquire_psbl_ngt_order: (야간)선물옵션 주문가능 조회
- inquire_daily_amount_fee: 선물옵션기간약정수수료일별
- ngt_margin_detail: (야간)선물옵션 증거금 상세

### 5. 해외주식 (Overseas Stock) - 34개 API

**도구명**: `overseas_stock`

**주요 기능**:
- 미국, 아시아 주식 시세
- 차트 데이터
- 호가 정보
- 잔고 조회
- 주문 (일반/주간)
- 예약 주문
- 기간 손익

**API 목록**:
- price: 해외주식 현재체결가
- inquire_daily_chartprice: 해외주식 종목/지수/환율기간별시세(일/주/월/년)
- inquire_time_itemchartprice: 해외주식분봉조회
- dailyprice: 해외주식 기간별시세
- price_detail: 해외주식 현재가상세
- inquire_asking_price: 해외주식 현재가 1호가
- inquire_search: 해외주식조건검색
- quot_inquire_ccnl: 해외주식 체결추이
- search_info: 해외주식 상품기본정보
- industry_theme: 해외주식 업종별시세
- inquire_time_indexchartprice: 해외지수분봉조회
- updown_rate: 해외주식 상승율/하락율
- rights_by_ice: 해외주식 권리종합
- price_fluct: 해외주식 가격급등락
- trade_vol: 해외주식 거래량순위
- period_rights: 해외주식 기간별권리조회
- inquire_present_balance: 해외주식 체결기준현재잔고
- inquire_balance: 해외주식 잔고
- inquire_nccs: 해외주식 미체결내역
- inquire_ccnl: 해외주식 주문체결내역
- inquire_psamount: 해외주식 매수가능금액조회
- foreign_margin: 해외증거금 통화별조회
- order: 해외주식 주문
- order_rvsecncl: 해외주식 정정취소주문
- inquire_period_trans: 해외주식 일별거래내역
- inquire_paymt_stdr_balance: 해외주식 결제기준잔고
- daytime_order: 해외주식 미국주간주문
- daytime_order_rvsecncl: 해외주식 미국주간정정취소
- inquire_period_profit: 해외주식 기간손익
- order_resv: 해외주식 예약주문접수
- order_resv_list: 해외주식 예약주문조회
- inquire_algo_ccnl: 해외주식 지정가체결내역조회
- order_resv_ccnl: 해외주식 예약주문접수취소
- algo_ordno: 해외주식 지정가주문번호조회

### 6. 해외선물옵션 (Overseas Future/Option) - 19개 API

**도구명**: `overseas_futureoption`

**주요 기능**:
- 해외 선물/옵션 시세
- 차트 데이터
- 호가 정보
- 잔고 및 예수금
- 주문 가능 조회
- 체결 내역

**API 목록**:
- inquire_time_futurechartprice: 해외선물 분봉조회
- inquire_price: 해외선물종목현재가
- opt_asking_price: 해외옵션 호가
- daily_ccnl: 해외선물 체결추이(일간)
- search_opt_detail: 해외옵션 상품기본정보
- opt_price: 해외옵션종목현재가
- inquire_asking_price: 해외선물 호가
- search_contract_detail: 해외선물 상품기본정보
- inquire_ccld: 해외선물옵션 당일주문내역조회
- inquire_unpd: 해외선물옵션 미결제내역조회(잔고)
- inquire_deposit: 해외선물옵션 예수금현황
- inquire_psamount: 해외선물옵션 주문가능조회
- inquire_daily_order: 해외선물옵션 일별 주문내역
- inquire_daily_ccld: 해외선물옵션 일별 체결내역
- inquire_period_ccld: 해외선물옵션 기간계좌손익 일별
- order_rvsecncl: 해외선물옵션 정정취소주문
- inquire_period_trans: 해외선물옵션 기간계좌거래내역
- margin_detail: 해외선물옵션 증거금상세
- order: 해외선물옵션 주문

### 7. ELW - 1개 API

**도구명**: `elw`

**주요 기능**:
- ELW 거래량 순위

**API 목록**:
- volume_rank: ELW 거래량순위

### 8. ETF/ETN - 2개 API

**도구명**: `etfetn`

**주요 기능**:
- ETF/ETN 시세
- NAV 비교

**API 목록**:
- inquire_price: ETF/ETN 현재가
- nav_comparison_trend: NAV 비교추이(종목)

## 자동매매 봇 개발에 필요한 주요 API

### 1. 필수 인증
- `auth.auth_token`: 접근 토큰 발급

### 2. 시세 데이터 수집
- `domestic_stock.inquire_price`: 실시간 현재가
- `domestic_stock.inquire_daily_itemchartprice`: 일봉 데이터
- `domestic_stock.inquire_time_itemchartprice`: 분봉 데이터
- `domestic_stock.inquire_asking_price_exp_ccn`: 호가 및 예상체결가

### 3. 계좌 정보
- `domestic_stock.inquire_account_balance`: 주문 가능 금액
- `domestic_stock.inquire_balance`: 보유 잔고
- `domestic_stock.inquire_psbl_sell`: 매도 가능 수량

### 4. 주문 실행
- `domestic_stock.buy`: 매수 주문
- `domestic_stock.sell`: 매도 주문
- `domestic_stock.order_rvsecncl`: 주문 정정/취소

### 5. 체결 확인
- `domestic_stock.inquire_ccnl`: 주문 체결 내역
- `domestic_stock.inquire_nccs`: 미체결 내역

### 6. 종목 분석
- `domestic_stock.fluctuation`: 등락률 순위
- `domestic_stock.volume_rank`: 거래량 순위
- `domestic_stock.volume_power`: 체결강도 순위

## 변동성 돌파 전략에 필요한 API

변동성 돌파 전략을 구현하기 위해 필요한 API:

1. **일봉 데이터 수집** (`inquire_daily_itemchartprice`)
   - 전일 고가/저가/종가 데이터 확보
   - 변동성(range) 계산

2. **당일 시세 모니터링** (`inquire_price`)
   - 당일 시가 확인
   - 현재가 실시간 추적

3. **목표가 도달 확인**
   - 시가 + (전일 고가 - 전일 저가) × k

4. **매수 주문** (`buy`)
   - 목표가 돌파 시 시장가 매수

5. **매도 주문** (`sell`)
   - 장 마감 전 시장가 매도

6. **잔고 확인** (`inquire_balance`)
   - 보유 종목 및 수량 확인

## Claude와의 통합 방법

### 1. MCP 도구 호출 형식

```
domestic_stock({
  "api_type": "inquire_price",
  "params": {
    "env_dv": "real",  // 또는 "demo" (모의투자)
    "fid_cond_mrkt_div_code": "J",  // KRX
    "fid_input_iscd": "005930"  // 종목코드
  }
})
```

### 2. 종목명으로 검색

```
domestic_stock({
  "api_type": "find_stock_code",
  "params": {
    "stock_name": "삼성전자"
  }
})
```

### 3. API 상세 정보 조회

```
domestic_stock({
  "api_type": "find_api_detail",
  "params": {
    "api_type": "inquire_price"
  }
})
```

## 주요 파라미터

### 공통 파라미터
- `env_dv`: 실전/모의 구분
  - `"real"`: 실전투자
  - `"demo"`: 모의투자

### 국내주식 파라미터
- `fid_cond_mrkt_div_code`: 시장 구분
  - `"J"`: KRX (한국거래소)
  - `"NX"`: 넥스트레이드
  - `"UN"`: 통합

- `fid_input_iscd`: 종목코드
  - 예: "005930" (삼성전자)

### 자동 처리되는 파라미터
다음 파라미터는 시스템이 자동으로 설정하므로 제공하지 않아도 됩니다:
- `cano`: 계좌번호
- `acnt_prdt_cd`: 계좌상품코드
- `my_htsid`: HTS ID
- `excg_id_dvsn_cd`: 거래소구분 (국내 API는 자동으로 "KRX" 설정)

## 참고 자료

- [한국투자증권 개발자 센터](https://apiportal.koreainvestment.com/)
- [Open Trading API GitHub](https://github.com/koreainvestment/open-trading-api)
- [MCP 프로토콜 문서](https://modelcontextprotocol.io/)

## 주의사항

1. **투자 책임**: 모든 투자 결정과 손익은 전적으로 투자자 본인의 책임입니다
2. **모의투자 권장**: 실전 투자 전 반드시 모의투자로 충분히 테스트하세요
3. **API 호출 제한**: 한국투자증권 API의 호출 제한을 준수해야 합니다
4. **보안**: API 키와 계좌 정보는 절대 외부에 노출하지 마세요
