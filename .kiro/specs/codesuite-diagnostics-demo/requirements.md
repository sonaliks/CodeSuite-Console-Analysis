# Requirements Document

## Introduction

This document defines the requirements for a demo project that showcases an intelligent "Analysis" section for the AWS CodeSuite console. The demo uses MCP (Model Context Protocol) servers and Amazon Bedrock (Claude 3.5 Sonnet) to automatically diagnose CI/CD pipeline failures and provide actionable recommendations. The demo covers three failure scenarios representing configuration issues, permission issues, and infrastructure issues. The target audience is internal stakeholders for a pitch/demo presentation.

## Glossary

- **Analysis_Panel**: The UI component in the demo console that displays diagnostic results and recommendations to the user
- **Bedrock_Agent**: The Amazon Bedrock Agent using Claude 3.5 Sonnet that orchestrates MCP tool calls to diagnose pipeline failures
- **CodeCommit_MCP_Server**: A custom Python MCP server that exposes CodeCommit repository operations (list files, get file content) as tools
- **CodePipeline_MCP_Server**: A custom Python MCP server that exposes CodePipeline operations (get pipeline state, get execution details, get action execution details) as tools
- **IAM_MCP_Server**: The pre-built AWS Labs MCP server that exposes IAM operations (get role policy, list attached policies) as tools
- **CloudWatch_MCP_Server**: The pre-built AWS Labs MCP server that exposes CloudWatch Logs operations (get log events, filter log events) as tools
- **Demo_UI**: A web-based interface mimicking the AWS CodeSuite console with an integrated Analysis panel
- **Seeded_Failure**: A pre-configured AWS resource setup designed to produce a predictable pipeline failure for demonstration purposes
- **LZA**: Landing Zone Accelerator, an AWS solution that deploys organizational infrastructure via CodePipeline
- **OU**: Organizational Unit within AWS Organizations
- **MCP_SDK**: The Model Context Protocol SDK used to build custom MCP servers in Python
- **Orchestrator**: The Bedrock Agent that receives a failure event, invokes MCP tools, reasons about results, and produces a diagnosis

## Requirements

### Requirement 1: CodeCommit MCP Server

**User Story:** As a demo presenter, I want a custom MCP server that exposes CodeCommit repository operations, so that the Bedrock Agent can inspect repository contents during diagnosis.

#### Acceptance Criteria

1. THE CodeCommit_MCP_Server SHALL expose a `list_files` tool that returns the file listing at the root of a specified CodeCommit repository and branch
2. THE CodeCommit_MCP_Server SHALL expose a `get_file_content` tool that returns the content of a specified file path from a CodeCommit repository and branch
3. THE CodeCommit_MCP_Server SHALL expose a `get_repository_metadata` tool that returns repository name, default branch, and clone URLs for a specified repository
4. WHEN the CodeCommit_MCP_Server receives a request for a non-existent repository, THE CodeCommit_MCP_Server SHALL return a descriptive error indicating the repository was not found
5. WHEN the CodeCommit_MCP_Server receives a request for a non-existent file path, THE CodeCommit_MCP_Server SHALL return a descriptive error indicating the file was not found
6. THE CodeCommit_MCP_Server SHALL use Python with the MCP SDK and boto3 for AWS API calls

### Requirement 2: CodePipeline MCP Server

**User Story:** As a demo presenter, I want a custom MCP server that exposes CodePipeline operations, so that the Bedrock Agent can retrieve pipeline execution details during diagnosis.

#### Acceptance Criteria

1. THE CodePipeline_MCP_Server SHALL expose a `get_pipeline_state` tool that returns the current state of a specified pipeline including stage and action statuses
2. THE CodePipeline_MCP_Server SHALL expose a `get_pipeline_execution` tool that returns execution details including status, start time, and trigger information for a specified execution ID
3. THE CodePipeline_MCP_Server SHALL expose a `get_action_execution_details` tool that returns detailed error messages and output for a specified failed action within a pipeline execution
4. THE CodePipeline_MCP_Server SHALL expose a `list_pipeline_executions` tool that returns recent executions for a specified pipeline with their statuses
5. WHEN the CodePipeline_MCP_Server receives a request for a non-existent pipeline, THE CodePipeline_MCP_Server SHALL return a descriptive error indicating the pipeline was not found
6. THE CodePipeline_MCP_Server SHALL use Python with the MCP SDK and boto3 for AWS API calls

### Requirement 3: Bedrock Agent Orchestration

**User Story:** As a demo presenter, I want a Bedrock Agent that orchestrates MCP tool calls to diagnose pipeline failures, so that the demo shows intelligent root cause analysis.

#### Acceptance Criteria

1. WHEN a pipeline failure is reported, THE Bedrock_Agent SHALL invoke the CodePipeline_MCP_Server to retrieve the failed execution details
2. WHEN the Bedrock_Agent identifies a deployment failure, THE Bedrock_Agent SHALL invoke the CodeCommit_MCP_Server to inspect the repository contents for missing or misconfigured files
3. WHEN the Bedrock_Agent identifies a permission-related failure, THE Bedrock_Agent SHALL invoke the IAM_MCP_Server to inspect the pipeline service role policies
4. WHEN the Bedrock_Agent identifies a build or execution failure with log output, THE Bedrock_Agent SHALL invoke the CloudWatch_MCP_Server to retrieve relevant log entries
5. THE Bedrock_Agent SHALL produce a structured diagnosis containing: root cause category, root cause description, affected resource, and recommended fix
6. THE Bedrock_Agent SHALL use Claude 3.5 Sonnet as the foundation model

### Requirement 4: Scenario 1 - Missing appspec.yml Detection

