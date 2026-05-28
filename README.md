# CodeSuite Diagnostics Demo

An intelligent "Analysis" section for the AWS CodeSuite console that uses MCP (Model Context Protocol) servers and Amazon Bedrock (Claude 3.5 Sonnet) to automatically diagnose CI/CD pipeline failures and provide actionable recommendations.

This demo showcases three failure scenarios — configuration issues, permission issues, and infrastructure issues — with a React-based UI mimicking the AWS console experience.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Demo UI (React + TypeScript)                  │
│   Pipeline List  │  Pipeline Detail  │  Analysis Panel           │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Backend API (Python FastAPI)                     │
│            Amazon Bedrock Agent (Claude 3.5 Sonnet)              │
└──────┬──────────────┬──────────────┬──────────────┬─────────────┘
       │              │              │              │
       ▼              ▼              ▼              ▼
  CodeCommit     CodePipeline      IAM MCP      CloudWatch
  MCP Server     MCP Server        Server       MCP Server
  (Custom)       (Custom)        (AWS Labs)    (AWS Labs)
       │              │              │              │
       └──────────────┴──────────────┴──────────────┘
                             │
                    AWS Account (Seeded Failures)
```

## Project Structure

```
├── mcp-servers/
│   ├── codecommit/        # Custom MCP server for CodeCommit operations
│   └── codepipeline/      # Custom MCP server for CodePipeline operations
├── backend/               # FastAPI backend with Bedrock Agent orchestration
├── demo-ui/               # React + TypeScript frontend (Vite, Tailwind CSS)
├── infrastructure/        # AWS CDK stacks for seeded failure scenarios
├── run-demo.sh            # Single command to start all services
└── README.md
```

## Prerequisites

Before setting up the demo, ensure you have the following:

### Required Software

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | MCP servers, backend, CDK |
| Node.js | 18+ | Frontend dev server |
| npm | 9+ | Frontend package management |
| AWS CLI | 2.x | AWS credential management |
| AWS CDK CLI | 2.120+ | Infrastructure deployment |

Install the AWS CDK CLI globally:

```bash
npm install -g aws-cdk
```

### AWS Account Setup

1. **AWS Account**: You need an AWS account with permissions to create CodeCommit, CodePipeline, CodeBuild, CodeDeploy, IAM, S3, and CloudWatch resources.

2. **AWS Credentials**: Configure credentials with sufficient permissions:
   ```bash
   aws configure
   ```
   Or set environment variables:
   ```bash
   export AWS_ACCESS_KEY_ID=<your-access-key>
   export AWS_SECRET_ACCESS_KEY=<your-secret-key>
   export AWS_DEFAULT_REGION=us-east-1
   ```

3. **Amazon Bedrock Access**: Ensure your account has access to Claude 3.5 Sonnet (`anthropic.claude-3-5-sonnet-20241022-v2:0`) in the `us-east-1` region. Request model access via the [Bedrock console](https://console.aws.amazon.com/bedrock/) if needed.

4. **CDK Bootstrap**: Bootstrap CDK in your target account and region (one-time setup):
   ```bash
   cdk bootstrap aws://<ACCOUNT_ID>/us-east-1
   ```

## Setup Instructions

### 1. Clone and Install Python Dependencies

```bash
# From the project root
pip install -r requirements.txt
```

### 2. Set Up MCP Servers

```bash
# CodeCommit MCP Server
cd mcp-servers/codecommit
pip install -r requirements.txt

# CodePipeline MCP Server
cd ../codepipeline
pip install -r requirements.txt
```

### 3. Set Up Backend

```bash
cd backend
pip install -r requirements.txt
```

### 4. Set Up Frontend

```bash
cd demo-ui
npm install
```

### 5. Set Up Infrastructure

```bash
cd infrastructure
pip install -r requirements.txt
```

## Deploying the Seeded Infrastructure

The infrastructure uses AWS CDK to deploy three failure scenarios as separate stacks:

```bash
cd infrastructure

# Preview what will be deployed
cdk synth

