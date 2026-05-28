"""Scenario 3 CDK Stack: LZA config references non-existent OU name.

This stack creates a CodePipeline that fails because the accounts-config.yaml
in the CodeCommit repository references an organizational unit name that does
not exist in the AWS Organization.

Root Cause Category: Infrastructure Issue
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


class Scenario3Stack(Stack):
    """Stack for Scenario 3: LZA config OU mismatch causes validation failure.

    Resources:
        - CodeCommit repository (with accounts-config.yaml referencing invalid OU)
        - CodeBuild project that validates OU names against AWS Organizations
        - CodePipeline: Source (CodeCommit) → Build (CodeBuild validation)
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Import shared artifact bucket
        artifact_bucket = s3.Bucket.from_bucket_arn(
            self,
            "ArtifactBucket",
            cdk.Fn.import_value("CodeSuiteDiag-ArtifactBucketArn"),
        )

        # CodeCommit repository - will be seeded with invalid OU in config
        repo = codecommit.Repository(
            self,
            "Scenario3Repo",
            repository_name="codesuite-diag-scenario3-lza-config",
            description="LZA config with invalid OU name (Scenario 3 - Infrastructure Issue)",
        )

        # CodeBuild role with Organizations read access for validation
        build_role = iam.Role(
            self,
            "Scenario3BuildRole",
            assumed_by=iam.ServicePrincipal("codebuild.amazonaws.com"),
            description="CodeBuild role for LZA config validation",
        )

        build_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "organizations:ListOrganizationalUnitsForParent",
                    "organizations:ListRoots",
                    "organizations:DescribeOrganizationalUnit",
                ],
                resources=["*"],
            )
        )

        build_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                resources=["*"],
            )
        )

        artifact_bucket.grant_read_write(build_role)

        # CodeBuild project that validates OU names
        build_project = codebuild.PipelineProject(
            self,
            "Scenario3ValidationProject",
            project_name="codesuite-diag-scenario3-lza-validate",
            role=build_role,
            build_spec=codebuild.BuildSpec.from_source_filename("buildspec.yml"),
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
            ),
        )

        # Pipeline artifacts
        source_output = codepipeline.Artifact("SourceOutput")

        # CodePipeline: Source → Build (validation fails due to invalid OU)
        pipeline = codepipeline.Pipeline(
            self,
            "Scenario3Pipeline",
            pipeline_name="codesuite-diag-scenario3-pipeline",
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
                    stage_name="Build",
                    actions=[
                        cpactions.CodeBuildAction(
                            action_name="LZA_Validate",
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
            description="Scenario 3 CodeCommit repository name",
        )
        cdk.CfnOutput(
            self,
            "PipelineName",
            value=pipeline.pipeline_name,
            description="Scenario 3 pipeline name",
        )
