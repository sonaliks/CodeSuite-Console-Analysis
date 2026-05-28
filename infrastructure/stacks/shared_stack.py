"""Shared stack for common resources used across all demo scenarios."""

import aws_cdk as cdk
from aws_cdk import RemovalPolicy, Stack
from aws_cdk import aws_s3 as s3
from constructs import Construct


class SharedStack(Stack):
    """Stack containing shared resources for the CodeSuite Diagnostics Demo.

    Resources:
        - S3 artifact bucket used by CodePipeline across all scenarios
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # S3 bucket for pipeline artifacts shared across all scenarios
        self.artifact_bucket = s3.Bucket(
            self,
            "ArtifactBucket",
            bucket_name=cdk.Fn.sub("codesuite-diag-artifacts-${AWS::AccountId}-${AWS::Region}"),
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
        )

        # Export the bucket ARN for use by scenario stacks
        cdk.CfnOutput(
            self,
            "ArtifactBucketArn",
            value=self.artifact_bucket.bucket_arn,
            description="ARN of the shared artifact bucket",
            export_name="CodeSuiteDiag-ArtifactBucketArn",
        )

        cdk.CfnOutput(
            self,
            "ArtifactBucketName",
            value=self.artifact_bucket.bucket_name,
            description="Name of the shared artifact bucket",
            export_name="CodeSuiteDiag-ArtifactBucketName",
        )
