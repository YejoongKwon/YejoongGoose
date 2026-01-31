#!/bin/bash
# GitHub Actions 배포를 위한 S3 버킷 생성 및 IAM 권한 설정
# 최초 1회만 실행

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/config/.env"

echo "========================================"
echo "Setup GitHub Actions Deploy"
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

BUCKET_NAME="trading-bot-deploy-${ACCOUNT_ID}"
REGION="ap-northeast-2"

# S3 버킷 생성
echo ""
echo ">>> Creating S3 bucket: $BUCKET_NAME"
if aws s3 ls "s3://$BUCKET_NAME" 2>&1 | grep -q 'NoSuchBucket'; then
    aws s3 mb "s3://$BUCKET_NAME" --region $REGION
    echo "✓ S3 bucket created"
else
    echo "✓ S3 bucket already exists"
fi

# EC2 역할에 S3 읽기 권한 추가
echo ""
echo ">>> Adding S3 read permission to EC2 role"
cat > /tmp/s3-policy.json << EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::$BUCKET_NAME",
                "arn:aws:s3:::$BUCKET_NAME/*"
            ]
        }
    ]
}
EOF

aws iam put-role-policy \
    --role-name trading-bot-ec2-role \
    --policy-name S3DeployAccess \
    --policy-document file:///tmp/s3-policy.json 2>/dev/null || echo "Policy may already exist or role not found"

rm /tmp/s3-policy.json

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Create a GitHub repository"
echo "2. Add these secrets to GitHub repository settings:"
echo "   - AWS_ACCESS_KEY_ID: $AWS_ACCESS_KEY_ID"
echo "   - AWS_SECRET_ACCESS_KEY: (from config/.env)"
echo "   - AWS_ACCOUNT_ID: $ACCOUNT_ID"
echo ""
echo "3. Push code to GitHub:"
echo "   git remote add origin https://github.com/YOUR_USERNAME/trading_bot.git"
echo "   git push -u origin main"
echo ""
echo "4. GitHub Actions will automatically deploy on push to main"
echo ""
