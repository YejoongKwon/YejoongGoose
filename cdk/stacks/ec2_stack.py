"""
EC2 Stack for Trading Bot
- t4g.micro (ARM) instance
- Load KIS API keys from config/.env directly into User Data
- Auto-start with Systemd service
- No Secrets Manager (cost saving)
"""
import json
from pathlib import Path

from aws_cdk import (
    Stack,
    CfnOutput,
    aws_ec2 as ec2,
    aws_iam as iam,
)
from constructs import Construct


def load_env_file() -> dict:
    """Load environment variables from config/.env"""
    env_vars = {}
    env_path = Path(__file__).parent.parent.parent / "config" / ".env"

    if env_path.exists():
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key.strip()] = value.strip()
    return env_vars


class Ec2Stack(Stack):
    """Trading Bot EC2 Instance Stack"""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        vpc: ec2.Vpc,
        github_repo: str = "",
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Load environment variables from config/.env
        env_vars = load_env_file()

        # =============================================
        # Security Group
        # =============================================
        self.security_group = ec2.SecurityGroup(
            self,
            "TradingBotSG",
            vpc=vpc,
            security_group_name="trading-bot-sg",
            description="Trading Bot Security Group",
            allow_all_outbound=True,
        )

        # SSH access
        self.security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(22),
            "SSH access",
        )

        # Flask Dashboard (port 5001)
        self.security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(5001),
            "Flask Dashboard",
        )

        # =============================================
        # IAM Role
        # =============================================
        self.role = iam.Role(
            self,
            "TradingBotRole",
            role_name="trading-bot-ec2-role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                # CloudWatch logs
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "CloudWatchAgentServerPolicy"
                ),
                # SSM Session Manager
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonSSMManagedInstanceCore"
                ),
            ],
        )

        # =============================================
        # Build .env content from config/.env
        # =============================================
        env_content = f"""# Runtime Environment
ENV_MODE=demo
FLASK_HOST=0.0.0.0
FLASK_PORT=5001
LOG_LEVEL=INFO

# KIS API - Real Trading
KIS_APP_KEY={env_vars.get("KIS_APP_KEY", "")}
KIS_APP_SECRET={env_vars.get("KIS_APP_SECRET", "")}

# KIS API - Paper Trading
KIS_PAPER_APP_KEY={env_vars.get("KIS_PAPER_APP_KEY", "")}
KIS_PAPER_APP_SECRET={env_vars.get("KIS_PAPER_APP_SECRET", "")}

# KIS Account Info
KIS_HTS_ID={env_vars.get("KIS_HTS_ID", "")}
KIS_ACCT_STOCK={env_vars.get("KIS_ACCT_STOCK", "")}
KIS_ACCT_FUTURE={env_vars.get("KIS_ACCT_FUTURE", "")}
KIS_PAPER_STOCK={env_vars.get("KIS_PAPER_STOCK", "")}
KIS_PAPER_FUTURE={env_vars.get("KIS_PAPER_FUTURE", "")}
KIS_PROD_TYPE={env_vars.get("KIS_PROD_TYPE", "")}
"""

        # =============================================
        # User Data Script (EC2 initialization)
        # =============================================
        user_data = ec2.UserData.for_linux()
        user_data.add_commands(
            "#!/bin/bash",
            "set -ex",
            "",
            "# Log setup",
            "exec > >(tee /var/log/user-data.log) 2>&1",
            "",
            "# System Update",
            "dnf update -y",
            "",
            "# Install Python 3.11 and Git",
            "dnf install -y python3.11 python3.11-pip git",
            "",
            "# Create app user",
            "useradd -m -s /bin/bash trading || true",
            "",
            "# Clone repository",
            "cd /home/trading",
            f'if [ -n "{github_repo}" ]; then',
            f'    git clone {github_repo} trading_bot || true',
            "else",
            '    echo "GitHub repo not specified, skipping clone"',
            "    mkdir -p trading_bot",
            "fi",
            "chown -R trading:trading trading_bot",
            "",
            "# Install dependencies",
            "cd /home/trading/trading_bot",
            "if [ -f requirements.txt ]; then",
            "    pip3.11 install -r requirements.txt",
            "fi",
            "",
            "# Create .env file directly",
            "mkdir -p /home/trading/trading_bot/config",
            f"cat > /home/trading/trading_bot/config/.env << 'ENVEOF'",
            env_content,
            "ENVEOF",
            "",
            "chown trading:trading /home/trading/trading_bot/config/.env",
            "chmod 600 /home/trading/trading_bot/config/.env",
            "",
            "# Setup trading-bot systemd service",
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
            "EnvironmentFile=/home/trading/trading_bot/config/.env",
            "ExecStart=/usr/bin/python3.11 apps/daily_breakout_app.py --mode demo --symbol 069500",
            "Restart=on-failure",
            "RestartSec=10",
            "StandardOutput=journal",
            "StandardError=journal",
            "",
            "[Install]",
            "WantedBy=multi-user.target",
            "EOF",
            "",
            "# Setup trading-web systemd service",
            "cat > /etc/systemd/system/trading-web.service << 'EOF'",
            "[Unit]",
            "Description=Trading Bot Web Dashboard",
            "After=network.target",
            "",
            "[Service]",
            "Type=simple",
            "User=trading",
            "WorkingDirectory=/home/trading/trading_bot",
            "Environment=PYTHONPATH=/home/trading/trading_bot",
            "EnvironmentFile=/home/trading/trading_bot/config/.env",
            "ExecStart=/usr/bin/python3.11 apps/flask_app.py",
            "Restart=always",
            "RestartSec=5",
            "StandardOutput=journal",
            "StandardError=journal",
            "",
            "[Install]",
            "WantedBy=multi-user.target",
            "EOF",
            "",
            "# Setup trading-bot timer (scheduling)",
            "cat > /etc/systemd/system/trading-bot.timer << 'EOF'",
            "[Unit]",
            "Description=Run Trading Bot daily at market open",
            "",
            "[Timer]",
            "OnCalendar=Mon..Fri 09:00:00",
            "Persistent=true",
            "",
            "[Install]",
            "WantedBy=timers.target",
            "EOF",
            "",
            "# Enable and start services",
            "systemctl daemon-reload",
            "systemctl enable trading-web",
            "systemctl start trading-web",
            "systemctl enable trading-bot.timer",
            "systemctl start trading-bot.timer",
            "",
            "echo 'User data script completed successfully'",
        )

        # =============================================
        # EC2 Instance
        # =============================================
        self.instance = ec2.Instance(
            self,
            "TradingBotInstance",
            instance_name="trading-bot",
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            # t4g.micro: ARM, cost-effective (~$3-4/month)
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.T4G,
                ec2.InstanceSize.MICRO,
            ),
            # Amazon Linux 2023 (ARM64)
            machine_image=ec2.MachineImage.latest_amazon_linux2023(
                cpu_type=ec2.AmazonLinuxCpuType.ARM_64
            ),
            security_group=self.security_group,
            role=self.role,
            user_data=user_data,
            # IMDSv2 required (security)
            require_imdsv2=True,
            # EBS volume
            block_devices=[
                ec2.BlockDevice(
                    device_name="/dev/xvda",
                    volume=ec2.BlockDeviceVolume.ebs(
                        volume_size=8,  # 8GB (minimum)
                        volume_type=ec2.EbsDeviceVolumeType.GP3,
                        encrypted=True,
                        delete_on_termination=True,
                    ),
                )
            ],
        )

        # =============================================
        # Elastic IP (static IP)
        # =============================================
        self.eip = ec2.CfnEIP(
            self,
            "TradingBotEIP",
            tags=[{"key": "Name", "value": "trading-bot-eip"}],
        )

        ec2.CfnEIPAssociation(
            self,
            "TradingBotEIPAssoc",
            eip=self.eip.ref,
            instance_id=self.instance.instance_id,
        )

        # =============================================
        # Outputs
        # =============================================
        CfnOutput(
            self,
            "InstanceId",
            value=self.instance.instance_id,
            description="EC2 Instance ID",
            export_name="TradingBotInstanceId",
        )

        CfnOutput(
            self,
            "InstancePublicIP",
            value=self.eip.ref,
            description="Elastic IP Address",
            export_name="TradingBotPublicIP",
        )

        CfnOutput(
            self,
            "SSMConnectCommand",
            value=f"aws ssm start-session --target {self.instance.instance_id} --region ap-northeast-2",
            description="SSM Session Manager connect command",
        )

        CfnOutput(
            self,
            "DashboardURL",
            value=f"http://{self.eip.ref}:5001",
            description="Flask Dashboard URL",
        )
