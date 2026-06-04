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
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from constructs import Construct


class Scenario1Stack(Stack):
    """Stack for Scenario 1: Missing appspec.yml causes CodeDeploy failure.

    Resources:
        - CodeCommit repository (without appspec.yml)
        - EC2 instance with CodeDeploy agent
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

        # VPC for the EC2 instance (use default VPC)
        vpc = ec2.Vpc.from_lookup(self, "DefaultVpc", is_default=True)

        # IAM role for EC2 instance (needs CodeDeploy agent + S3 access)
        instance_role = iam.Role(
            self,
            "Scenario1InstanceRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"),
            ],
        )
        artifact_bucket.grant_read(instance_role)

        # EC2 instance with CodeDeploy agent installed via user data
        user_data = ec2.UserData.for_linux()
        user_data.add_commands(
            "yum update -y",
            "yum install -y ruby wget",
            "wget https://aws-codedeploy-us-east-1.s3.us-east-1.amazonaws.com/latest/install",
            "chmod +x ./install",
            "./install auto",
            "service codedeploy-agent start",
        )

        instance = ec2.Instance(
            self,
            "Scenario1Instance",
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MICRO),
            machine_image=ec2.AmazonLinuxImage(
                generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2,
            ),
            vpc=vpc,
            role=instance_role,
            user_data=user_data,
        )

        # Tag the instance for CodeDeploy targeting
        cdk.Tags.of(instance).add("CodeDeploy", "Scenario1")

        # CodeDeploy application
        application = codedeploy.ServerApplication(
            self,
            "Scenario1App",
            application_name="codesuite-diag-scenario1-app",
        )

        # CodeDeploy deployment group targeting tagged instances
        deployment_group = codedeploy.ServerDeploymentGroup(
            self,
            "Scenario1DeploymentGroup",
            application=application,
            deployment_group_name="codesuite-diag-scenario1-dg",
            install_agent=False,
            ec2_instance_tags=codedeploy.InstanceTagSet(
                {"CodeDeploy": ["Scenario1"]}
            ),
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
