#!/usr/bin/env python3
"""
변동성 돌파 일간 실행 앱

LangGraph 기반 자동매매 봇을 실행하는 CLI 앱
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from datetime import datetime
import yaml
from dotenv import load_dotenv

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 환경 변수 로드
env_file = project_root / "config" / "settings.example.env"
if env_file.exists():
    load_dotenv(env_file)

from skills.trading_core.graph.graph_builder import build_trading_graph
from skills.trading_core.graph.state import create_initial_state


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    로깅 설정

    Args:
        log_level: 로그 레벨

    Returns:
        Logger 인스턴스
    """
    log_dir = project_root.parent / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / f"trading_{datetime.now().strftime('%Y%m%d')}.log"

    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info("변동성 돌파 자동매매 봇 시작 (LangGraph)")
    logger.info("=" * 80)

    return logger


def load_strategy_config(config_path: Path) -> dict:
    """
    전략 설정 로드

    Args:
        config_path: 설정 파일 경로

    Returns:
        설정 딕셔너리
    """
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    return config


def main():
    """메인 실행 함수"""
    # 명령행 인수 파싱
    parser = argparse.ArgumentParser(
        description='변동성 돌파 자동매매 봇 (LangGraph)'
    )
    parser.add_argument(
        '--mode',
        choices=['demo', 'real'],
        default='demo',
        help='거래 모드 (demo: 모의투자, real: 실전투자)'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config/trading_config.yaml',
        help='전략 설정 파일 경로'
    )
    parser.add_argument(
        '--symbol',
        type=str,
        default='069500',
        help='거래 종목 코드'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='로그 레벨'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='실제 주문 없이 시뮬레이션만 실행'
    )

    args = parser.parse_args()

    # 로깅 설정
    logger = setup_logging(args.log_level)

    try:
        # 전략 설정 로드
        config_path = project_root / args.config
        if not config_path.exists():
            logger.error(f"설정 파일을 찾을 수 없습니다: {config_path}")
            return 1

        config = load_strategy_config(config_path)
        logger.info(f"전략 설정 로드 완료: {config_path}")

        # LangGraph 빌드
        logger.info("LangGraph 빌드 시작...")
        graph = build_trading_graph()
        logger.info("LangGraph 빌드 완료")

        # 초기 상태 생성 (config 값으로 오버라이드)
        initial_state = create_initial_state(
            symbol=args.symbol,
            initial_capital=config.get('trading', {}).get('capital'),
            k_value=config.get('volatility_breakout', {}).get('k_value'),
            stop_loss_pct=config.get('risk', {}).get('stop_loss'),
            take_profit_pct=config.get('risk', {}).get('take_profit'),
            env_mode=args.mode
        )

        logger.info(f"초기 상태 생성 완료: {args.symbol}")
        logger.info(f"  - 초기 자본: {config.get('trading', {}).get('capital', 0):,.0f}원")
        logger.info(f"  - k 값: {config.get('volatility_breakout', {}).get('k_value', 0)}")
        logger.info(f"  - 손절매: {config.get('risk', {}).get('stop_loss', 0)*100}%")
        logger.info(f"  - 익절: {config.get('risk', {}).get('take_profit', 0)*100}%")

        if args.dry_run:
            logger.warning("DRY-RUN 모드: 실제 주문은 실행되지 않습니다")
            initial_state["debug_mode"] = True

        # LangGraph 실행
        logger.info("=" * 80)
        logger.info("LangGraph 실행 시작")
        logger.info("=" * 80)

        result = graph.invoke(initial_state)

        # 결과 출력
        logger.info("=" * 80)
        logger.info("실행 결과")
        logger.info("=" * 80)
        logger.info(f"종목: {result['symbol']} ({result.get('symbol_name', '')})")
        logger.info(f"현재가: {result['current_price']:,.0f}원")
        logger.info(f"목표가: {result['target_price']:,.0f}원")
        logger.info(f"포지션: {result['position_status']}")

        if result['position_status'] == 'IN_POSITION':
            logger.info(f"진입가: {result['entry_price']:,.0f}원")
            logger.info(f"보유수량: {result['position_qty']}주")
            logger.info(f"미실현손익: {result['unrealized_pnl']:,.0f}원 ({result['unrealized_pnl_pct']*100:.2f}%)")

        logger.info(f"일일손익: {result['daily_pnl']:,.0f}원 ({result['daily_pnl_pct']*100:.2f}%)")
        logger.info(f"총자산: {result['total_asset']:,.0f}원")
        logger.info(f"총거래수: {result['total_trades']}회 (승: {result['winning_trades']}, 패: {result['losing_trades']})")

        if result['trading_stopped']:
            logger.warning(f"거래 중단: {result['stop_reason']}")

        logger.info("=" * 80)

        return 0

    except FileNotFoundError as e:
        logger.error(f"파일을 찾을 수 없습니다: {e}")
        return 1
    except Exception as e:
        logger.error(f"예기치 않은 오류 발생: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
