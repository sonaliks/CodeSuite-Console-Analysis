# Implementation Plan: CodeSuite Diagnostics Demo

## Overview

This implementation plan covers building an intelligent CI/CD diagnostics demo using MCP servers and Amazon Bedrock. The system includes custom MCP servers for CodeCommit and CodePipeline, seeded AWS infrastructure with three failure scenarios, a Bedrock Agent orchestrator for root cause analysis, and a React-based demo UI mimicking the AWS console. Tasks are organized in phases from project setup through integration testing.

## Tasks

### Phase 1: Project Setup and Infrastructure

- [x] 1.1 Initialize project repository structure with top-level directories: `mcp-servers/`, `backend/`, `demo-ui/`, `infrastructure/`
- [x] 1.2 Create shared Python requirements and configuration files (pyproject.toml or requirements.txt for common dependencies: mcp, boto3, pydantic)
- [x] 1.3 Set up AWS CDK project in `infrastructure/` with app.py, cdk.json, and shared stack for common resources (S3 artifact bucket)

### Phase 2: Custom MCP Servers

- [x] 2.1 Implement CodeCommit MCP Server entry point (`mcp-servers/codecommit/server.py`) with MCP SDK server initialization and tool registration
  - _Requirements: 1.1, 1.2, 1.3, 1.6_
- [x] 2.2 Implement CodeCommit MCP Server handlers (`mcp-servers/codecommit/handlers.py`) with `list_files`, `get_file_content`, and `get_repository_metadata` using boto3
  - _Requirements: 1.1, 1.2, 1.3_
- [x] 2.3 Add error handling to CodeCommit MCP Server for non-existent repositories and file paths (return descriptive MCP error responses)
  - _Requirements: 1.4, 1.5_
- [x] 2.4 Implement CodePipeline MCP Server entry point (`mcp-servers/codepipeline/server.py`) with MCP SDK server initialization and tool registration
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.6_
- [x] 2.5 Implement CodePipeline MCP Server handlers (`mcp-servers/codepipeline/handlers.py`) with `get_pipeline_state`, `get_pipeline_execution`, `get_action_execution_details`, and `list_pipeline_executions` using boto3
  - _Requirements: 2.1, 2.2, 2.3, 2.4_
- [x] 2.6 Add error handling to CodePipeline MCP Server for non-existent pipelines (return descriptive MCP error responses)
  - _Requirements: 2.5_
- [ ]* 2.7 Write unit tests for CodeCommit MCP Server handlers using mocked boto3 responses
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_
- [ ]* 2.8 Write unit tests for CodePipeline MCP Server handlers using mocked boto3 responses
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

### Phase 3: Seeded Failure Infrastructure

- [ ] 3.1 Implement Scenario 1 CDK stack: CodeCommit repo (no appspec.yml), CodeDeploy app/deployment group, CodePipeline (Source → Deploy)
  - _Requirements: 4.1, 8.1, 8.2_
- [ ] 3.2 Create seed data for Scenario 1: sample application files (index.html, scripts/) without appspec.yml
  - _Requirements: 4.1, 8.2_
- [ ] 3.3 Implement Scenario 2 CDK stack: CodeCommit repo (valid code), IAM role missing `codecommit:GitPull`, CodePipeline (Source → Build)
  - _Requirements: 5.1, 8.1, 8.3_
- [ ] 3.4 Create seed data for Scenario 2: valid application files with appspec.yml
  - _Requirements: 5.1, 8.3_
- [ ] 3.5 Implement Scenario 3 CDK stack: CodeCommit repo with accounts-config.yaml (invalid OU name), CodeBuild validation project, CodePipeline (Source → Build)
  - _Requirements: 6.1, 8.1, 8.4_
- [ ] 3.6 Create seed data for Scenario 3: accounts-config.yaml referencing non-existent OU "Workloads-Production" (actual OU is "Workloads-Prod")
  - _Requirements: 6.1, 6.3, 8.4_
- [ ] 3.7 Create CodeBuild buildspec for Scenario 3 that validates OU names against AWS Organizations and fails with descriptive error
  - _Requirements: 6.1, 8.5_

### Phase 4: Bedrock Agent Backend

- [ ] 4.1 Set up FastAPI application (`backend/app.py`) with CORS, health check, and API route structure
  - _Requirements: 3.1, 7.1_
- [ ] 4.2 Implement MCP client module (`backend/mcp_client.py`) that spawns MCP server subprocesses and communicates via stdio JSON-RPC
  - _Requirements: 3.1, 9.1, 9.2_
- [ ] 4.3 Implement Pydantic models (`backend/models.py`) for diagnosis output (root_cause_category, root_cause_description, affected_resource, recommended_fix, evidence)
  - _Requirements: 3.5_
