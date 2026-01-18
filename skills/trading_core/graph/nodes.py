"""
LangGraph 노드 함수들

각 노드는 TradingState를 받아 처리 후 업데이트된 상태를 반환합니다.
"""

from datetime import datetime
import logging
from typing import Dict, Any
import sys
from pathlib import Path

# 프로젝트 루트 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from .state import TradingState
from ..strategies.breakout_etf import BreakoutStrategy
from ..strategies.risk_rules import RiskRules

# KIS API import
try:
    from lib.kis import kis_auth as ka
    KIS_AVAILABLE = True
except ImportError as e:
    KIS_AVAILABLE = False
    logging.warning(f"kis_auth를 import할 수 없습니다: {e}. 모의 데이터를 사용합니다.")

logger = logging.getLogger(__name__)

# 전략 및 리스크 관리자 인스턴스
breakout_strategy = BreakoutStrategy()
risk_rules = RiskRules()


def _init_kis_auth(env_mode: str = "demo"):
    """
    KIS 인증 초기화

    Args:
        env_mode: 실행 모드 ("demo" | "real")
    """
    if not KIS_AVAILABLE:
        logger.warning("KIS API 사용 불가")
        return False

    try:
        if env_mode == "demo":
            ka.auth("vps")  # 모의투자
        else:
            ka.auth()  # 실전투자
        logger.info(f"KIS 인증 완료: {env_mode} 모드")
        return True
    except Exception as e:
        logger.error(f"KIS 인증 실패: {e}")
        return False


def _call_inquire_price(env_mode: str, symbol: str) -> Dict[str, Any]:
    """
    현재가 조회 API 호출

    Args:
        env_mode: 실행 모드
        symbol: 종목 코드

    Returns:
        현재가 데이터
    """
    try:
        # API 호출
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",  # J:KRX
            "FID_INPUT_ISCD": symbol
        }

        # TR ID 설정
        if env_mode == "demo":
            tr_id = "FHKST01010100"
        else:
            tr_id = "FHKST01010100"

        # API 호출
        api_url = "/uapi/domestic-stock/v1/quotations/inquire-price"
        res = ka._url_fetch(api_url, tr_id, "", params)

        if res.isOK():
            output = res.getBody().output
            return {
                'current_price': float(output['stck_prpr']),  # 현재가
                'open': float(output['stck_oprc']),  # 시가
                'high': float(output['stck_hgpr']),  # 고가
                'low': float(output['stck_lwpr']),  # 저가
                'volume': int(output['acml_vol']),  # 누적거래량
                'change': float(output['prdy_vrss']),  # 전일대비
                'change_pct': float(output['prdy_ctrt'])  # 전일대비율
            }
        else:
            res.printError(url=api_url)
            raise Exception("현재가 조회 실패")

    except Exception as e:
        logger.error(f"현재가 조회 API 호출 실패: {e}")
        raise


def _call_inquire_daily_chart(env_mode: str, symbol: str, days: int = 2) -> list:
    """
    일봉 차트 조회 API 호출

    Args:
        env_mode: 실행 모드
        symbol: 종목 코드
        days: 조회 일수

    Returns:
        일봉 데이터 리스트
    """
    try:
        from datetime import datetime, timedelta

        # 날짜 계산 (오늘부터 days일 전까지)
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days+5)).strftime("%Y%m%d")  # 여유있게 조회

        # API 호출
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",  # J:KRX
            "FID_INPUT_ISCD": symbol,
            "FID_INPUT_DATE_1": start_date,
            "FID_INPUT_DATE_2": end_date,
            "FID_PERIOD_DIV_CODE": "D",  # D:일봉
            "FID_ORG_ADJ_PRC": "1"  # 1:원주가
        }

        # TR ID 설정
        if env_mode == "demo":
            tr_id = "FHKST03010100"
        else:
            tr_id = "FHKST03010100"

        # API 호출
        api_url = "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice"
        res = ka._url_fetch(api_url, tr_id, "", params)

        if res.isOK():
            output2 = res.getBody().output2
            chart_data = []
            for item in output2[:days]:
                chart_data.append({
                    'date': item['stck_bsop_date'],
                    'open': float(item['stck_oprc']),
                    'high': float(item['stck_hgpr']),
                    'low': float(item['stck_lwpr']),
                    'close': float(item['stck_clpr']),
                    'volume': int(item['acml_vol'])
                })
            return chart_data
        else:
            res.printError(url=api_url)
            raise Exception("일봉 차트 조회 실패")

    except Exception as e:
        logger.error(f"일봉 차트 조회 API 호출 실패: {e}")
        raise


