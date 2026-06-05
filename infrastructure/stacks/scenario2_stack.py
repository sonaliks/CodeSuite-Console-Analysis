"""Scenario 2 CDK Stack: Insufficient IAM permissions on pipeline role.

This stack creates a CodePipeline whose service role deliberately lacks
the codecommit:GitPull permission, causing the Source stage to fail.

Root Cause Category: Permission Issue
"""

import aws_cdk as cdk
from aws_cdk import RemovalPolicy, Stack
from aws_cdk import aws_codecommit as codecommit
from aws_cdk import aws_codebuild as codebuild
from aws_cdk import aws_codepipeline as codepipeline
from aws_cdk import aws_codepipeline_actions as cpactions
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from constructs import Construct


class Scenario2Stack(Stack):
    """Stack for Scenario 2: Missing IAM permission causes Source stage failure.

    Resources:
        - CodeCommit repository (with valid code)
        - IAM role for pipeline missing codecommit:GitPull
        - CodeBuild project
        - CodePipeline: Source (CodeCommit) → Build (CodeBuild)
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Import shared artifact bucket
        artifact_bucket = s3.Bucket.from_bucket_arn(
            self,
            "ArtifactBucket",
            cdk.Fn.import_value("CodeSuiteDiag-ArtifactBucketArn"),
        )

        # CodeCommit repository - will be seeded with valid code
        repo = codecommit.Repository(
            self,
            "Scenario2Repo",
            repository_name="codesuite-diag-scenario2-app",
            description="Demo app with valid code (Scenario 2 - Permission Issue)",
        )

        # Custom pipeline role - deliberately missing codecommit:GitPull
        pipeline_role = iam.Role(
            self,
            "Scenario2PipelineRole",
            role_name="codesuite-diag-scenario2-pipeline-role",
            assumed_by=iam.ServicePrincipal("codepipeline.amazonaws.com"),
            description="Pipeline role intentionally missing codecommit:GitPull permission",
        )

        # Grant S3 artifact access (pipeline needs this to function)
        artifact_bucket.grant_read_write(pipeline_role)

        # Grant CodeBuild start permission
        pipeline_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "codebuild:BatchGetBuilds",
                    "codebuild:StartBuild",
                ],
                resources=["*"],
            )
        )

        # Deliberately grant only codecommit:GetBranch and GetCommit
        # but NOT codecommit:GitPull - this causes the failure
        pipeline_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "codecommit:GetBranch",
                    "codecommit:GetCommit",
                    "codecommit:GetRepository",
                    "codecommit:ListBranches",
                    # NOTE: codecommit:GitPull is intentionally MISSING
                ],
                resources=[repo.repository_arn],
            )
        )

        # Explicit DENY on GitPull to override any CDK auto-grants
        pipeline_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.DENY,
                actions=[
                    "codecommit:GitPull",
                    "codecommit:UploadArchive",
                    "codecommit:GetUploadArchiveStatus",
                ],
                resources=[repo.repository_arn],
            )
        )

        # CodeBuild project
        build_project = codebuild.PipelineProject(
            self,
            "Scenario2BuildProject",
            project_name="codesuite-diag-scenario2-build",
            build_spec=codebuild.BuildSpec.from_object({
                "version": "0.2",
                "phases": {
                    "build": {
                        "commands": ["echo Build succeeded"],
                    },
                },
            }),
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
            ),
        )

        # Pipeline artifacts
        source_output = codepipeline.Artifact("SourceOutput")

        # CodePipeline: Source → Build (will fail at Source due to missing GitPull)
        pipeline = codepipeline.Pipeline(
            self,
            "Scenario2Pipeline",
            pipeline_name="codesuite-diag-scenario2-pipeline",
            role=pipeline_role,
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
                            role=pipeline_role,
                        ),
                    ],
                ),
                codepipeline.StageProps(
                    stage_name="Build",
                    actions=[
                        cpactions.CodeBuildAction(
                            action_name="CodeBuild_Build",
                            project=build_project,
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
            description="Scenario 2 CodeCommit repository name",
        )
        cdk.CfnOutput(
            self,
            "PipelineName",
            value=pipeline.pipeline_name,
            description="Scenario 2 pipeline name",
        )
        cdk.CfnOutput(
            self,
            "PipelineRoleArn",
            value=pipeline_role.role_arn,
            description="Scenario 2 pipeline role ARN (missing codecommit:GitPull)",
        )