**User Story:** As a demo viewer, I want to see the agent diagnose a missing appspec.yml file, so that I understand how the system handles configuration issues.

#### Acceptance Criteria

1. THE Seeded_Failure for Scenario 1 SHALL consist of a CodePipeline with a CodeDeploy action that fails because appspec.yml is absent from the CodeCommit repository root
2. WHEN the Bedrock_Agent diagnoses Scenario 1, THE Bedrock_Agent SHALL identify the root cause as a missing appspec.yml file in the repository root
3. WHEN the Bedrock_Agent diagnoses Scenario 1, THE Bedrock_Agent SHALL recommend the exact file content and location to add to resolve the failure
4. WHEN the Bedrock_Agent diagnoses Scenario 1, THE Bedrock_Agent SHALL classify the root cause category as "Configuration Issue"

### Requirement 5: Scenario 2 - Insufficient IAM Permissions Detection

**User Story:** As a demo viewer, I want to see the agent diagnose a missing IAM permission, so that I understand how the system handles permission issues.

#### Acceptance Criteria

1. THE Seeded_Failure for Scenario 2 SHALL consist of a CodePipeline whose service role lacks the `codecommit:GitPull` permission, causing the Source stage to fail
2. WHEN the Bedrock_Agent diagnoses Scenario 2, THE Bedrock_Agent SHALL identify the specific IAM role attached to the pipeline
3. WHEN the Bedrock_Agent diagnoses Scenario 2, THE Bedrock_Agent SHALL identify `codecommit:GitPull` as the missing permission
4. WHEN the Bedrock_Agent diagnoses Scenario 2, THE Bedrock_Agent SHALL recommend the IAM policy statement to add to the role to resolve the failure
5. WHEN the Bedrock_Agent diagnoses Scenario 2, THE Bedrock_Agent SHALL classify the root cause category as "Permission Issue"

### Requirement 6: Scenario 3 - LZA Config OU Mismatch Detection

**User Story:** As a demo viewer, I want to see the agent diagnose an invalid OU reference in LZA config, so that I understand how the system handles infrastructure issues.

#### Acceptance Criteria

1. THE Seeded_Failure for Scenario 3 SHALL consist of an LZA pipeline that fails because accounts-config.yaml references an organizational unit name that does not exist in the AWS Organization
2. WHEN the Bedrock_Agent diagnoses Scenario 3, THE Bedrock_Agent SHALL retrieve the accounts-config.yaml file from the CodeCommit repository using the CodeCommit_MCP_Server
3. WHEN the Bedrock_Agent diagnoses Scenario 3, THE Bedrock_Agent SHALL identify the specific OU name in accounts-config.yaml that does not match any OU in the AWS Organization
4. WHEN the Bedrock_Agent diagnoses Scenario 3, THE Bedrock_Agent SHALL list the valid OU names from the actual organization structure as part of the recommendation
5. WHEN the Bedrock_Agent diagnoses Scenario 3, THE Bedrock_Agent SHALL classify the root cause category as "Infrastructure Issue"

### Requirement 7: Demo UI

**User Story:** As a demo presenter, I want a web-based UI that mimics the CodeSuite console with an Analysis panel, so that stakeholders can visualize the end-user experience.

#### Acceptance Criteria

1. THE Demo_UI SHALL display a pipeline list view showing pipeline names and their current execution statuses
2. THE Demo_UI SHALL display a pipeline detail view showing stages, actions, and execution history for a selected pipeline
3. WHEN a user selects a failed pipeline execution, THE Demo_UI SHALL display an Analysis panel with the diagnostic results from the Bedrock_Agent
4. THE Analysis_Panel SHALL display the root cause category, root cause description, affected resource, and recommended fix in a structured format
5. THE Analysis_Panel SHALL display a loading state while the Bedrock_Agent is processing the diagnosis
6. THE Demo_UI SHALL visually resemble the AWS CodeSuite console styling (dark navigation, service-specific color accents, AWS typography)

### Requirement 8: Seeded Failure Infrastructure

**User Story:** As a demo presenter, I want pre-configured AWS resources that produce predictable failures, so that the demo runs reliably during presentations.

#### Acceptance Criteria

1. THE Seeded_Failure infrastructure SHALL be deployable via Infrastructure as Code (CloudFormation or CDK)
2. THE Seeded_Failure infrastructure SHALL include a CodeCommit repository without appspec.yml for Scenario 1
3. THE Seeded_Failure infrastructure SHALL include a CodePipeline with a service role missing `codecommit:GitPull` for Scenario 2
4. THE Seeded_Failure infrastructure SHALL include a CodeCommit repository containing an accounts-config.yaml with an invalid OU name for Scenario 3
5. WHEN the Seeded_Failure infrastructure is deployed, THE pipelines SHALL fail predictably within one execution cycle
6. THE Seeded_Failure infrastructure SHALL include a teardown mechanism to remove all created resources

### Requirement 9: MCP Server Integration with Pre-built AWS Labs Servers

**User Story:** As a demo presenter, I want the system to leverage pre-built AWS Labs MCP servers for IAM and CloudWatch, so that the demo demonstrates ecosystem reuse.

#### Acceptance Criteria

1. THE Bedrock_Agent SHALL integrate with the AWS Labs IAM MCP Server from github.com/awslabs/mcp for IAM policy inspection
2. THE Bedrock_Agent SHALL integrate with the AWS Labs CloudWatch MCP Server from github.com/awslabs/mcp for log retrieval
3. WHEN the IAM_MCP_Server is invoked, THE IAM_MCP_Server SHALL return policy documents and attached policies for a specified IAM role
4. WHEN the CloudWatch_MCP_Server is invoked, THE CloudWatch_MCP_Server SHALL return log events from a specified log group and time range
