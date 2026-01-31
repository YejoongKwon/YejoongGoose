# Trading Bot AWS CDK 배포 아키텍처

## 개요

Trading Bot을 EC2에 배포하기 위한 비용 효율적인 AWS CDK 아키텍처입니다.

---

## 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────────┐
│                         AWS Cloud                                │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                      VPC (10.0.0.0/16)                     │  │
│  │                                                            │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │              Public Subnet (10.0.1.0/24)            │  │  │
│  │  │                                                      │  │  │
│  │  │  ┌────────────────────────────────────────────────┐ │  │  │
│  │  │  │           EC2 (t3.micro / t4g.micro)           │ │  │  │
│  │  │  │                                                 │ │  │  │
│  │  │  │  ┌─────────────┐    ┌─────────────────────┐   │ │  │  │
│  │  │  │  │ Trading Bot │    │ Flask Dashboard     │   │ │  │  │
│  │  │  │  │ (Python)    │    │ (Port 5001)         │   │ │  │  │
│  │  │  │  └─────────────┘    └─────────────────────┘   │ │  │  │
│  │  │  │                                                 │ │  │  │
│  │  │  │  ┌─────────────────────────────────────────┐   │ │  │  │
│  │  │  │  │ Systemd Services                        │   │ │  │  │
│  │  │  │  │ - trading-bot.service (cron 대체)       │   │ │  │  │
│  │  │  │  │ - trading-web.service                   │   │ │  │  │
│  │  │  │  └─────────────────────────────────────────┘   │ │  │  │
│  │  │  └────────────────────────────────────────────────┘ │  │  │
│  │  │                         │                            │  │  │
│  │  │                    Elastic IP                        │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │                                                            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ CloudWatch Logs │  │ Secrets Manager │  │ S3 (선택사항)   │ │
│  │ - 거래 로그     │  │ - KIS API Keys  │  │ - 백업/기록     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
            ┌─────────────────────────────────┐
            │     한국투자증권 Open API        │
            │  openapi.koreainvestment.com    │
            └─────────────────────────────────┘
```

---

## 비용 효율적인 인스턴스 선택

### 권장 옵션 (예상 월간 비용)

| 옵션 | 인스턴스 | vCPU | 메모리 | 월 비용 | 적합 상황 |
|------|----------|------|--------|---------|-----------|
| **1. 최저 비용** | t4g.micro | 2 | 1GB | ~$3-4 | 테스트/모의투자 |
| **2. 권장** | t3.micro | 2 | 1GB | ~$7-8 | 일반 운영 |
| **3. 여유** | t3.small | 2 | 2GB | ~$15-17 | 안정적 운영 |

### 비용 절감 전략

1. **Spot 인스턴스**: 70-90% 비용 절감 (중단 허용 시)
2. **Reserved Instance (1년)**: 약 30% 절감
3. **Savings Plans**: 유연한 할인 옵션

### 권장: t4g.micro (ARM 기반)
- **이유**: ARM 프로세서로 가격 대비 성능 우수
- **Python 호환**: 완전 호환
- **예상 월 비용**: $3-4 (On-Demand 기준)

---

## CDK 스택 구성

### 1. 디렉토리 구조

```
trading_bot/
├── cdk/                          # CDK 프로젝트
│   ├── app.py                    # CDK 앱 진입점
│   ├── cdk.json                  # CDK 설정
│   ├── requirements.txt          # CDK 의존성
│   └── stacks/
│       ├── __init__.py
│       ├── vpc_stack.py          # VPC 스택
│       ├── ec2_stack.py          # EC2 스택
│       └── monitoring_stack.py   # 모니터링 스택 (선택)
└── deploy/
    ├── user_data.sh              # EC2 초기화 스크립트
    └── trading-bot.service       # Systemd 서비스 파일
```

### 2. VPC 스택 (최소 구성)

```python
# cdk/stacks/vpc_stack.py
from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
)
from constructs import Construct

class VpcStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # 단일 AZ, Public Subnet만 사용 (비용 절감)
        self.vpc = ec2.Vpc(
            self, "TradingBotVpc",
            max_azs=1,
            nat_gateways=0,  # NAT Gateway 없음 (월 $32 절약)
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                )
            ]
        )
```

### 3. EC2 스택

```python
# cdk/stacks/ec2_stack.py
from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
    CfnOutput,
)
from constructs import Construct

