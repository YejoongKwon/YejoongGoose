# Trading Bot AWS 배포 가이드

## 사전 준비사항

### 1. AWS CLI 설치 및 설정

```bash
# AWS CLI 설치 (macOS)
brew install awscli

# AWS CLI 설정
aws configure
# AWS Access Key ID: [YOUR_ACCESS_KEY]
# AWS Secret Access Key: [YOUR_SECRET_KEY]
# Default region name: ap-northeast-2
# Default output format: json
```

### 2. Node.js 및 AWS CDK 설치

```bash
# Node.js 설치 (CDK 실행에 필요)
brew install node

# AWS CDK CLI 설치
npm install -g aws-cdk

# CDK 버전 확인
cdk --version
```

### 3. Python 가상환경 설정

```bash
cd /Users/yejoong_kwon_babitalk/trading_bot/cdk

# 가상환경 생성
python3 -m venv .venv

# 가상환경 활성화
source .venv/bin/activate

# CDK 의존성 설치
pip install -r requirements.txt
```

---

## 비밀값 설정 가이드

### AWS Secrets Manager에 저장할 KIS API 키

CDK 배포 후 **AWS Secrets Manager**에 다음 값들을 저장해야 합니다.

#### 저장할 비밀값 (Secret Name: `trading-bot/kis-api`)

```json
{
  "KIS_APP_KEY": "실전투자_앱키",
  "KIS_APP_SECRET": "실전투자_앱시크릿",
  "KIS_PAPER_APP_KEY": "모의투자_앱키",
  "KIS_PAPER_APP_SECRET": "모의투자_앱시크릿"
}
```

#### 현재 config/.env에서 복사할 값들

현재 로컬의 `config/.env` 파일에서 다음 값들을 확인하세요:

| 환경 변수 | 설명 | Secrets Manager 키 |
|----------|------|-------------------|
| `KIS_APP_KEY` | 실전투자 APP KEY | `KIS_APP_KEY` |
| `KIS_APP_SECRET` | 실전투자 APP SECRET | `KIS_APP_SECRET` |
| `KIS_PAPER_APP_KEY` | 모의투자 APP KEY | `KIS_PAPER_APP_KEY` |
| `KIS_PAPER_APP_SECRET` | 모의투자 APP SECRET | `KIS_PAPER_APP_SECRET` |

---

## 배포 단계

### Step 1: CDK 부트스트랩 (최초 1회)

```bash
cd /Users/yejoong_kwon_babitalk/trading_bot/cdk
source .venv/bin/activate

# AWS 계정 ID 확인
aws sts get-caller-identity --query Account --output text

# CDK 부트스트랩 실행
cdk bootstrap aws://YOUR_ACCOUNT_ID/ap-northeast-2
```

### Step 2: CDK 배포

```bash
# 변경사항 미리보기
cdk diff

# 전체 스택 배포
cdk deploy --all

# 또는 개별 스택 배포
cdk deploy TradingBotVpc
cdk deploy TradingBotEc2
```

배포 중 IAM 역할 생성에 대한 확인 메시지가 표시되면 `y`를 입력하세요.

### Step 3: Secrets Manager에 API 키 저장

배포 완료 후, AWS 콘솔 또는 CLI로 비밀값을 업데이트합니다.

#### 방법 1: AWS CLI 사용

```bash
# 비밀값 업데이트
aws secretsmanager put-secret-value \
  --secret-id trading-bot/kis-api \
  --region ap-northeast-2 \
  --secret-string '{
    "KIS_APP_KEY": "YOUR_REAL_APP_KEY",
    "KIS_APP_SECRET": "YOUR_REAL_APP_SECRET",
    "KIS_PAPER_APP_KEY": "YOUR_PAPER_APP_KEY",
    "KIS_PAPER_APP_SECRET": "YOUR_PAPER_APP_SECRET"
  }'
```

#### 방법 2: AWS 콘솔 사용

1. AWS 콘솔 → Secrets Manager 이동
2. `trading-bot/kis-api` 시크릿 선택
3. "Retrieve secret value" 클릭
4. "Edit" 버튼 클릭
5. JSON 형식으로 값 입력 후 저장

### Step 4: EC2 인스턴스에서 비밀값 로드

EC2에 접속하여 비밀값이 제대로 로드되었는지 확인합니다.

