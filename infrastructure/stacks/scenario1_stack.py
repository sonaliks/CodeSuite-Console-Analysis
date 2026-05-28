"""Scenario 1 CDK Stack: Missing appspec.yml in CodeCommit repository.

This stack creates a CodePipeline that fails because the CodeCommit repository
does not contain an appspec.yml file, causing the CodeDeploy action to fail.

Root Cause Category: Configuration Issue
"""

import aws_cdk as cdk
from aws_cdk import RemovalPolicy, Stack
from aws_cdk import aws_codecommit as codecommit
from aws_cdk import aws_codedeploy as codedeploy
from aws_cdk import aws_codepipeline as codepipeline
from aws_cdk import aws_codepipeline_actions as cpactions
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from constructs import Construct


class Scenario1Stack(Stack):
    """Stack for Scenario 1: Missing appspec.yml causes CodeDeploy failure.

    Resources:
        - CodeCommit repository (without appspec.yml)
        - CodeDeploy application and deployment group
        - CodePipeline: Source (CodeCommit) → Deploy (CodeDeploy)
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Import shared artifact bucket
        artifact_bucket = s3.Bucket.from_bucket_arn(
            self,
            "ArtifactBucket",
            cdk.Fn.import_value("CodeSuiteDiag-ArtifactBucketArn"),
        )

        # CodeCommit repository - will be seeded WITHOUT appspec.yml
        repo = codecommit.Repository(
            self,
            "Scenario1Repo",
            repository_name="codesuite-diag-scenario1-app",
            description="Demo app missing appspec.yml (Scenario 1 - Configuration Issue)",
        )

        # CodeDeploy application
        application = codedeploy.ServerApplication(
            self,
            "Scenario1App",
            application_name="codesuite-diag-scenario1-app",
        )

        # CodeDeploy deployment group (targets don't need to exist for demo)
        deployment_group = codedeploy.ServerDeploymentGroup(
            self,
            "Scenario1DeploymentGroup",
            application=application,
            deployment_group_name="codesuite-diag-scenario1-dg",
            install_agent=False,
            # No EC2 instances - deployment will fail at appspec validation
        )

        # Pipeline artifacts
        source_output = codepipeline.Artifact("SourceOutput")

        # CodePipeline: Source → Deploy
        pipeline = codepipeline.Pipeline(
            self,
            "Scenario1Pipeline",
            pipeline_name="codesuite-diag-scenario1-pipeline",
            artifact_bucket=artifact_bucket,
            stages=[
                codepipeline.StageProps(
                    stage_name="Source",
                    actions=[
                        cpactions.CodeCommitSourceAction(
                            action_name="CodeCommit_Source",
                            repository=repo,
                            branch="main",
                            output=source_output,
                        ),
                    ],
                ),
                codepipeline.StageProps(
                    stage_name="Deploy",
                    actions=[
                        cpactions.CodeDeployServerDeployAction(
                            action_name="CodeDeploy_Deploy",
                            deployment_group=deployment_group,
                            input=source_output,
                        ),
                    ],
                ),
            ],
        )

        # Outputs
        cdk.CfnOutput(
            self,
            "RepositoryName",
            value=repo.repository_name,
            description="Scenario 1 CodeCommit repository name",
        )
        cdk.CfnOutput(
            self,
            "PipelineName",
            value=pipeline.pipeline_name,
            description="Scenario 1 pipeline name",
        )