class Ec2Stack(Stack):
    def __init__(self, scope: Construct, id: str, vpc: ec2.Vpc, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Security Group
        sg = ec2.SecurityGroup(
            self, "TradingBotSG",
            vpc=vpc,
            description="Trading Bot Security Group",
            allow_all_outbound=True
        )

        # SSH 접근 (개인 IP만 허용 권장)
        sg.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(22),
            "SSH access"
        )

        # Flask Dashboard (필요시)
        sg.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(5001),
            "Flask Dashboard"
        )

        # IAM Role
        role = iam.Role(
            self, "TradingBotRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "CloudWatchAgentServerPolicy"
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonSSMManagedInstanceCore"
                )
            ]
        )

        # User Data Script
        user_data = ec2.UserData.for_linux()
        user_data.add_commands(
            "#!/bin/bash",
            "set -e",
            "",
            "# System Update",
            "yum update -y",
            "",
            "# Install Python 3.11+",
            "yum install -y python3.11 python3.11-pip git",
            "",
            "# Create app user",
            "useradd -m -s /bin/bash trading",
            "",
            "# Clone repository (또는 S3에서 다운로드)",
            "cd /home/trading",
            "git clone https://github.com/YOUR_REPO/trading_bot.git",
            "chown -R trading:trading trading_bot",
            "",
            "# Install dependencies",
            "cd trading_bot",
            "pip3.11 install -r requirements.txt",
            "",
            "# Setup systemd service",
            "cat > /etc/systemd/system/trading-bot.service << 'EOF'",
            "[Unit]",
            "Description=Trading Bot Service",
            "After=network.target",
            "",
            "[Service]",
            "Type=simple",
            "User=trading",
            "WorkingDirectory=/home/trading/trading_bot",
            "Environment=PYTHONPATH=/home/trading/trading_bot",
            "ExecStart=/usr/bin/python3.11 apps/daily_breakout_app.py --mode demo",
            "Restart=on-failure",
            "RestartSec=10",
            "",
            "[Install]",
            "WantedBy=multi-user.target",
            "EOF",
            "",
            "# Enable and start service",
            "systemctl daemon-reload",
            "systemctl enable trading-bot",
        )

        # EC2 Instance (ARM 기반 t4g.micro 권장)
        instance = ec2.Instance(
            self, "TradingBotInstance",
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.T4G,
                ec2.InstanceSize.MICRO
            ),
            machine_image=ec2.MachineImage.latest_amazon_linux2023(
                cpu_type=ec2.AmazonLinuxCpuType.ARM_64
            ),
            security_group=sg,
            role=role,
            user_data=user_data,
            key_name="your-key-pair",  # SSH 키 이름
        )

        # Elastic IP (고정 IP)
        eip = ec2.CfnEIP(self, "TradingBotEIP")
        ec2.CfnEIPAssociation(
            self, "TradingBotEIPAssoc",
            eip=eip.ref,
            instance_id=instance.instance_id
        )

        CfnOutput(self, "InstancePublicIP", value=eip.ref)
        CfnOutput(self, "InstanceId", value=instance.instance_id)
```

### 4. CDK App

```python
# cdk/app.py
#!/usr/bin/env python3
import aws_cdk as cdk
from stacks.vpc_stack import VpcStack
from stacks.ec2_stack import Ec2Stack

app = cdk.App()

# 환경 설정
env = cdk.Environment(
    account="YOUR_ACCOUNT_ID",
    region="ap-northeast-2"  # 서울 리전
)

# 스택 생성
vpc_stack = VpcStack(app, "TradingBotVpc", env=env)
ec2_stack = Ec2Stack(
    app, "TradingBotEc2",
    vpc=vpc_stack.vpc,
    env=env
)

app.synth()
```

---

## Systemd 서비스 설정

### trading-bot.service (거래 봇)

```ini
[Unit]
Description=Trading Bot Service
After=network.target

[Service]
Type=simple
User=trading
WorkingDirectory=/home/trading/trading_bot
Environment=PYTHONPATH=/home/trading/trading_bot
Environment=ENV_MODE=demo
ExecStart=/usr/bin/python3.11 apps/daily_breakout_app.py --mode demo --symbol 069500
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### trading-web.service (웹 대시보드)

