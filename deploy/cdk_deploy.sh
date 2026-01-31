#!/bin/bash
# Trading Bot CDK 배포 스크립트
# 계정: 040604761819 (cdk-admin)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CDK_DIR="$PROJECT_ROOT/cdk"
ENV_FILE="$PROJECT_ROOT/config/.env"

echo "========================================"
echo "Trading Bot CDK Deploy Script"
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
ACCOUNT_INFO=$(aws sts get-caller-identity 2>&1)
ACCOUNT_ID=$(echo "$ACCOUNT_INFO" | jq -r '.Account')
USER_ARN=$(echo "$ACCOUNT_INFO" | jq -r '.Arn')

echo "Account ID: $ACCOUNT_ID"
echo "User: $USER_ARN"

if [ "$ACCOUNT_ID" != "040604761819" ]; then
    echo "✗ Error: Expected account 040604761819, got $ACCOUNT_ID"
    echo "Please check AWS credentials in config/.env"
    exit 1
fi
echo "✓ Correct account (040604761819)"

# CDK 디렉토리로 이동
cd "$CDK_DIR"

# Python 가상환경 설정
echo ""
echo ">>> Setting up Python virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✓ Virtual environment created"
fi

source .venv/bin/activate
pip install -q -r requirements.txt
echo "✓ Dependencies installed"

# CDK CLI 확인
if ! command -v cdk &> /dev/null; then
    echo ""
    echo ">>> Installing AWS CDK CLI..."
    npm install -g aws-cdk
fi
echo "✓ CDK CLI ready ($(cdk --version))"

# CDK 부트스트랩 (최초 1회)
echo ""
echo ">>> Checking CDK bootstrap..."

# SSM parameter로 부트스트랩 상태 확인 (더 정확함)
SSM_CHECK=$(aws ssm get-parameter --name "/cdk-bootstrap/hnb659fds/version" --region ap-northeast-2 2>&1 || true)

if echo "$SSM_CHECK" | grep -q "ParameterNotFound\|does not exist\|error\|Error"; then
    echo "CDK bootstrap required. Running bootstrap..."
    cdk bootstrap aws://040604761819/ap-northeast-2
    echo "✓ CDK bootstrap completed"
else
    echo "✓ CDK already bootstrapped"
fi

# 배포 확인
echo ""
echo "========================================"
echo "Ready to deploy the following stacks:"
echo "  - TradingBotVpc"
echo "  - TradingBotEc2"
echo ""
echo "Estimated monthly cost: ~\$6-8"
echo "========================================"
read -p "Proceed with deployment? (y/N): " confirm

if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "Deployment cancelled."
    exit 0
fi

# CDK 배포
echo ""
echo ">>> Deploying CDK stacks..."
cdk deploy --all --require-approval never

# 배포 결과 출력
echo ""
echo "========================================"
echo "Deployment completed!"
echo "========================================"

# Outputs 가져오기
echo ""
echo ">>> Stack Outputs:"
aws cloudformation describe-stacks \
    --stack-name TradingBotEc2 \
    --region ap-northeast-2 \
    --query 'Stacks[0].Outputs[*].[OutputKey,OutputValue]' \
    --output table 2>/dev/null || echo "Could not fetch outputs"

# KIS API keys are embedded directly into EC2 User Data from config/.env
echo ""
echo "✓ KIS API keys loaded from config/.env into EC2 User Data"
echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Wait 5-10 minutes for EC2 initialization"
echo "2. Access dashboard at the URL shown above"
echo "3. Check logs: aws ssm start-session --target <instance-id> --region ap-northeast-2"
echo ""
