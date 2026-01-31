"""
VPC Stack for Trading Bot
- 단일 AZ, Public Subnet만 사용 (비용 절감)
- NAT Gateway 없음 (월 $32 절약)
"""
from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    CfnOutput,
)
from constructs import Construct


class VpcStack(Stack):
    """최소 비용의 VPC 구성"""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # 단일 AZ, Public Subnet만 사용 (비용 절감)
        self.vpc = ec2.Vpc(
            self,
            "TradingBotVpc",
            vpc_name="trading-bot-vpc",
            max_azs=1,
            nat_gateways=0,  # NAT Gateway 없음 (월 $32 절약)
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                )
            ],
            # 기본 CIDR
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
        )

        # Outputs
        CfnOutput(
            self,
            "VpcId",
            value=self.vpc.vpc_id,
            description="VPC ID",
            export_name="TradingBotVpcId",
        )

        CfnOutput(
            self,
            "PublicSubnetId",
            value=self.vpc.public_subnets[0].subnet_id,
            description="Public Subnet ID",
            export_name="TradingBotPublicSubnetId",
        )
