# Implementation Tasks

## Phase 1: Project Setup and Infrastructure

- [ ] 1.1 Initialize project repository structure with top-level directories: `mcp-servers/`, `backend/`, `demo-ui/`, `infrastructure/`
- [ ] 1.2 Create shared Python requirements and configuration files (pyproject.toml or requirements.txt for common dependencies: mcp, boto3, pydantic)
- [ ] 1.3 Set up AWS CDK project in `infrastructure/` with app.py, cdk.json, and shared stack for common resources (S3 artifact bucket)

## Phase 2: Custom MCP Servers

- [ ] 2.1 Implement CodeCommit MCP Server entry point (`mcp-servers/codecommit/server.py`) with MCP SDK server initialization and tool registration
- [ ] 2.2 Implement CodeCommit MCP Server handlers (`mcp-servers/codecommit/handlers.py`) with `list_files`, `get_file_content`, and `get_repository_metadata` using boto3
- [ ] 2.3 Add error handling to CodeCommit MCP Server for non-existent repositories and file paths (return descriptive MCP error responses)
- [ ] 2.4 Implement CodePipeline MCP Server entry point (`mcp-servers/codepipeline/server.py`) with MCP SDK server initialization and tool registration
- [ ] 2.5 Implement CodePipeline MCP Server handlers (`mcp-servers/codepipeline/handlers.py`) with `get_pipeline_state`, `get_pipeline_execution`, `get_action_execution_details`, and `list_pipeline_executions` using boto3
- [ ] 2.6 Add error handling to CodePipeline MCP Server for non-existent pipelines (return descriptive MCP error responses)
- [ ] 2.7 Write unit tests for CodeCommit MCP Server handlers using mocked boto3 responses
- [ ] 2.8 Write unit tests for CodePipeline MCP Server handlers using mocked boto3 responses

## Phase 3: Seeded Failure Infrastructure

- [ ] 3.1 Implement Scenario 1 CDK stack: CodeCommit repo (no appspec.yml), CodeDeploy app/deployment group, CodePipeline (Source → Deploy)
- [ ] 3.2 Create seed data for Scenario 1: sample application files (index.html, scripts/) without appspec.yml
- [ ] 3.3 Implement Scenario 2 CDK stack: CodeCommit repo (valid code), IAM role missing `codecommit:GitPull`, CodePipeline (Source → Build)
- [ ] 3.4 Create seed data for Scenario 2: valid application files with appspec.yml
- [ ] 3.5 Implement Scenario 3 CDK stack: CodeCommit repo with accounts-config.yaml (invalid OU name), CodeBuild validation project, CodePipeline (Source → Build)
- [ ] 3.6 Create seed data for Scenario 3: accounts-config.yaml referencing non-existent OU "Workloads-Production" (actual OU is "Workloads-Prod")
- [ ] 3.7 Create CodeBuild buildspec for Scenario 3 that validates OU names against AWS Organizations and fails with descriptive error

## Phase 4: Bedrock Agent Backend

- [ ] 4.1 Set up FastAPI application (`backend/app.py`) with CORS, health check, and API route structure
- [ ] 4.2 Implement MCP client module (`backend/mcp_client.py`) that spawns MCP server subprocesses and communicates via stdio JSON-RPC
- [ ] 4.3 Implement Pydantic models (`backend/models.py`) for diagnosis output (root_cause_category, root_cause_description, affected_resource, recommended_fix, evidence)
- [ ] 4.4 Implement agent orchestration (`backend/agent.py`) using Bedrock Converse API with tool_use, system prompt, and MCP tool schema registration
- [ ] 4.5 Create system prompt (`backend/prompts.py`) that instructs the agent on diagnostic methodology: retrieve state → read errors → investigate → diagnose
- [ ] 4.6 Implement API endpoints: GET `/api/pipelines`, GET `/api/pipelines/{name}`, GET `/api/pipelines/{name}/executions/{id}`, POST `/api/pipelines/{name}/executions/{id}/diagnose`
- [ ] 4.7 Integrate AWS Labs IAM MCP Server and CloudWatch MCP Server as additional tool providers in the agent configuration
- [ ] 4.8 Test agent orchestration end-to-end against each seeded failure scenario

## Phase 5: Demo UI

- [ ] 5.1 Initialize React + TypeScript project with Vite, Tailwind CSS, and project structure (`demo-ui/`)
- [ ] 5.2 Implement Layout component with AWS console-style navigation (dark sidebar, header with service name)
- [ ] 5.3 Implement PipelineList component displaying pipeline names and execution statuses with color-coded indicators
- [ ] 5.4 Implement PipelineDetail component with stage visualization (Source → Build/Deploy flow diagram) and execution history
- [ ] 5.5 Implement AnalysisPanel component with structured diagnosis display (category badge, description, affected resource, recommended fix with code blocks)
- [ ] 5.6 Implement API client (`demo-ui/src/api/client.ts`) for backend communication
- [ ] 5.7 Add loading state to AnalysisPanel with animated progress indicators showing MCP tool invocations
- [ ] 5.8 Apply AWS console styling: color scheme (#232f3e nav, #ff9900 accents), typography (Amazon Ember font or fallback), spacing patterns

## Phase 6: Integration and Demo Polish

- [ ] 6.1 End-to-end integration test: trigger Scenario 1 diagnosis from UI and verify correct Analysis Panel output
- [ ] 6.2 End-to-end integration test: trigger Scenario 2 diagnosis from UI and verify correct Analysis Panel output
- [ ] 6.3 End-to-end integration test: trigger Scenario 3 diagnosis from UI and verify correct Analysis Panel output
- [ ] 6.4 Create demo run script that starts all services (MCP servers, backend, frontend) with a single command
- [ ] 6.5 Write README.md with setup instructions, prerequisites (AWS account, credentials, CDK bootstrap), and demo walkthrough guide
- [ ] 6.6 Create presentation talking points document mapping each scenario to the 2-pager root cause categories
