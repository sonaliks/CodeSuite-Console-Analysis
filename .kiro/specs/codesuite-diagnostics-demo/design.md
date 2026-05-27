# Design Document

## Introduction

This document describes the technical design for the CodeSuite Diagnostics Demo — a system that uses MCP servers and Amazon Bedrock to automatically diagnose CI/CD pipeline failures. The architecture consists of custom and pre-built MCP servers, a Bedrock Agent orchestrator, seeded AWS infrastructure for demo scenarios, and a web-based demo UI.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Demo UI (React)                             │
│  ┌──────────────┐  ┌──────────────────┐  ┌──────────────────────┐  │
│  │ Pipeline List │  │ Pipeline Detail  │  │   Analysis Panel     │  │
│  └──────────────┘  └──────────────────┘  └──────────────────────┘  │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │ REST API
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Backend API (Python FastAPI)                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │              Amazon Bedrock Agent (Claude 3.5 Sonnet)           │ │
│  └────────────────────┬──────────────┬────────────────────────────┘ │
└───────────────────────┼──────────────┼──────────────────────────────┘
                        │              │
          ┌─────────────┼──────────────┼─────────────────┐
          ▼             ▼              ▼                  ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  CodeCommit  │ │ CodePipeline │ │   IAM MCP    │ │ CloudWatch   │
│  MCP Server  │ │  MCP Server  │ │   Server     │ │  MCP Server  │
│  (Custom)    │ │  (Custom)    │ │ (AWS Labs)   │ │ (AWS Labs)   │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                 │                │                 │
       ▼                 ▼                ▼                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         AWS Account                                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐  │
│  │ CodeCommit  │ │ CodePipeline│ │    IAM      │ │ CloudWatch  │  │
│  │ Repos       │ │ Pipelines   │ │   Roles     │ │    Logs     │  │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Design

### 1. CodeCommit MCP Server

**Technology:** Python 3.11+, MCP SDK (`mcp` package), boto3

**File Structure:**
```
mcp-servers/codecommit/
├── server.py          # MCP server entry point and tool definitions
├── handlers.py        # Tool handler implementations
├── requirements.txt   # Python dependencies
└── README.md
```

**Tools Exposed:**

| Tool Name | Parameters | Returns |
|-----------|-----------|---------|
| `list_files` | `repository_name`, `branch` (optional, default: main) | Array of file paths at repository root |
| `get_file_content` | `repository_name`, `file_path`, `branch` (optional) | File content as string |
| `get_repository_metadata` | `repository_name` | Repository name, default branch, clone URLs |

**Implementation Details:**
- Uses `boto3.client('codecommit')` for AWS API calls
- `list_files` calls `get_folder()` API with `/` as folder path
- `get_file_content` calls `get_file()` API and decodes the blob content
- Error handling wraps boto3 exceptions into MCP-friendly error responses
- Server runs as a stdio-based MCP server process

### 2. CodePipeline MCP Server

**Technology:** Python 3.11+, MCP SDK (`mcp` package), boto3

**File Structure:**
```
mcp-servers/codepipeline/
├── server.py          # MCP server entry point and tool definitions
├── handlers.py        # Tool handler implementations
├── requirements.txt   # Python dependencies
└── README.md
```

**Tools Exposed:**

| Tool Name | Parameters | Returns |
|-----------|-----------|---------|
| `get_pipeline_state` | `pipeline_name` | Pipeline state with stage/action statuses |
| `get_pipeline_execution` | `pipeline_name`, `execution_id` | Execution details (status, timestamps, trigger) |
| `get_action_execution_details` | `pipeline_name`, `execution_id`, `stage_name`, `action_name` | Error messages, output variables, logs URL |
| `list_pipeline_executions` | `pipeline_name`, `max_results` (optional, default: 5) | Recent executions with statuses |

**Implementation Details:**
- Uses `boto3.client('codepipeline')` for AWS API calls
- `get_pipeline_state` calls `get_pipeline_state()` API
- `get_action_execution_details` calls `list_action_executions()` with filters
- Extracts error messages from `actionExecutionDetails[].output.executionResult.externalExecutionSummary`
- Server runs as a stdio-based MCP server process

### 3. Bedrock Agent Orchestrator

**Technology:** Python 3.11+, boto3 (Bedrock Runtime), LangChain or direct Bedrock Converse API

**File Structure:**
```
backend/
├── app.py             # FastAPI application entry point
├── agent.py           # Bedrock Agent orchestration logic
├── mcp_client.py      # MCP client for connecting to MCP servers
├── prompts.py         # System prompts and prompt templates
├── models.py          # Pydantic models for request/response
├── config.py          # Configuration (model ID, MCP server paths)
├── requirements.txt
└── README.md
```

