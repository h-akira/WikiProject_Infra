#!/usr/bin/env python3
import os
import json
import aws_cdk as cdk

from stacks import (
  CognitoStack,
  DashboardMainStack,
  DSQLStack,
)

# Load configuration from config.json
with open("config.json", "r") as f:
  config = json.load(f)

# Get account from environment or config
account = config.get("account") or os.getenv("CDK_DEFAULT_ACCOUNT")
region = config["region"]
environment = config["environment"]

app = cdk.App()

# Stack 1: Cognito (Common Authentication)
# Deploy this first
cognito_stack = CognitoStack(
  app,
  "stack-finance-common-infra-cognito",
  user_pool_name=config["cognito"]["user_pool_name"],
  client_name=config["cognito"]["client_name"],
  ssm_prefix=config["cognito"]["ssm_prefix"],
  environment=environment,
  env=cdk.Environment(account=account, region=region),
  description="Cognito User Pool and Client for Finance Project",
)

# Stack 2: Aurora DSQL Cluster for Wiki Project
dsql_stack = DSQLStack(
  app,
  "stack-wiki-infra-dsql",
  ssm_prefix=config["dsql"]["ssm_prefix"],
  environment=environment,
  env=cdk.Environment(account=account, region=region),
  description="Aurora DSQL Cluster for Wiki Project",
)

# Stack 3: Main (S3 + CloudFront)
# Deploy this after SAM stack is deployed
# API Gateway URL is automatically imported from SAM stack output
main_stack = DashboardMainStack(
  app,
  "stack-wiki-infra-main",
  domain_name=config["main"]["domain_name"],
  acm_certificate_arn=config["main"]["acm_certificate_arn"],
  s3_bucket_name=config["main"]["s3_bucket_name"],
  s3_origin_path=config["main"]["s3_origin_path"],
  app_stack_name=config["main"]["app_stack_name"],
  environment=environment,
  env=cdk.Environment(account=account, region=region),
  description="S3 + CloudFront for Frontend (auto-imports API Gateway URL from SAM)",
)
# Note: Ensure SAM stack is deployed before deploying this stack

app.synth()
