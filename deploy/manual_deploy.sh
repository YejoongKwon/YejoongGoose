#!/bin/bash
# 수동 배포 스크립트 - 로컬에서 EC2로 직접 배포
# GitHub Actions 설정 전에 사용하거나 긴급 배포 시 사용

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/config/.env"

echo "========================================"
echo "Manual Deploy to EC2"
echo "========================================"

# .env 파일에서 AWS 자격 증명 로드
if [ -f "$ENV_FILE" ]; then
    export $(grep -E '^AWS_' "$ENV_FILE" | xargs)
    echo "✓ AWS credentials loaded"
else
    echo "✗ Error: $ENV_FILE not found"
    exit 1
fi

# 계정 확인
ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)
echo "Account ID: $ACCOUNT_ID"

if [ "$ACCOUNT_ID" != "040604761819" ]; then
    echo "✗ Error: Expected account 040604761819, got $ACCOUNT_ID"
    exit 1
fi
echo "✓ Correct account"

# EC2 인스턴스 ID 찾기
echo ""
echo ">>> Finding EC2 instance..."
INSTANCE_ID=$(aws ec2 describe-instances \
    --filters "Name=tag:Name,Values=trading-bot" "Name=instance-state-name,Values=running" \
    --query 'Reservations[*].Instances[*].InstanceId' \
    --output text \
    --region ap-northeast-2)

if [ -z "$INSTANCE_ID" ]; then
    echo "✗ Error: No running trading-bot instance found"
    exit 1
fi
echo "✓ Instance ID: $INSTANCE_ID"

# S3 버킷
BUCKET_NAME="trading-bot-deploy-${ACCOUNT_ID}"
REGION="ap-northeast-2"

# S3 버킷 확인/생성
echo ""
echo ">>> Checking S3 bucket..."
if ! aws s3 ls "s3://$BUCKET_NAME" 2>/dev/null; then
    echo "Creating S3 bucket: $BUCKET_NAME"
    aws s3 mb "s3://$BUCKET_NAME" --region $REGION
fi
echo "✓ S3 bucket ready"

# 배포 패키지 생성
echo ""
echo ">>> Creating deployment package..."
cd "$PROJECT_ROOT"
tar -czf /tmp/deploy.tar.gz \
    --exclude='.git' \
    --exclude='.github' \
    --exclude='venv' \
    --exclude='.venv' \
    --exclude='cdk/.venv' \
    --exclude='cdk/cdk.out' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache' \
    --exclude='data/logs/*' \
    --exclude='config/.env' \
    --exclude='config/KIS*' \
    .
echo "✓ Package created: $(du -h /tmp/deploy.tar.gz | cut -f1)"

# S3에 업로드
echo ""
echo ">>> Uploading to S3..."
aws s3 cp /tmp/deploy.tar.gz "s3://$BUCKET_NAME/deploy.tar.gz"
echo "✓ Uploaded to S3"

# EC2에 배포
echo ""
echo ">>> Deploying to EC2..."
COMMAND_ID=$(aws ssm send-command \
    --instance-ids "$INSTANCE_ID" \
    --document-name "AWS-RunShellScript" \
    --parameters "commands=[
        'cd /home/trading/trading_bot',
        'aws s3 cp s3://$BUCKET_NAME/deploy.tar.gz /tmp/deploy.tar.gz',
        'tar -xzf /tmp/deploy.tar.gz -C /home/trading/trading_bot',
        'chown -R trading:trading /home/trading/trading_bot',
        'pip3.11 install -r requirements.txt --quiet',
        'systemctl restart trading-web',
        'systemctl restart trading-bot.timer',
        'rm /tmp/deploy.tar.gz',
        'echo Deploy completed at \$(date)'
    ]" \
    --region $REGION \
    --output text \
    --query "Command.CommandId")

echo "Command ID: $COMMAND_ID"

# 배포 결과 대기
echo ""
echo ">>> Waiting for deployment to complete..."
sleep 5

# 결과 확인
aws ssm get-command-invocation \
    --command-id "$COMMAND_ID" \
    --instance-id "$INSTANCE_ID" \
    --region $REGION \
    --query '[Status, StatusDetails]' \
    --output text 2>/dev/null || echo "Still running..."

sleep 5

STATUS=$(aws ssm get-command-invocation \
    --command-id "$COMMAND_ID" \
    --instance-id "$INSTANCE_ID" \
    --region $REGION \
    --query 'Status' \
    --output text 2>/dev/null || echo "Pending")

if [ "$STATUS" = "Success" ]; then
    echo ""
    echo "========================================"
    echo "✓ Deployment completed successfully!"
    echo "========================================"
    echo ""
    echo "Dashboard: http://15.164.38.157:5001"
else
    echo ""
    echo "Deployment status: $STATUS"
    echo "Check logs with: aws ssm get-command-invocation --command-id $COMMAND_ID --instance-id $INSTANCE_ID --region $REGION"
fi

# 정리
rm -f /tmp/deploy.tar.gz