def _call_inquire_balance(env_mode: str) -> tuple:
    """
    잔고 조회 API 호출

    Args:
        env_mode: 실행 모드

    Returns:
        (잔고 DataFrame1, 잔고 DataFrame2)
    """
    try:
        # TR ID 설정
        if env_mode == "demo":
            tr_id = "VTTC8434R"
        else:
            tr_id = "TTTC8434R"

        # API 호출
        params = {
            "CANO": ka._TRENV.my_acct,  # 계좌번호 앞 8자리
            "ACNT_PRDT_CD": ka._TRENV.my_prod,  # 계좌번호 뒤 2자리
            "AFHR_FLPR_YN": "N",  # N:기본값
            "OFL_YN": "",
            "INQR_DVSN": "02",  # 02:종목별
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "01",  # 01:전일매매미포함
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": ""
        }

        api_url = "/uapi/domestic-stock/v1/trading/inquire-balance"
        res = ka._url_fetch(api_url, tr_id, "", params)

        if res.isOK():
            # output1: 종목별 잔고
            # output2: 계좌 총평가
            return (res.getBody().output1, res.getBody().output2)
        else:
            res.printError(url=api_url)
            raise Exception("잔고 조회 실패")

    except Exception as e:
        logger.error(f"잔고 조회 API 호출 실패: {e}")
        raise


def _call_order_cash(
    env_mode: str,
    order_type: str,  # "buy" | "sell"
    symbol: str,
    qty: int,
    price: int = 0,
    order_dvsn: str = "01"  # 00:지정가, 01:시장가
) -> Dict[str, Any]:
    """
    현금 주문 API 호출

    Args:
        env_mode: 실행 모드
        order_type: 주문 유형 (buy | sell)
        symbol: 종목 코드
        qty: 주문 수량
        price: 주문 단가 (시장가의 경우 0)
        order_dvsn: 주문 구분 (00:지정가, 01:시장가)

    Returns:
        주문 결과
    """
    try:
        # TR ID 설정
        if env_mode == "demo":
            if order_type == "buy":
                tr_id = "VTTC0012U"
            else:
                tr_id = "VTTC0011U"
        else:
            if order_type == "buy":
                tr_id = "TTTC0012U"
            else:
                tr_id = "TTTC0011U"

        # API 호출
        params = {
            "CANO": ka._TRENV.my_acct,  # 계좌번호 앞 8자리
            "ACNT_PRDT_CD": ka._TRENV.my_prod,  # 계좌번호 뒤 2자리
            "PDNO": symbol,  # 종목코드
            "ORD_DVSN": order_dvsn,  # 주문구분
            "ORD_QTY": str(qty),  # 주문수량 (문자열)
            "ORD_UNPR": str(price),  # 주문단가 (문자열)
            "EXCG_ID_DVSN_CD": "KRX",  # 거래소ID
            "SLL_TYPE": "01" if order_type == "sell" else "",  # 매도유형
            "CNDT_PRIC": ""  # 조건가격
        }

        api_url = "/uapi/domestic-stock/v1/trading/order-cash"
        res = ka._url_fetch(api_url, tr_id, "", params, postFlag=True)

        if res.isOK():
            output = res.getBody().output
            return {
                'success': True,
                'order_no': output.get('KRX_FWDG_ORD_ORGNO', '') + output.get('ODNO', ''),  # 주문번호
                'order_time': output.get('ORD_TMD', ''),  # 주문시각
                'message': f"{order_type.upper()} 주문 접수 완료"
            }
        else:
            error_msg = f"{order_type.upper()} 주문 실패"
            res.printError(url=api_url)
            return {
                'success': False,
                'order_no': '',
                'message': error_msg
            }

    except Exception as e:
        logger.error(f"주문 API 호출 실패: {e}")
        return {
            'success': False,
            'order_no': '',
            'message': f"주문 API 호출 오류: {str(e)}"
        }


