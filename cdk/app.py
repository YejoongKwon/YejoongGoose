#!/usr/bin/env python3
"""
Trading Bot CDK Application
AWS CDK를 사용한 인프라 배포
"""
import os
import aws_cdk as cdk
from stacks.vpc_stack import VpcStack
from stacks.ec2_stack import Ec2Stack


# =============================================
# 환경 설정
# =============================================
# AWS 계정 ID와 리전은 환경 변수 또는 기본값 사용
ACCOUNT = os.environ.get("CDK_DEFAULT_ACCOUNT", os.environ.get("AWS_ACCOUNT_ID", ""))
REGION = os.environ.get("CDK_DEFAULT_REGION", "ap-northeast-2")  # 서울 리전

# GitHub 리포지토리 URL (선택사항)
# 예: "https://github.com/username/trading_bot.git"
GITHUB_REPO = os.environ.get("GITHUB_REPO", "")


def main():
    app = cdk.App()

    # 환경 설정
    env = cdk.Environment(
        account=ACCOUNT,
        region=REGION,
    )

    # =============================================
    # 스택 생성
    # =============================================

    # 1. VPC 스택
    vpc_stack = VpcStack(
        app,
        "TradingBotVpc",
        env=env,
        description="Trading Bot VPC - 단일 AZ, Public Subnet",
    )

    # 2. EC2 스택
    ec2_stack = Ec2Stack(
        app,
        "TradingBotEc2",
        vpc=vpc_stack.vpc,
        github_repo=GITHUB_REPO,
        env=env,
        description="Trading Bot EC2 Instance",
    )

    # 스택 의존성 설정
    ec2_stack.add_dependency(vpc_stack)

    # 태그 추가
    cdk.Tags.of(app).add("Project", "trading-bot")
    cdk.Tags.of(app).add("Environment", "production")
    cdk.Tags.of(app).add("ManagedBy", "CDK")

    app.synth()


if __name__ == "__main__":
    main()