# Deploy all stacks (shared resources + 3 scenarios)
cdk deploy --all
```

This creates:
- **Shared Stack**: S3 artifact bucket used by all pipelines
- **Scenario 1 Stack**: CodePipeline with CodeDeploy that fails due to missing `appspec.yml`
- **Scenario 2 Stack**: CodePipeline with IAM role missing `codecommit:GitPull` permission
- **Scenario 3 Stack**: CodePipeline with LZA validation that fails due to OU name mismatch

After deployment, the pipelines will automatically trigger and fail predictably within one execution cycle.

## Running the Demo

### Quick Start (All Services)

Use the provided script to start all services with a single command:

```bash
./run-demo.sh
```

This starts:
1. CodeCommit MCP Server
2. CodePipeline MCP Server
3. Backend API Server (uvicorn on port 8000)
4. Frontend Dev Server (Vite on port 5173)

Access the demo at: **http://localhost:5173**

Press `Ctrl+C` to stop all services.

### Manual Start (Individual Services)

If you prefer to start services individually:

```bash
# Terminal 1: Backend API
cd backend
python3 -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Frontend
cd demo-ui
npm run dev
```

The MCP servers are spawned as subprocesses by the backend and do not need to be started separately in manual mode.

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BEDROCK_MODEL_ID` | `anthropic.claude-3-5-sonnet-20241022-v2:0` | Bedrock model to use |
| `BEDROCK_REGION` | `us-east-1` | AWS region for Bedrock API calls |
| `BACKEND_HOST` | `0.0.0.0` | Backend server bind address |
| `BACKEND_PORT` | `8000` | Backend server port |

## Demo Walkthrough

### Overview

The demo presents three pre-configured pipeline failures. For each scenario, the Bedrock Agent uses MCP tools to investigate the failure, identify the root cause, and provide a recommended fix — all displayed in the Analysis Panel.

---

### Scenario 1: Missing appspec.yml (Configuration Issue)

**What happens:** A CodePipeline with a CodeDeploy action fails because the CodeCommit repository is missing the required `appspec.yml` file.

**Demo steps:**
1. Open the demo UI at http://localhost:5173
2. Select the Scenario 1 pipeline from the pipeline list
3. Click on the failed execution
4. Click "Analyze" to trigger the Bedrock Agent diagnosis

**What the agent does:**
1. Retrieves the pipeline state and identifies the failed Deploy stage
2. Gets the action execution error details from CodeDeploy
3. Inspects the CodeCommit repository file listing using the CodeCommit MCP Server
4. Confirms `appspec.yml` is absent from the repository root

**Expected diagnosis:**
- **Category:** Configuration Issue
- **Root Cause:** Missing `appspec.yml` file in the repository root
- **Recommendation:** Add an `appspec.yml` file with the correct deployment configuration

---

### Scenario 2: Missing IAM Permission (Permission Issue)

**What happens:** A CodePipeline fails at the Source stage because the pipeline's IAM service role is missing the `codecommit:GitPull` permission.

**Demo steps:**
1. Select the Scenario 2 pipeline from the pipeline list
2. Click on the failed execution
3. Click "Analyze" to trigger diagnosis

**What the agent does:**
1. Retrieves the pipeline state and identifies the failed Source stage
2. Reads the AccessDenied error from the action execution details
3. Identifies the IAM role attached to the pipeline
4. Inspects the role's policies using the IAM MCP Server
5. Determines that `codecommit:GitPull` is not granted

**Expected diagnosis:**
- **Category:** Permission Issue
- **Root Cause:** Pipeline service role missing `codecommit:GitPull` permission
- **Recommendation:** Add an IAM policy statement granting `codecommit:GitPull` to the role

---

### Scenario 3: LZA Config OU Mismatch (Infrastructure Issue)

**What happens:** An LZA-style pipeline fails at the Build stage because `accounts-config.yaml` references an organizational unit name ("Workloads-Production") that doesn't exist — the actual OU is "Workloads-Prod".

**Demo steps:**
1. Select the Scenario 3 pipeline from the pipeline list
2. Click on the failed execution
3. Click "Analyze" to trigger diagnosis