```bash
# SSM Session Manager로 접속 (SSH 키 불필요)
aws ssm start-session --target INSTANCE_ID --region ap-northeast-2

# 또는 SSH로 접속 (키 페어 설정한 경우)
ssh -i your-key.pem ec2-user@ELASTIC_IP

# trading 사용자로 전환
sudo su - trading

# .env 파일 확인
cat /home/trading/trading_bot/config/.env

# 비밀값 다시 로드 (필요시)
SECRET_JSON=$(aws secretsmanager get-secret-value \
  --secret-id trading-bot/kis-api \
  --region ap-northeast-2 \
  --query SecretString \
  --output text)
echo $SECRET_JSON | jq .
```

### Step 5: 서비스 재시작

비밀값 업데이트 후 서비스를 재시작합니다.

```bash
# EC2에서 실행
sudo systemctl restart trading-web
sudo systemctl restart trading-bot

# 상태 확인
sudo systemctl status trading-web
sudo systemctl status trading-bot
```

---

## 배포 후 확인사항

### 1. 출력값 확인

```bash
# CDK 출력값 조회
cdk deploy TradingBotEc2 --outputs-file outputs.json
cat outputs.json
```

출력값:
- `InstancePublicIP`: Elastic IP 주소
- `InstanceId`: EC2 인스턴스 ID
- `SecretArn`: Secrets Manager ARN
- `DashboardURL`: Flask 대시보드 URL

### 2. 대시보드 접속

```
http://ELASTIC_IP:5001
```

### 3. 로그 확인

```bash
# EC2에서 실행
sudo journalctl -u trading-web -f
sudo journalctl -u trading-bot -f

# User Data 스크립트 로그
sudo cat /var/log/user-data.log
```

### 4. 타이머 확인

```bash
# 스케줄링된 타이머 확인
sudo systemctl list-timers trading-bot.timer
```

---

## 비용 요약

| 서비스 | 사양 | 월 비용 (예상) |
|--------|------|----------------|
| EC2 (t4g.micro) | On-Demand | ~$3-4 |
| EBS (gp3, 8GB) | 스토리지 | ~$0.64 |
| Elastic IP | 사용 중 | $0 |
| Data Transfer | 1GB Out | ~$0.12 |
| Secrets Manager | 1 시크릿 | ~$0.40 |
| **합계** | | **~$4-6/월** |

---

## 문제 해결

### EC2 접속 문제

```bash
# SSM 에이전트 상태 확인 (EC2 내부)
sudo systemctl status amazon-ssm-agent

# Security Group 확인
aws ec2 describe-security-groups \
  --group-names trading-bot-sg \
  --region ap-northeast-2
```

### 서비스 시작 실패

```bash
# 서비스 로그 확인
sudo journalctl -u trading-bot -n 100 --no-pager
sudo journalctl -u trading-web -n 100 --no-pager

# Python 의존성 확인
cd /home/trading/trading_bot
pip3.11 list
```

### Secrets Manager 접근 오류

```bash
# IAM 역할 확인
aws sts get-caller-identity

# Secrets Manager 접근 테스트
aws secretsmanager get-secret-value \
  --secret-id trading-bot/kis-api \
  --region ap-northeast-2
```

---

## 리소스 삭제

```bash
# 전체 스택 삭제
cdk destroy --all

# 개별 삭제 (순서 중요)
cdk destroy TradingBotEc2
cdk destroy TradingBotVpc
```

**주의**: Secrets Manager의 시크릿은 기본적으로 30일간 보관 후 삭제됩니다.
즉시 삭제하려면:

```bash
aws secretsmanager delete-secret \
  --secret-id trading-bot/kis-api \
  --force-delete-without-recovery \
  --region ap-northeast-2
```

---

## 보안 권장사항

1. **SSH 접근 제한**: Security Group에서 특정 IP만 허용
2. **SSM Session Manager 사용**: SSH 키 없이 안전하게 접속
3. **Secrets Manager**: API 키를 코드나 .env 파일에 하드코딩하지 않음
4. **EBS 암호화**: 활성화됨 (기본 설정)
5. **IMDSv2 강제**: 메타데이터 서비스 보안 (기본 설정)

---

## 다음 단계 체크리스트

- [ ] AWS CLI 설치 및 설정
- [ ] CDK 부트스트랩 실행
- [ ] CDK 배포 (`cdk deploy --all`)
- [ ] Secrets Manager에 KIS API 키 저장
- [ ] EC2 접속 및 서비스 상태 확인
- [ ] 대시보드 접속 테스트 (http://IP:5001)
- [ ] Security Group SSH 접근 IP 제한
