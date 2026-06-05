"""Scenario 3 CDK Stack: ECS Deploy failure.

This stack creates a CodePipeline that mimics a container image deployment workflow:
ECR Source → CodeBuild (format imagedefinitions.json) → ECS Deploy.
The ECS Deploy stage fails because the ECS service cannot stabilize
(container fails health checks / task definition references non-existent image tag).

Root Cause Category: Infrastructure Issue
"""

import aws_cdk as cdk
from aws_cdk import RemovalPolicy, Stack, Duration
from aws_cdk import aws_codebuild as codebuild
from aws_cdk import aws_codepipeline as codepipeline
from aws_cdk import aws_codepipeline_actions as cpactions
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_logs as logs
from constructs import Construct


class Scenario3Stack(Stack):
    """Stack for Scenario 3: ECS Deploy failure due to container health check failure.

    Resources:
        - ECR repository with a dummy image
        - ECS Cluster (Fargate)
        - ECS Service with a task definition pointing to a non-working image
        - CodeBuild project to format imagedefinitions.json
        - CodePipeline: Source (ECR) → Build (CodeBuild) → Deploy (ECS)

    The ECS deployment fails because the container cannot pass health checks,
    causing the deployment to time out and the pipeline Deploy stage to fail.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Import shared artifact bucket
        artifact_bucket = s3.Bucket.from_bucket_arn(
            self,
            "ArtifactBucket",
            cdk.Fn.import_value("CodeSuiteDiag-ArtifactBucketArn"),
        )

        # ECR Repository
        ecr_repo = ecr.Repository(
            self,
            "Scenario3EcrRepo",
            repository_name="codesuite-diag-scenario3-api",
            removal_policy=RemovalPolicy.DESTROY,
            empty_on_delete=True,
        )

        # VPC for ECS
        vpc = ec2.Vpc(
            self,
            "Scenario3Vpc",
            max_azs=2,
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
            ],
        )

        # ECS Cluster
        cluster = ecs.Cluster(
            self,
            "Scenario3Cluster",
            cluster_name="codesuite-diag-scenario3-cluster",
            vpc=vpc,
        )

        # Task Definition - references a non-existent image tag to cause failure
        task_def = ecs.FargateTaskDefinition(
            self,
            "Scenario3TaskDef",
            memory_limit_mib=512,
            cpu=256,
        )

        # Container using a deliberately broken image URI.
        # The task def references tag "nonexistent-v99" which doesn't exist in ECR.
        # When the pipeline's ECS deploy action updates the service, ECS will try to
        # pull this image and fail, causing the deployment to time out.
        container = task_def.add_container(
            "api",
            image=ecs.ContainerImage.from_ecr_repository(ecr_repo, tag="nonexistent-v99"),
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="scenario3",
                log_retention=logs.RetentionDays.ONE_DAY,
            ),
            port_mappings=[ecs.PortMapping(container_port=8080)],
            health_check=ecs.HealthCheck(
                command=["CMD-SHELL", "curl -f http://localhost:8080/health || exit 1"],
                interval=Duration.seconds(10),
                timeout=Duration.seconds(5),
                retries=2,
                start_period=Duration.seconds(10),
            ),
        )

        # ECS Service (Fargate) - start with 0 desired count so CDK deploys successfully.
        # The pipeline's ECS deploy action will fail when it tries to update the service
        # because the image tag referenced in imagedefinitions.json won't be pullable.
        service = ecs.FargateService(
            self,
            "Scenario3Service",
            cluster=cluster,
            task_definition=task_def,
            service_name="codesuite-diag-scenario3-api",
            desired_count=1,
            assign_public_ip=True,
            circuit_breaker=ecs.DeploymentCircuitBreaker(rollback=True),
        )

        # CodeBuild project to format imagedefinitions.json
        # DELIBERATELY references a non-existent image tag "v2.0.0-rc1" to cause
        # ECS deployment failure (image pull error)
        build_project = codebuild.PipelineProject(
            self,
            "Scenario3BuildProject",
            project_name="codesuite-diag-scenario3-format-image",
            build_spec=codebuild.BuildSpec.from_object({
                "version": "0.2",
                "phases": {
                    "build": {
                        "commands": [
                            'echo \'[{"name":"api","imageUri":"\'$REPOSITORY_URI\':\'$IMAGE_TAG\'"}]\' > imagedefinitions.json',
                            "cat imagedefinitions.json",
                        ],
                    },
                },
                "artifacts": {
                    "files": ["imagedefinitions.json"],
                },
            }),
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
            ),
            environment_variables={
                "REPOSITORY_URI": codebuild.BuildEnvironmentVariable(
                    value=ecr_repo.repository_uri,
                ),
                "IMAGE_TAG": codebuild.BuildEnvironmentVariable(
                    value="v2.0.0-rc1",  # This tag does NOT exist - causes ECS image pull failure
                ),
            },
        )

        # Grant ECR read to CodeBuild
        ecr_repo.grant_pull(build_project)

        # Pipeline artifacts
        source_output = codepipeline.Artifact("SourceOutput")
        build_output = codepipeline.Artifact("BuildOutput")

        # CodePipeline: Source (ECR) → Build (format image defs) → Deploy (ECS)
        pipeline = codepipeline.Pipeline(
            self,
            "Scenario3Pipeline",
            pipeline_name="codesuite-diag-scenario3-pipeline",
            artifact_bucket=artifact_bucket,
            pipeline_type=codepipeline.PipelineType.V2,
            stages=[
                codepipeline.StageProps(
                    stage_name="Source",
                    actions=[
                        cpactions.EcrSourceAction(
                            action_name="EcrSource",
                            repository=ecr_repo,
                            image_tag="latest",
                            output=source_output,
                        ),
                    ],
                ),
                codepipeline.StageProps(
                    stage_name="Build",
                    actions=[
                        cpactions.CodeBuildAction(
                            action_name="FormatImageDefinitions",
                            project=build_project,
                            input=source_output,
                            outputs=[build_output],
                        ),
                    ],
                ),
                codepipeline.StageProps(
                    stage_name="Deploy",
                    actions=[
                        cpactions.EcsDeployAction(
                            action_name="EcsDeploy",
                            service=service,
                            input=build_output,
                            deployment_timeout=Duration.minutes(10),
                        ),
                    ],
                ),
            ],
        )

        # Outputs
        cdk.CfnOutput(
            self,
            "PipelineName",
            value=pipeline.pipeline_name,
            description="Scenario 3 pipeline name",
        )
        cdk.CfnOutput(
            self,
            "EcrRepoName",
            value=ecr_repo.repository_name,
            description="Scenario 3 ECR repository name",
        )
        cdk.CfnOutput(
            self,
            "ClusterName",
            value=cluster.cluster_name,
            description="Scenario 3 ECS cluster name",
        )
        cdk.CfnOutput(
            self,
            "ServiceName",
            value=service.service_name,
            description="Scenario 3 ECS service name",
        )
