#!/bin/bash
# Trading Bot CDK 삭제 스크립트
# 계정: 040604761819 (cdk-admin)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CDK_DIR="$PROJECT_ROOT/cdk"
ENV_FILE="$PROJECT_ROOT/config/.env"

echo "========================================"
echo "Trading Bot CDK Destroy Script"
echo "========================================"

# .env 파일에서 AWS 자격 증명 로드
if [ -f "$ENV_FILE" ]; then
    export $(grep -E '^AWS_' "$ENV_FILE" | xargs)
    echo "✓ AWS credentials loaded from config/.env"
else
    echo "✗ Error: $ENV_FILE not found"
    exit 1
fi

# 계정 확인
echo ""
echo ">>> Checking AWS Account..."
ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text 2>&1)
echo "Account ID: $ACCOUNT_ID"

if [ "$ACCOUNT_ID" != "040604761819" ]; then
    echo "✗ Error: Expected account 040604761819, got $ACCOUNT_ID"
    exit 1
fi
echo "✓ Correct account (040604761819)"

# CDK 디렉토리로 이동
cd "$CDK_DIR"

# Python 가상환경 활성화
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# 현재 스택 목록
echo ""
echo ">>> Current stacks:"
aws cloudformation list-stacks \
    --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
    --region ap-northeast-2 \
    --query 'StackSummaries[?starts_with(StackName, `TradingBot`)].StackName' \
    --output table 2>/dev/null || echo "No stacks found"

# 삭제 확인
echo ""
echo "========================================"
echo "WARNING: This will delete all Trading Bot resources!"
echo "  - TradingBotEc2 (EC2, EIP, Security Group, IAM Role, Secret)"
echo "  - TradingBotVpc (VPC, Subnet, Internet Gateway)"
echo "========================================"
read -p "Are you sure? Type 'delete' to confirm: " confirm

if [ "$confirm" != "delete" ]; then
    echo "Destruction cancelled."
    exit 0
fi

# CDK 삭제
echo ""
echo ">>> Destroying CDK stacks..."
cdk destroy --all --force

echo ""
echo "========================================"
echo "Destruction completed!"
echo "========================================"

# 남은 리소스 확인
echo ""
echo ">>> Checking remaining stacks..."
aws cloudformation list-stacks \
    --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE DELETE_FAILED \
    --region ap-northeast-2 \
    --query 'StackSummaries[?starts_with(StackName, `TradingBot`)].{Name:StackName,Status:StackStatus}' \
    --output table 2>/dev/null || echo "No stacks found"

echo ""
echo "Note: If any stacks show DELETE_FAILED, delete them manually from AWS Console"
echo "      CloudFormation → Stacks → Select stack → Delete (with Retain option if needed)"