def fetch_market_data_node(state: TradingState) -> Dict[str, Any]:
    """
    시장 데이터 수집 노드

    KIS API를 통해 현재가 및 전일 데이터를 조회합니다.

    Raises:
        RuntimeError: KIS API를 사용할 수 없는 경우
        Exception: API 호출 실패 시
    """
    logger.info(f"[fetch_market_data] 시작: {state['symbol']}")

    updates = {
        "timestamp": datetime.now().isoformat(),
        "iteration": state["iteration"] + 1,
    }

    # KIS API 사용 가능 여부 확인
    if not KIS_AVAILABLE:
        error_msg = (
            "KIS API를 사용할 수 없습니다.\n"
            "해결 방법:\n"
            "1. 가상환경이 활성화되어 있는지 확인: source venv/bin/activate\n"
            "2. 필수 패키지 설치 확인: pip install pandas requests websockets pycryptodome PyYAML\n"
            "3. lib/kis/kis_auth.py 파일이 존재하는지 확인"
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    # KIS 인증
    if not _init_kis_auth(state["env_mode"]):
        error_msg = (
            "KIS 인증에 실패했습니다.\n"
            "해결 방법:\n"
            "1. config/kis_devlp.yaml 파일이 존재하는지 확인\n"
            "2. API 키와 시크릿이 올바르게 설정되어 있는지 확인\n"
            "3. 계좌 번호가 정확한지 확인\n"
            f"4. 현재 모드: {state['env_mode']} (demo: 모의투자, real: 실전투자)"
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    try:
        # 1. 현재가 조회
        price_data = _call_inquire_price(state["env_mode"], state["symbol"])
        logger.info(f"[fetch_market_data] 현재가 조회 완료: {price_data['current_price']:,.0f}원")

        # 2. 일봉 차트 조회 (전일 데이터 포함)
        chart_data = _call_inquire_daily_chart(state["env_mode"], state["symbol"], days=2)
        logger.info(f"[fetch_market_data] 일봉 조회 완료: {len(chart_data)}일")

        # 전일 데이터 추출 (chart_data[1]이 전일)
        if len(chart_data) >= 2:
            yesterday = chart_data[1]
        elif len(chart_data) >= 1:
            yesterday = chart_data[0]
        else:
            raise Exception("일봉 데이터 부족")

        # 상태 업데이트
        updates.update({
            "current_price": price_data['current_price'],
            "today_open": price_data['open'],
            "today_high": price_data['high'],
            "today_low": price_data['low'],
            "today_volume": price_data['volume'],
            "yesterday_open": yesterday['open'],
            "yesterday_high": yesterday['high'],
            "yesterday_low": yesterday['low'],
            "yesterday_close": yesterday['close'],
            "yesterday_volume": yesterday['volume'],
        })

        logger.info(
            f"[fetch_market_data] 데이터 수집 완료 - "
            f"현재가: {price_data['current_price']:,.0f}원, "
            f"시가: {price_data['open']:,.0f}원, "
            f"전일고가: {yesterday['high']:,.0f}원, "
            f"전일저가: {yesterday['low']:,.0f}원"
        )

        return updates

    except Exception as e:
        error_msg = (
            f"[fetch_market_data] 시장 데이터 조회 실패: {e}\n"
            f"종목 코드: {state['symbol']}\n"
            f"실행 모드: {state['env_mode']}\n"
            "해결 방법:\n"
            "1. 종목 코드가 올바른지 확인\n"
            "2. 네트워크 연결 상태 확인\n"
            "3. KIS API 서버 상태 확인\n"
            "4. API 호출 제한(Rate Limit)에 걸리지 않았는지 확인"
        )
        logger.error(error_msg)
        raise Exception(error_msg) from e


def calculate_target_node(state: TradingState) -> Dict[str, Any]:
    """
    목표가 계산 노드

    변동성 돌파 전략의 목표가를 계산합니다.
    """
    logger.info("[calculate_target] 목표가 계산 시작")

    target_price = breakout_strategy.calculate_target_price(
        open_price=state["today_open"],
        prev_high=state["yesterday_high"],
        prev_low=state["yesterday_low"],
        k=state["k_value"]
    )

    logger.info(f"[calculate_target] 목표가: {target_price:,.0f}원")

    return {
        "target_price": target_price
    }


def generate_signal_node(state: TradingState) -> Dict[str, Any]:
    """
    매매 신호 생성 노드

    현재 포지션 상태에 따라 매수 또는 매도 신호를 생성합니다.
    """
    logger.info("[generate_signal] 신호 생성 시작")

    updates: Dict[str, Any] = {
        "should_buy": False,
        "should_sell": False,
        "buy_reason": None,
        "sell_reason": None
    }

    # 포지션 없을 때: 매수 신호 확인
    if state["position_status"] == "IDLE":
        should_enter, reason = breakout_strategy.should_enter(
            current_price=state["current_price"],
            target_price=state["target_price"]
        )

        if should_enter:
            # 매수 수량 계산
            qty = breakout_strategy.calculate_position_size(
                capital=state["cash_balance"],
                current_price=state["current_price"],
                position_ratio=state["max_position_size"]
            )

            updates["should_buy"] = True
            updates["buy_reason"] = reason
            updates["order_qty"] = qty
            logger.info(f"[generate_signal] 매수 신호 발생: {reason}, 수량: {qty}주")

    # 포지션 있을 때: 매도 신호 확인
    elif state["position_status"] == "IN_POSITION":
        should_exit, reason = breakout_strategy.should_exit(
            entry_price=state["entry_price"],
            current_price=state["current_price"],
            stop_loss_pct=state["stop_loss_pct"],
            take_profit_pct=state["take_profit_pct"]
        )

        if should_exit:
            updates["should_sell"] = True
            updates["sell_reason"] = reason
            logger.info(f"[generate_signal] 매도 신호 발생: {reason}")

    return updates


def risk_check_node(state: TradingState) -> Dict[str, Any]:
    """
    리스크 체크 노드

    일일 손실 한도, 포지션 크기 등을 확인합니다.
    """
    logger.info("[risk_check] 리스크 체크 시작")

    updates: Dict[str, Any] = {}

    # 일일 손실 한도 체크
    if risk_rules.check_daily_loss_limit(
        daily_pnl=state["daily_pnl"],
        initial_capital=state["initial_capital"],
        max_daily_loss=state["max_daily_loss"]
    ):
        logger.warning("[risk_check] 일일 손실 한도 초과!")
        updates["trading_stopped"] = True
        updates["stop_reason"] = "일일 손실 한도 초과"
        updates["should_buy"] = False  # 매수 신호 취소

    # 포지션 크기 체크
    if state.get("should_buy", False):
        order_qty = state.get("order_qty", 0)
        position_value = state["current_price"] * order_qty
        is_valid, reason = risk_rules.check_position_size(
            position_value=position_value,
            total_asset=state["total_asset"],
            max_position_size=state["max_position_size"]
        )

        if not is_valid:
            logger.warning(f"[risk_check] 포지션 크기 초과: {reason}")
            updates["should_buy"] = False
            updates["buy_reason"] = None

    return updates


def execute_order_node(state: TradingState) -> Dict[str, Any]:
    """
    주문 실행 노드

    매수 또는 매도 주문을 실행합니다.

    Raises:
        RuntimeError: KIS API를 사용할 수 없거나 인증 실패 시
    """
    logger.info("[execute_order] 주문 실행 시작")

    updates: Dict[str, Any] = {}

    # 매수/매도 신호가 없으면 아무것도 하지 않음
    if not state.get("should_buy") and not state.get("should_sell"):
        logger.info("[execute_order] 주문 신호 없음")
        return updates

    # KIS API 사용 가능 여부 확인
    if not KIS_AVAILABLE:
        error_msg = (
            "주문 실행 실패: KIS API를 사용할 수 없습니다.\n"
            "해결 방법:\n"
            "1. 가상환경이 활성화되어 있는지 확인\n"
            "2. 필수 패키지가 설치되어 있는지 확인"
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    # KIS 인증
    if not _init_kis_auth(state["env_mode"]):
        error_msg = (
            "주문 실행 실패: KIS 인증에 실패했습니다.\n"
            "해결 방법:\n"
            "1. config/kis_devlp.yaml 파일 확인\n"
            "2. API 키와 계좌 정보 확인"
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    try:
        # 매수 주문
        if state["should_buy"] and not state["trading_stopped"]:
            order_qty = state.get("order_qty", 0)
            if order_qty <= 0:
                logger.warning("[execute_order] 주문 수량이 0 이하입니다")
                return updates

            logger.info(f"[execute_order] 매수 주문 실행: {state['symbol']}, {order_qty}주")

            result = _call_order_cash(
                env_mode=state["env_mode"],
                order_type="buy",
                symbol=state["symbol"],
                qty=order_qty,
                price=0,  # 시장가
                order_dvsn="01"  # 시장가
            )

            if result["success"]:
                logger.info(f"[execute_order] 매수 체결: {result['order_no']}")
                updates.update({
                    "position_status": "IN_POSITION",
                    "entry_price": state["current_price"],
                    "entry_time": datetime.now().isoformat(),
                    "position_qty": order_qty,
                    "highest_price": state["current_price"],
                    "lowest_price": state["current_price"],
                    "cash_balance": state["cash_balance"] - (state["current_price"] * order_qty),
                    "last_order_no": result["order_no"],
                    "last_order_status": "체결",
                    "last_order_message": result["message"],
                    "should_buy": False
                })
            else:
                logger.error(f"[execute_order] 매수 실패: {result['message']}")
                updates["should_buy"] = False

        # 매도 주문
        elif state["should_sell"]:
            logger.info(f"[execute_order] 매도 주문 실행: {state['symbol']}, {state['position_qty']}주")

            result = _call_order_cash(
                env_mode=state["env_mode"],
                order_type="sell",
                symbol=state["symbol"],
                qty=state["position_qty"],
                price=0,  # 시장가
                order_dvsn="01"  # 시장가
            )

            if result["success"]:
                logger.info(f"[execute_order] 매도 체결: {result['order_no']}")

                # 손익 계산
                pnl = (state["current_price"] - state["entry_price"]) * state["position_qty"]
                pnl_pct = (state["current_price"] - state["entry_price"]) / state["entry_price"]

                updates.update({
                    "position_status": "IDLE",
                    "entry_price": None,
                    "entry_time": None,
                    "position_qty": 0,
                    "highest_price": None,
                    "lowest_price": None,
                    "cash_balance": state["cash_balance"] + (state["current_price"] * state["position_qty"]),
                    "realized_pnl": state["realized_pnl"] + pnl,
                    "realized_pnl_pct": pnl_pct,
                    "daily_pnl": state["daily_pnl"] + pnl,
                    "total_trades": state["total_trades"] + 1,
                    "winning_trades": state["winning_trades"] + (1 if pnl > 0 else 0),
                    "losing_trades": state["losing_trades"] + (1 if pnl <= 0 else 0),
                    "last_order_no": result["order_no"],
                    "last_order_status": "체결",
                    "last_order_message": result["message"],
                    "should_sell": False
                })
            else:
                logger.error(f"[execute_order] 매도 실패: {result['message']}")
                updates["should_sell"] = False

    except Exception as e:
        logger.error(f"[execute_order] 주문 실행 오류: {e}")
        updates["should_buy"] = False
        updates["should_sell"] = False

    return updates


def monitor_position_node(state: TradingState) -> Dict[str, Any]:
    """
    포지션 모니터링 노드

    현재 포지션의 미실현 손익을 계산하고 추적합니다.
    """
    logger.info("[monitor_position] 포지션 모니터링")

    updates: Dict[str, Any] = {}

    if state["position_status"] == "IN_POSITION":
        # 미실현 손익 계산
        unrealized_pnl = (state["current_price"] - state["entry_price"]) * state["position_qty"]
        unrealized_pnl_pct = (state["current_price"] - state["entry_price"]) / state["entry_price"]

        # 최고가/최저가 업데이트
        highest_price = max(state.get("highest_price", 0), state["current_price"])
        lowest_price = min(state.get("lowest_price", float('inf')), state["current_price"])

        updates.update({
            "unrealized_pnl": unrealized_pnl,
            "unrealized_pnl_pct": unrealized_pnl_pct,
            "highest_price": highest_price,
            "lowest_price": lowest_price
        })

        logger.info(
            f"[monitor_position] 미실현 손익: {unrealized_pnl:,.0f}원 "
            f"({unrealized_pnl_pct*100:.2f}%)"
        )

    return updates


def update_account_node(state: TradingState) -> Dict[str, Any]:
    """
    계좌 정보 업데이트 노드

    현금 잔고 및 총 자산을 업데이트합니다.

    Raises:
        RuntimeError: KIS API를 사용할 수 없거나 인증 실패 시
        Exception: 잔고 조회 실패 시
    """
    logger.info("[update_account] 계좌 정보 업데이트")

    # KIS API 사용 가능 여부 확인
    if not KIS_AVAILABLE:
        error_msg = (
            "계좌 정보 업데이트 실패: KIS API를 사용할 수 없습니다.\n"
            "해결 방법:\n"
            "1. 가상환경이 활성화되어 있는지 확인\n"
            "2. 필수 패키지가 설치되어 있는지 확인"
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    # KIS 인증
    if not _init_kis_auth(state["env_mode"]):
        error_msg = (
            "계좌 정보 업데이트 실패: KIS 인증에 실패했습니다.\n"
            "해결 방법:\n"
            "1. config/kis_devlp.yaml 파일 확인\n"
            "2. API 키와 계좌 정보 확인"
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    try:
        # 잔고 조회
        output1, output2 = _call_inquire_balance(state["env_mode"])

        # output2에서 총평가금액 추출
        if output2 and len(output2) > 0:
            total_eval = float(output2[0].get('tot_evlu_amt', 0))  # 총평가금액
            logger.info(f"[update_account] API 잔고 조회 완료: 총평가금액 {total_eval:,.0f}원")

            return {
                "total_asset": total_eval,
                "daily_pnl_pct": (total_eval - state["initial_capital"]) / state["initial_capital"]
            }
        else:
            raise Exception("잔고 데이터 없음")

    except Exception as e:
        error_msg = (
            f"[update_account] 잔고 조회 실패: {e}\n"
            f"실행 모드: {state['env_mode']}\n"
            "해결 방법:\n"
            "1. 계좌 번호가 올바른지 확인\n"
            "2. 네트워크 연결 상태 확인\n"
            "3. KIS API 서버 상태 확인"
        )
        logger.error(error_msg)
        raise Exception(error_msg) from e