**Agent Design:**
- Uses Bedrock Converse API with `tool_use` for MCP tool invocation
- System prompt instructs the agent on diagnostic methodology:
  1. Retrieve pipeline execution state
  2. Identify the failed stage and action
  3. Read error messages from the failed action
  4. Based on error type, invoke appropriate MCP tools for deeper investigation
  5. Produce structured diagnosis

**System Prompt Strategy:**
```
You are a CI/CD diagnostics agent. When given a failed pipeline, follow this process:
1. Get the pipeline state to identify which stage/action failed
2. Get the action execution details to read the error message
3. Based on the error:
   - If deployment config error → check repository files with CodeCommit tools
   - If access denied/permission error → check IAM role policies
   - If build/execution error → check CloudWatch logs
4. Produce a diagnosis with: root_cause_category, root_cause_description, affected_resource, recommended_fix
```

**MCP Client Integration:**
- Spawns MCP server processes as subprocesses
- Communicates via stdio JSON-RPC (standard MCP transport)
- Translates MCP tool schemas into Bedrock Converse tool definitions
- Routes tool_use responses back to appropriate MCP server

**Diagnosis Output Schema:**
```json
{
  "root_cause_category": "Configuration Issue | Permission Issue | Infrastructure Issue",
  "root_cause_description": "Human-readable explanation of what went wrong",
  "affected_resource": "ARN or identifier of the affected resource",
  "recommended_fix": "Step-by-step instructions to resolve the issue",
  "evidence": [
    {"source": "tool_name", "finding": "what was discovered"}
  ]
}
```

### 4. Demo UI

**Technology:** React 18, TypeScript, Tailwind CSS, AWS Amplify (optional for hosting)

**File Structure:**
```
demo-ui/
├── src/
│   ├── App.tsx
│   ├── components/
│   │   ├── PipelineList.tsx        # Pipeline list view
│   │   ├── PipelineDetail.tsx      # Pipeline detail with stages
│   │   ├── AnalysisPanel.tsx       # Diagnosis results display
│   │   ├── StageVisualization.tsx  # Pipeline stage flow diagram
│   │   └── Layout.tsx             # Console-like shell layout
│   ├── api/
│   │   └── client.ts              # API client for backend
│   ├── types/
│   │   └── index.ts               # TypeScript type definitions
│   └── styles/
│       └── aws-console.css        # AWS console styling overrides
├── package.json
├── tailwind.config.js
├── tsconfig.json
└── vite.config.ts
```

