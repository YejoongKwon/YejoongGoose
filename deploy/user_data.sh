#!/bin/bash
# Trading Bot EC2 User Data Script
# 이 스크립트는 EC2 인스턴스 시작 시 자동 실행됩니다

set -ex

# 로그 파일 설정
exec > >(tee /var/log/user-data.log) 2>&1

echo "===== Trading Bot Setup Started ====="
echo "Date: $(date)"

# System Update
echo ">>> System Update"
dnf update -y

# Install Python 3.11 and required tools
echo ">>> Installing Python 3.11 and tools"
dnf install -y python3.11 python3.11-pip git jq

# Create app user
echo ">>> Creating trading user"
useradd -m -s /bin/bash trading || true

# Clone repository (환경 변수로 전달된 경우)
echo ">>> Setting up application"
cd /home/trading

if [ -n "${GITHUB_REPO}" ]; then
    echo "Cloning from ${GITHUB_REPO}"
    git clone ${GITHUB_REPO} trading_bot || true
else
    echo "GitHub repo not specified, creating directory"
    mkdir -p trading_bot
fi

chown -R trading:trading trading_bot

# Install dependencies
echo ">>> Installing Python dependencies"
cd /home/trading/trading_bot
if [ -f requirements.txt ]; then
    pip3.11 install -r requirements.txt
fi

# Create config directory
mkdir -p /home/trading/trading_bot/config

# Secrets Manager에서 비밀값 가져오기
echo ">>> Loading secrets from AWS Secrets Manager"
SECRET_JSON=$(aws secretsmanager get-secret-value \
    --secret-id trading-bot/kis-api \
    --region ap-northeast-2 \
    --query SecretString \
    --output text 2>/dev/null || echo "{}")

# .env 파일 생성
echo ">>> Creating .env file"
cat > /home/trading/trading_bot/config/.env << 'ENVEOF'
# 실행 환경
ENV_MODE=demo
FLASK_HOST=0.0.0.0
FLASK_PORT=5001
LOG_LEVEL=INFO

# KIS API 계좌 정보 (Secrets Manager에서 로드)
KIS_HTS_ID=@2702095
KIS_ACCT_STOCK=43573420
KIS_ACCT_FUTURE=43573420
KIS_PROD_TYPE=01
KIS_PAPER_STOCK=50157842
KIS_PAPER_FUTURE=60036022
ENVEOF

# Secrets Manager 값 추가 (API 키들)
if [ "$SECRET_JSON" != "{}" ]; then
    echo "" >> /home/trading/trading_bot/config/.env
    echo "# KIS API Keys from Secrets Manager" >> /home/trading/trading_bot/config/.env
    echo "$SECRET_JSON" | jq -r 'to_entries[] | "\(.key)=\(.value)"' >> /home/trading/trading_bot/config/.env
fi

chown trading:trading /home/trading/trading_bot/config/.env
chmod 600 /home/trading/trading_bot/config/.env

# Setup trading-bot systemd service
echo ">>> Creating systemd services"
cat > /etc/systemd/system/trading-bot.service << 'EOF'
[Unit]
Description=Trading Bot Service
After=network.target

[Service]
Type=simple
User=trading
WorkingDirectory=/home/trading/trading_bot
Environment=PYTHONPATH=/home/trading/trading_bot
EnvironmentFile=/home/trading/trading_bot/config/.env
ExecStart=/usr/bin/python3.11 apps/daily_breakout_app.py --mode demo --symbol 069500
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Setup trading-web systemd service
cat > /etc/systemd/system/trading-web.service << 'EOF'
[Unit]
Description=Trading Bot Web Dashboard
After=network.target

[Service]
Type=simple
User=trading
WorkingDirectory=/home/trading/trading_bot
Environment=PYTHONPATH=/home/trading/trading_bot
EnvironmentFile=/home/trading/trading_bot/config/.env
ExecStart=/usr/bin/python3.11 apps/flask_app.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Setup trading-bot timer (매일 09:00 실행)
cat > /etc/systemd/system/trading-bot.timer << 'EOF'
[Unit]
Description=Run Trading Bot daily at market open

[Timer]
OnCalendar=Mon..Fri 09:00:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Enable and start services
echo ">>> Enabling systemd services"
systemctl daemon-reload
systemctl enable trading-web
systemctl start trading-web
systemctl enable trading-bot.timer
systemctl start trading-bot.timer

echo "===== Trading Bot Setup Completed ====="
echo "Date: $(date)"
echo ""
echo "Services status:"
systemctl status trading-web --no-pager || true
systemctl list-timers trading-bot.timer --no-pager || true
