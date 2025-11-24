from aws_cdk import (
  Stack,
  aws_s3 as s3,
  aws_cloudfront as cloudfront,
  aws_cloudfront_origins as origins,
  aws_certificatemanager as acm,
  aws_iam as iam,
  RemovalPolicy,
  CfnOutput,
  Duration,
  Tags,
  Fn,
)
from constructs import Construct

class MainStack(Stack):
  """
  S3 + CloudFront Stack for Wiki Project Frontend
  """

  def __init__(
    self,
    scope: Construct,
    construct_id: str,
    domain_name: str,
    acm_certificate_arn: str,
    s3_bucket_name: str,
    s3_origin_path: str,
    app_stack_name: str,
    environment: str,
    **kwargs
  ) -> None:
    super().__init__(scope, construct_id, **kwargs)

    # Import API Gateway URL from Backend stack output
    api_gateway_url = Fn.import_value(f"{app_stack_name}-ApiUrl")

    # Extract domain and stage from URL
    # Expected format: https://{api-id}.execute-api.{region}.amazonaws.com/{stage}/
    # We'll use Fn.select and Fn.split to parse the URL
    api_gateway_domain_name = Fn.select(2, Fn.split("/", api_gateway_url))
    api_gateway_stage_name = Fn.select(3, Fn.split("/", api_gateway_url))

    # Create S3 bucket for frontend hosting
    frontend_bucket = s3.Bucket(
      self, "ContentsBucket",
      bucket_name=s3_bucket_name,
      block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
      removal_policy=RemovalPolicy.RETAIN,
      auto_delete_objects=False,
    )

    # Import existing ACM certificate
    certificate = acm.Certificate.from_certificate_arn(
      self, "Certificate",
      certificate_arn=acm_certificate_arn
    )

    # Create Origin Access Control for S3
    s3_oac = cloudfront.S3OriginAccessControl(
      self, "S3OAC",
      signing=cloudfront.Signing.SIGV4_NO_OVERRIDE,
    )

    # Create S3 Origin
    s3_origin = origins.S3BucketOrigin(
      frontend_bucket,
      origin_path=s3_origin_path,
      origin_access_control_id=s3_oac.origin_access_control_id,
    )

    # Create API Gateway Origin (shared by multiple behaviors)
    api_origin = origins.HttpOrigin(
      api_gateway_domain_name,
      origin_path=f"/{api_gateway_stage_name}",
      protocol_policy=cloudfront.OriginProtocolPolicy.HTTPS_ONLY,
    )

    # CloudFront distribution
    distribution = cloudfront.Distribution(
      self, "Distribution",
      default_behavior=cloudfront.BehaviorOptions(
        origin=s3_origin,
        viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
        compress=True,
        allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD,
      ),
      additional_behaviors={
        "/accounts/*": cloudfront.BehaviorOptions(
          origin=api_origin,
          viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
          cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
          origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
          compress=True,
          allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
        ),
        "/api/*": cloudfront.BehaviorOptions(
          origin=api_origin,
          viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
          cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
          origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
          compress=True,
          allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
        ),
      },
      domain_names=[domain_name],
      certificate=certificate,
      minimum_protocol_version=cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,
      enable_ipv6=True,
      http_version=cloudfront.HttpVersion.HTTP2,
      price_class=cloudfront.PriceClass.PRICE_CLASS_ALL,
      default_root_object="index.html",
      error_responses=[
        cloudfront.ErrorResponse(
          http_status=404,
          response_http_status=200,
          response_page_path="/index.html",
          ttl=Duration.seconds(300),
        ),
      ],
    )

    # Grant CloudFront access to S3 bucket
    frontend_bucket.add_to_resource_policy(
      iam.PolicyStatement(
        actions=["s3:GetObject"],
        resources=[frontend_bucket.arn_for_objects("*")],
        principals=[iam.ServicePrincipal("cloudfront.amazonaws.com")],
        conditions={
          "StringEquals": {
            "AWS:SourceArn": f"arn:aws:cloudfront::{self.account}:distribution/{distribution.distribution_id}"
          }
        },
      )
    )

    # Add tags
    Tags.of(self).add("Environment", environment)
    Tags.of(self).add("Created", "20251026")

    # Outputs
    CfnOutput(
      self, "BucketName",
      value=frontend_bucket.bucket_name,
      description="S3 bucket name for frontend",
    )

    CfnOutput(
      self, "DistributionId",
      value=distribution.distribution_id,
      description="CloudFront distribution ID",
    )

    CfnOutput(
      self, "DistributionDomainName",
      value=distribution.distribution_domain_name,
      description="CloudFront distribution domain name",
    )

    CfnOutput(
      self, "WebsiteURL",
      value=f"https://{domain_name}",
      description="Website URL",
    )

    self.bucket = frontend_bucket
    self.distribution = distribution