- [ ] 4.4 Implement agent orchestration (`backend/agent.py`) using Bedrock Converse API with tool_use, system prompt, and MCP tool schema registration
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6_
- [ ] 4.5 Create system prompt (`backend/prompts.py`) that instructs the agent on diagnostic methodology: retrieve state → read errors → investigate → diagnose
  - _Requirements: 3.1, 3.2, 3.3, 3.4_
- [ ] 4.6 Implement API endpoints: GET `/api/pipelines`, GET `/api/pipelines/{name}`, GET `/api/pipelines/{name}/executions/{id}`, POST `/api/pipelines/{name}/executions/{id}/diagnose`
  - _Requirements: 7.1, 7.2, 7.3_
- [ ] 4.7 Integrate AWS Labs IAM MCP Server and CloudWatch MCP Server as additional tool providers in the agent configuration
  - _Requirements: 9.1, 9.2, 9.3, 9.4_
- [ ]* 4.8 Test agent orchestration end-to-end against each seeded failure scenario
  - _Requirements: 4.2, 4.3, 4.4, 5.2, 5.3, 5.4, 5.5, 6.2, 6.3, 6.4, 6.5_

### Phase 5: Demo UI

- [ ] 5.1 Initialize React + TypeScript project with Vite, Tailwind CSS, and project structure (`demo-ui/`)
  - _Requirements: 7.6_
- [ ] 5.2 Implement Layout component with AWS console-style navigation (dark sidebar, header with service name)
  - _Requirements: 7.6_
- [ ] 5.3 Implement PipelineList component displaying pipeline names and execution statuses with color-coded indicators
  - _Requirements: 7.1_
- [ ] 5.4 Implement PipelineDetail component with stage visualization (Source → Build/Deploy flow diagram) and execution history
  - _Requirements: 7.2_
- [ ] 5.5 Implement AnalysisPanel component with structured diagnosis display (category badge, description, affected resource, recommended fix with code blocks)
  - _Requirements: 7.3, 7.4_
- [ ] 5.6 Implement API client (`demo-ui/src/api/client.ts`) for backend communication
  - _Requirements: 7.1, 7.2, 7.3_
- [ ] 5.7 Add loading state to AnalysisPanel with animated progress indicators showing MCP tool invocations
  - _Requirements: 7.5_
- [ ] 5.8 Apply AWS console styling: color scheme (#232f3e nav, #ff9900 accents), typography (Amazon Ember font or fallback), spacing patterns
  - _Requirements: 7.6_

### Phase 6: Integration and Demo Polish

- [ ]* 6.1 End-to-end integration test: trigger Scenario 1 diagnosis from UI and verify correct Analysis Panel output
  - _Requirements: 4.2, 4.3, 4.4_
- [ ]* 6.2 End-to-end integration test: trigger Scenario 2 diagnosis from UI and verify correct Analysis Panel output
  - _Requirements: 5.2, 5.3, 5.4, 5.5_
- [ ]* 6.3 End-to-end integration test: trigger Scenario 3 diagnosis from UI and verify correct Analysis Panel output
  - _Requirements: 6.2, 6.3, 6.4, 6.5_
- [ ] 6.4 Create demo run script that starts all services (MCP servers, backend, frontend) with a single command
  - _Requirements: 8.1_
- [ ] 6.5 Write README.md with setup instructions, prerequisites (AWS account, credentials, CDK bootstrap), and demo walkthrough guide
  - _Requirements: 8.1, 8.6_
- [ ] 6.6 Create presentation talking points document mapping each scenario to the 2-pager root cause categories
  - _Requirements: 4.4, 5.5, 6.5_

- [ ] 7. Final checkpoint
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- The design uses Python for MCP servers and backend, and TypeScript/React for the frontend
- AWS CDK (Python) is used for all infrastructure-as-code
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- Pre-built AWS Labs MCP servers (IAM, CloudWatch) are integrated as dependencies rather than built from scratch

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "1.3", "5.1"] },
    { "id": 2, "tasks": ["2.1", "2.4", "3.1", "3.3", "3.5", "5.2"] },
    { "id": 3, "tasks": ["2.2", "2.5", "3.2", "3.4", "3.6", "3.7", "5.3", "5.4", "5.8"] },
    { "id": 4, "tasks": ["2.3", "2.6", "4.1", "4.3", "5.5", "5.6", "5.7"] },
    { "id": 5, "tasks": ["2.7", "2.8", "4.2", "4.5"] },
    { "id": 6, "tasks": ["4.4", "4.7"] },
    { "id": 7, "tasks": ["4.6", "4.8"] },
    { "id": 8, "tasks": ["6.1", "6.2", "6.3", "6.4", "6.5", "6.6"] }
  ]
}
```