**What the agent does:**
1. Retrieves the pipeline state and identifies the failed Build stage
2. Checks CloudWatch logs for the CodeBuild validation error
3. Retrieves `accounts-config.yaml` from the CodeCommit repository
4. Identifies the invalid OU reference "Workloads-Production"
5. Lists valid OU names from the organization structure

**Expected diagnosis:**
- **Category:** Infrastructure Issue
- **Root Cause:** `accounts-config.yaml` references OU "Workloads-Production" but the actual OU is "Workloads-Prod"
- **Recommendation:** Update the OU name in `accounts-config.yaml` to match the actual organization structure

---

## Verifying the Setup

After deploying infrastructure and starting services, use these steps to confirm everything is working:

### 1. Verify Infrastructure Deployment

```bash
cd infrastructure

# Check all stacks deployed successfully
cdk list
# Should show: SharedStack, Scenario1Stack, Scenario2Stack, Scenario3Stack

# Verify pipelines exist and have failed executions
aws codepipeline list-pipelines --query 'pipelines[].name'
```

### 2. Verify Backend API

```bash
# Health check
curl http://localhost:8000/health
# Expected: {"status": "ok"}

# List pipelines
curl http://localhost:8000/api/pipelines
# Expected: JSON array with 3 pipelines and their statuses
```

### 3. Verify Frontend

Open http://localhost:5173 in your browser. You should see:
- AWS console-style dark navigation sidebar
- Pipeline list with 3 pipelines showing "Failed" status indicators
- Clicking a pipeline shows stage visualization and execution history

### 4. Verify End-to-End Diagnosis

For each scenario, trigger a diagnosis and confirm the expected output:

```bash
# Get the latest failed execution ID for a pipeline
EXEC_ID=$(curl -s http://localhost:8000/api/pipelines/Scenario1Pipeline/executions | python3 -c "import sys,json; execs=json.load(sys.stdin); print(next(e['id'] for e in execs if e['status']=='Failed'))")

# Trigger diagnosis
curl -X POST http://localhost:8000/api/pipelines/Scenario1Pipeline/executions/$EXEC_ID/diagnose
```

**Expected results per scenario:**

| Scenario | Root Cause Category | Key Finding |
|----------|-------------------|-------------|
| 1 | Configuration Issue | Missing `appspec.yml` |
| 2 | Permission Issue | Missing `codecommit:GitPull` |
| 3 | Infrastructure Issue | OU name mismatch ("Workloads-Production" vs "Workloads-Prod") |

### 5. Verify from the UI

1. Select each failed pipeline in the UI
2. Click "Analyze" on the failed execution
3. Confirm the Analysis Panel shows the correct category, description, affected resource, and recommended fix
4. Verify the loading animation appears while the agent processes

If all three scenarios produce correct diagnoses, the demo is fully operational.

---

## Teardown

To remove all AWS resources created by the demo:

```bash
cd infrastructure
cdk destroy --all
```

This will:
- Delete all three scenario stacks and the shared stack
- Remove CodeCommit repositories, CodePipeline pipelines, CodeBuild projects, CodeDeploy applications, IAM roles, and S3 buckets
- All resources are configured with `RemovalPolicy.DESTROY` for clean teardown

Confirm the deletion when prompted. No manual cleanup is required — all resources are removed automatically.

## Troubleshooting

### Common Issues

**CDK deploy fails with "bootstrap required"**
```bash
cdk bootstrap aws://<ACCOUNT_ID>/<REGION>
```

**Bedrock model access denied**
Ensure you've enabled Claude 3.5 Sonnet access in the [Bedrock console](https://console.aws.amazon.com/bedrock/) under Model Access.

**MCP server connection errors**
Verify AWS credentials are configured and have the necessary permissions for CodeCommit, CodePipeline, IAM, and CloudWatch read access.

**Frontend can't reach backend**
Ensure the backend is running on port 8000. The frontend Vite dev server proxies API requests to `http://localhost:8000`.

## License

This project is for internal demo purposes.
