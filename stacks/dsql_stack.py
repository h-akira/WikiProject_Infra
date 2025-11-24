from aws_cdk import (
  Stack,
  aws_dsql as dsql,
  aws_ssm as ssm,
  RemovalPolicy,
  Tags,
)
from constructs import Construct

class DSQLStack(Stack):
  """
  Aurora DSQL Cluster for Wiki Project
  """

  def __init__(
    self,
    scope: Construct,
    construct_id: str,
    ssm_prefix: str,
    environment: str,
    **kwargs
  ) -> None:
    super().__init__(scope, construct_id, **kwargs)

    # Create Aurora DSQL Cluster
    cluster = dsql.CfnCluster(
      self, "WikiDSQLCluster",
      deletion_protection_enabled=True,
    )

    # Store DSQL Cluster endpoint in SSM Parameter Store
    ssm.StringParameter(
      self, "DSQLClusterEndpointParameter",
      parameter_name=f"{ssm_prefix}/host",
      string_value=cluster.attr_endpoint,
      description="Aurora DSQL Cluster Endpoint for Wiki Project",
      tier=ssm.ParameterTier.STANDARD,
    )

    # Add tags
    Tags.of(self).add("Environment", environment)
    Tags.of(self).add("Created", "20251123")

    # Output
    self.cluster = cluster
    self.cluster_endpoint = cluster.attr_endpoint