**UI Design:**
- Left navigation mimicking AWS console sidebar (CodePipeline, CodeCommit, CodeDeploy links)
- Main content area with pipeline list → pipeline detail drill-down
- Analysis panel slides in from the right when a failed execution is selected
- Loading state shows animated "Analyzing..." with progress indicators for each MCP tool call
- Color scheme: AWS dark nav (#232f3e), orange accents (#ff9900), white content area

**API Endpoints (Backend):**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/pipelines` | GET | List all demo pipelines with status |
| `/api/pipelines/{name}` | GET | Get pipeline detail with stages |
| `/api/pipelines/{name}/executions/{id}` | GET | Get execution details |
| `/api/pipelines/{name}/executions/{id}/diagnose` | POST | Trigger diagnosis, returns analysis |

### 5. Seeded Failure Infrastructure

**Technology:** AWS CDK (Python)

**File Structure:**
```
infrastructure/
├── app.py                    # CDK app entry point
├── stacks/
│   ├── scenario1_stack.py    # Missing appspec.yml scenario
│   ├── scenario2_stack.py    # Missing IAM permission scenario
│   ├── scenario3_stack.py    # LZA OU mismatch scenario
│   └── shared_stack.py       # Shared resources (S3 artifact bucket, etc.)
├── seed_data/
│   ├── scenario1/            # Repo contents without appspec.yml
│   │   └── index.html
│   ├── scenario2/            # Repo contents (valid, issue is in IAM)
│   │   ├── appspec.yml
│   │   └── index.html
│   └── scenario3/            # LZA config with bad OU name
│       └── accounts-config.yaml
├── cdk.json
├── requirements.txt
└── README.md
```

**Scenario 1 Stack:**
- CodeCommit repository with sample app files but NO appspec.yml
- CodePipeline: Source (CodeCommit) → Deploy (CodeDeploy)
- CodeDeploy application and deployment group targeting a dummy EC2 instance
- Pipeline triggers on repo creation, fails at Deploy stage

**Scenario 2 Stack:**
- CodeCommit repository with valid source code and appspec.yml
- IAM role for pipeline with deliberately missing `codecommit:GitPull` permission
- CodePipeline: Source (CodeCommit) → Build (CodeBuild)
- Pipeline fails at Source stage with AccessDenied

**Scenario 3 Stack:**
- CodeCommit repository containing LZA-style accounts-config.yaml
- accounts-config.yaml references OU name "Workloads-Production" but actual OU is "Workloads-Prod"
- CodePipeline: Source (CodeCommit) → Build (CodeBuild with LZA validation script)
- CodeBuild project runs a validation script that checks OU names against AWS Organizations
- Pipeline fails at Build stage with validation error in CloudWatch logs

### 6. Pre-built MCP Server Integration

**AWS Labs MCP Servers (from github.com/awslabs/mcp):**

- **IAM MCP Server**: Provides tools for `get_role`, `get_role_policy`, `list_attached_role_policies`, `get_policy_version`
- **CloudWatch MCP Server**: Provides tools for `get_log_events`, `filter_log_events`, `describe_log_groups`

**Integration approach:**
- Clone/install AWS Labs MCP servers as dependencies
- Configure them with appropriate AWS credentials (same account as seeded infrastructure)
- Register their tool schemas with the Bedrock Agent alongside custom MCP server tools

## Data Flow: Diagnosis Sequence

```
User clicks "Analyze" on failed pipeline
        │
        ▼
Backend receives POST /diagnose
        │
        ▼
Agent invokes: codepipeline.get_pipeline_state(pipeline_name)
        │
        ▼
Agent invokes: codepipeline.get_action_execution_details(...)
        │
        ▼
Agent reads error message, determines investigation path
        │
        ├─── Config error ──► codecommit.list_files() → codecommit.get_file_content()
        │
        ├─── Permission error ──► iam.get_role_policy() → iam.list_attached_role_policies()
        │
        └─── Build error ──► cloudwatch.filter_log_events()
                              → codecommit.get_file_content()
        │
        ▼
Agent produces structured diagnosis JSON
        │
        ▼
Backend returns diagnosis to UI
        │
        ▼
Analysis Panel renders results
```

## Technology Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| MCP Server Language | Python | Matches MCP SDK availability, boto3 native, team familiarity |
| Backend Framework | FastAPI | Async support, auto-generated OpenAPI docs, lightweight |
| Frontend Framework | React + TypeScript | Component-based UI, strong typing, wide ecosystem |
| Styling | Tailwind CSS | Rapid prototyping, easy to match AWS console look |
| IaC | AWS CDK (Python) | Consistent language with MCP servers, higher-level constructs |
| Agent Framework | Bedrock Converse API | Direct AWS integration, no external dependencies |
| MCP Transport | stdio | Standard MCP transport, simple subprocess management |

## Security Considerations

- Demo runs in a dedicated AWS account (not production)
- IAM roles for MCP servers follow least-privilege (read-only access to relevant services)
- No sensitive data in seeded repositories
- API backend does not require authentication (demo-only, local or internal network)
- AWS credentials managed via environment variables or IAM instance profiles

## Deployment Strategy

1. Deploy seeded infrastructure via `cdk deploy --all`
2. Start MCP servers as local processes (or containerized)
3. Start backend API server
4. Start frontend dev server or serve built static assets
5. Demo is ready — presenter navigates to UI and triggers analysis on each scenario

## Correctness Properties

### Property 1: MCP Server Tool Schema Validity
For all tools exposed by the CodeCommit_MCP_Server and CodePipeline_MCP_Server, the tool schema SHALL be valid JSON Schema and SHALL include required parameter definitions with types and descriptions.

### Property 2: Error Response Consistency
For all invalid inputs to custom MCP server tools (non-existent repos, files, pipelines), the server SHALL return an error response with a human-readable message and SHALL NOT throw an unhandled exception.

### Property 3: Diagnosis Completeness
For all three seeded failure scenarios, the Bedrock_Agent diagnosis output SHALL contain all four required fields: root_cause_category, root_cause_description, affected_resource, and recommended_fix.

### Property 4: Diagnosis Accuracy
For each seeded failure scenario, the root_cause_category in the diagnosis SHALL match the expected category (Configuration Issue, Permission Issue, or Infrastructure Issue respectively).

### Property 5: Infrastructure Idempotency
Deploying the seeded failure infrastructure via CDK SHALL be idempotent — running `cdk deploy` multiple times SHALL produce the same resource state without errors.

### Property 6: UI State Consistency
The Analysis_Panel SHALL only display diagnosis results when a failed execution is selected. Selecting a successful execution or no execution SHALL show no analysis content.
