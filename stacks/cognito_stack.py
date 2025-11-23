from aws_cdk import (
  Stack,
  aws_cognito as cognito,
  aws_ssm as ssm,
  Duration,
  RemovalPolicy,
  Tags,
)
from constructs import Construct

class CognitoStack(Stack):
  """
  Cognito User Pool and Client for Wiki Project
  Equivalent to Terraform: WikiProject_Infra/common/cognito
  """

  def __init__(
    self,
    scope: Construct,
    construct_id: str,
    user_pool_name: str,
    client_name: str,
    ssm_prefix: str,
    environment: str,
    **kwargs
  ) -> None:
    super().__init__(scope, construct_id, **kwargs)

    # Create Cognito User Pool
    user_pool = cognito.UserPool(
      self, "WikiUserPool",
      user_pool_name=user_pool_name,
      self_sign_up_enabled=True,
      # Use sign_in_aliases to allow login with username OR email (alias)
      # This matches Terraform's alias_attributes = ["email"]
      sign_in_aliases=cognito.SignInAliases(
        email=True,
        username=True,  # Allow username login as well as email
      ),
      auto_verify=cognito.AutoVerifiedAttrs(email=True),
      password_policy=cognito.PasswordPolicy(
        min_length=8,
        require_lowercase=True,
        require_uppercase=True,
        require_digits=True,
        require_symbols=True,
      ),
      account_recovery=cognito.AccountRecovery.EMAIL_ONLY,
      removal_policy=RemovalPolicy.RETAIN,
      # Note: CDK doesn't have direct deletion_protection like Terraform
      # Use removal_policy=RETAIN as a safeguard
      # Username configuration - case insensitive (matches Terraform)
      sign_in_case_sensitive=False,
    )

    # Create Cognito User Pool Client
    user_pool_client = cognito.UserPoolClient(
      self, "WikitUserPoolClient",
      user_pool=user_pool,
      user_pool_client_name=client_name,
      generate_secret=True,
      # Auth flows - must match Terraform's explicit_auth_flows
      # Note: ALLOW_REFRESH_TOKEN_AUTH is enabled by default in CDK
      auth_flows=cognito.AuthFlow(
        admin_user_password=True,  # ALLOW_ADMIN_USER_PASSWORD_AUTH
        custom=False,
        user_password=False,
        user_srp=False,
      ),
      access_token_validity=Duration.minutes(30),
      id_token_validity=Duration.minutes(30),
      refresh_token_validity=Duration.days(5),
      enable_token_revocation=True,
      # Prevent user existence errors (matches Terraform)
      prevent_user_existence_errors=True,
      # Supported identity providers (matches Terraform)
      supported_identity_providers=[
        cognito.UserPoolClientIdentityProvider.COGNITO
      ],
    )

    # Store Cognito details in SSM Parameter Store
    ssm.StringParameter(
      self, "UserPoolIdParameter",
      parameter_name=f"{ssm_prefix}/user_pool_id",
      string_value=user_pool.user_pool_id,
      description="Cognito User Pool ID for Wiki Project",
      tier=ssm.ParameterTier.STANDARD,
    )

    ssm.StringParameter(
      self, "ClientIdParameter",
      parameter_name=f"{ssm_prefix}/client_id",
      string_value=user_pool_client.user_pool_client_id,
      description="Cognito User Pool Client ID for Wiki Project",
      tier=ssm.ParameterTier.STANDARD,
    )

    # Store Client Secret
    # Note: This will be stored as a regular String parameter, not SecureString
    # CDK's StringParameter doesn't support SecureString type
    ssm.StringParameter(
      self, "ClientSecretParameter",
      parameter_name=f"{ssm_prefix}/client_secret",
      string_value=user_pool_client.user_pool_client_secret.unsafe_unwrap(),
      description="Cognito User Pool Client Secret",
      tier=ssm.ParameterTier.STANDARD,
    )

    # Add tags
    Tags.of(self).add("Environment", environment)
    Tags.of(self).add("Created", "20251026")

    # Outputs (similar to Terraform outputs)
    self.user_pool = user_pool
    self.user_pool_client = user_pool_client