```ini
[Unit]
Description=Trading Bot Web Dashboard
After=network.target

[Service]
Type=simple
User=trading
WorkingDirectory=/home/trading/trading_bot
Environment=PYTHONPATH=/home/trading/trading_bot
Environment=FLASK_HOST=0.0.0.0
Environment=FLASK_PORT=5001
ExecStart=/usr/bin/python3.11 apps/flask_app.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### Systemd Timer (스케줄링)

```ini
# /etc/systemd/system/trading-bot.timer
[Unit]
Description=Run Trading Bot daily at market open

[Timer]
OnCalendar=Mon..Fri 09:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

---

## Secrets Manager 설정 (권장)

API 키를 안전하게 관리하기 위해 AWS Secrets Manager 사용을 권장합니다.

```python
# secrets 조회 코드 (kis_auth.py에 추가)
import boto3
import json

def get_kis_secrets():
    client = boto3.client('secretsmanager', region_name='ap-northeast-2')
    response = client.get_secret_value(SecretId='trading-bot/kis-api')
    return json.loads(response['SecretString'])
```

### CDK에서 Secret 생성

```python
from aws_cdk import aws_secretsmanager as sm

secret = sm.Secret(
    self, "KisApiSecret",
    secret_name="trading-bot/kis-api",
    description="KIS API credentials"
)
```

---

## 비용 요약

### 최소 구성 (월간 예상)

| 서비스 | 사양 | 월 비용 |
|--------|------|---------|
| EC2 (t4g.micro) | On-Demand | ~$3-4 |
| EBS (gp3, 8GB) | 스토리지 | ~$0.64 |
| Elastic IP | 사용 중 무료 | $0 |
| Data Transfer | 1GB 아웃바운드 | ~$0.12 |
| CloudWatch Logs | 5GB | ~$2.50 |
| **합계** | | **~$6-8/월** |

### 추가 비용 옵션

| 서비스 | 월 비용 | 비고 |
|--------|---------|------|
| Secrets Manager | $0.40/시크릿 | 권장 |
| S3 (백업) | ~$0.50 | 선택 |
| Route53 (도메인) | $0.50 | 선택 |

### 비용 절감 팁

1. **Spot 인스턴스**: t4g.micro Spot = ~$1.5/월 (70% 절감)
2. **Reserved Instance (1년)**: ~$2.5/월 (40% 절감)
3. **Free Tier 활용**: 신규 계정 12개월 무료

---

## 배포 명령어

```bash
# 1. CDK 설치
pip install aws-cdk-lib constructs

# 2. CDK 부트스트랩 (최초 1회)
cdk bootstrap aws://ACCOUNT_ID/ap-northeast-2

# 3. 배포
cd cdk
cdk deploy --all

# 4. EC2 접속
ssh -i your-key.pem ec2-user@<ELASTIC_IP>

# 5. 서비스 확인
sudo systemctl status trading-bot
sudo journalctl -u trading-bot -f
```

---

## 모니터링 및 알림

### CloudWatch 알람 (선택)

```python
from aws_cdk import aws_cloudwatch as cw
from aws_cdk import aws_cloudwatch_actions as cw_actions
from aws_cdk import aws_sns as sns

# SNS Topic for alerts
topic = sns.Topic(self, "TradingAlerts")

# CPU 사용률 알람
cw.Alarm(
    self, "CpuAlarm",
    metric=instance.metric_cpu_utilization(),
    threshold=80,
    evaluation_periods=2,
    actions_enabled=True,
).add_alarm_action(cw_actions.SnsAction(topic))
```

---

## 보안 권장사항

1. **SSH 접근 제한**: 특정 IP만 허용
2. **Secrets Manager**: API 키 안전 관리
3. **VPC Flow Logs**: 네트워크 모니터링
4. **IMDSv2 강제**: 메타데이터 서비스 보안
5. **자동 패치**: Amazon Linux 2023 자동 업데이트

---

## 다음 단계

1. [ ] CDK 프로젝트 디렉토리 생성
2. [ ] AWS 계정 설정 및 자격 증명 구성
3. [ ] SSH 키 페어 생성
4. [ ] Secrets Manager에 KIS API 키 저장
5. [ ] CDK 배포 실행
6. [ ] 서비스 상태 확인 및 로그 모니터링
