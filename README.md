# CodeSuite Diagnostics Demo

An intelligent "Analysis" section for the AWS CodeSuite console that uses MCP (Model Context Protocol) servers and Amazon Bedrock to automatically diagnose CI/CD pipeline failures and provide actionable recommendations.

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
│            Amazon Bedrock Agent (Claude Haiku 4.5)               │
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
├── tests/                 # Unit tests and E2E integration tests
├── docs/                  # Demo talking points
└── README.md
```

## Prerequisites

### Required Software

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | MCP servers, backend, CDK (macOS system Python 3.9 will NOT work) |
| Node.js | 22+ | Frontend dev server (Vite requires 20.19+ or 22+) |
| npm | 9+ | Frontend package management |
| AWS CLI | 2.x | AWS credential management |
| AWS CDK CLI | 2.1100+ | Infrastructure deployment |

### Install dependencies

```bash
# Install CDK CLI
npm install -g aws-cdk

# If using nvm for Node.js
nvm install 22
nvm use 22

# If Python 3.11 is not your default, install via Homebrew (macOS)
brew install python@3.11
```

### AWS Account Setup

1. **AWS Credentials**: Configure credentials with permissions for CodeCommit, CodePipeline, CodeBuild, CodeDeploy, IAM, S3, CloudWatch, EC2, and Bedrock:
   ```bash
   aws configure
   ```

2. **Amazon Bedrock Access**: Enable model access in the [Bedrock console](https://console.aws.amazon.com/bedrock/) under Model Access. The demo uses **Claude Haiku 4.5** via the inference profile `us.anthropic.claude-haiku-4-5-20251001-v1:0`. You can change this by setting the `BEDROCK_MODEL_ID` environment variable.

3. **CDK Bootstrap** (one-time per account/region):
   ```bash
   cdk bootstrap aws://<YOUR_ACCOUNT_ID>/us-east-1
   ```

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/sonaliks/CodeSuite-Console-Analysis.git
cd CodeSuite-Console-Analysis
```

### 2. Install Python Dependencies

```bash
# Use Python 3.11+ (not system Python 3.9)
python3.11 -m pip install mcp boto3 fastapi uvicorn pydantic
```

### 3. Install Frontend Dependencies

```bash
cd demo-ui
npm install
cd ..
```

### 4. Configure CDK for Your Account

Edit `infrastructure/app.py` and update the account ID:

```python
env = cdk.Environment(
    account="<YOUR_AWS_ACCOUNT_ID>",  # Replace with your account ID
    region="us-east-1",
)
```

### 5. Deploy Infrastructure

```bash
cd infrastructure
python3.11 -m pip install -r requirements.txt
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Synthesize to verify templates
cdk synth

# Deploy all stacks
cdk deploy --all --require-approval never
```

This creates:
- **Shared Stack**: S3 artifact bucket
- **Scenario 1**: CodePipeline + CodeDeploy + EC2 instance (fails due to missing `appspec.yml`)
- **Scenario 2**: CodePipeline with restricted IAM role (fails due to missing `codecommit:GitPull`)
- **Scenario 3**: CodePipeline + CodeBuild LZA validator (fails due to OU name mismatch)

### 6. Push Seed Data to CodeCommit Repositories

After CDK deploy, the repos are empty. Push the seed data so the pipelines trigger and fail correctly:

```bash
# Scenario 1: App without appspec.yml
aws codecommit put-file \
  --repository-name codesuite-diag-scenario1-app \
  --branch-name main \
  --file-content fileb://infrastructure/seed_data/scenario1/index.html \
  --file-path index.html \
  --commit-message "Initial commit" --name "Demo" --email "demo@example.com"

COMMIT_ID=$(aws codecommit get-branch --repository-name codesuite-diag-scenario1-app --branch-name main --query 'branch.commitId' --output text)
aws codecommit put-file \
  --repository-name codesuite-diag-scenario1-app \
  --branch-name main \
  --file-content fileb://infrastructure/seed_data/scenario1/scripts/app.js \
  --file-path scripts/app.js \
  --parent-commit-id "$COMMIT_ID" \
  --commit-message "Add scripts" --name "Demo" --email "demo@example.com"

# Scenario 2: Valid app (pipeline fails on IAM permission)
aws codecommit put-file \
  --repository-name codesuite-diag-scenario2-app \
  --branch-name main \
  --file-content fileb://infrastructure/seed_data/scenario2/index.html \
  --file-path index.html \
  --commit-message "Initial commit" --name "Demo" --email "demo@example.com"

COMMIT_ID=$(aws codecommit get-branch --repository-name codesuite-diag-scenario2-app --branch-name main --query 'branch.commitId' --output text)
aws codecommit put-file \
  --repository-name codesuite-diag-scenario2-app \
  --branch-name main \
  --file-content fileb://infrastructure/seed_data/scenario2/appspec.yml \
  --file-path appspec.yml \
  --parent-commit-id "$COMMIT_ID" \
  --commit-message "Add appspec" --name "Demo" --email "demo@example.com"

COMMIT_ID=$(aws codecommit get-branch --repository-name codesuite-diag-scenario2-app --branch-name main --query 'branch.commitId' --output text)
aws codecommit put-file \
  --repository-name codesuite-diag-scenario2-app \
  --branch-name main \
  --file-content fileb://infrastructure/seed_data/scenario2/buildspec.yml \
  --file-path buildspec.yml \
  --parent-commit-id "$COMMIT_ID" \
  --commit-message "Add buildspec" --name "Demo" --email "demo@example.com"

# Scenario 3: LZA config with invalid OU
aws codecommit put-file \
  --repository-name codesuite-diag-scenario3-lza-config \
  --branch-name main \
  --file-content fileb://infrastructure/seed_data/scenario3/accounts-config.yaml \
  --file-path accounts-config.yaml \
  --commit-message "Initial commit" --name "Demo" --email "demo@example.com"

COMMIT_ID=$(aws codecommit get-branch --repository-name codesuite-diag-scenario3-lza-config --branch-name main --query 'branch.commitId' --output text)
aws codecommit put-file \
  --repository-name codesuite-diag-scenario3-lza-config \
  --branch-name main \
  --file-content fileb://infrastructure/seed_data/scenario3/buildspec.yml \
  --file-path buildspec.yml \
  --parent-commit-id "$COMMIT_ID" \
  --commit-message "Add buildspec" --name "Demo" --email "demo@example.com"

COMMIT_ID=$(aws codecommit get-branch --repository-name codesuite-diag-scenario3-lza-config --branch-name main --query 'branch.commitId' --output text)
aws codecommit put-file \
  --repository-name codesuite-diag-scenario3-lza-config \
  --branch-name main \
  --file-content fileb://infrastructure/seed_data/scenario3/validate_ou_names.py \
  --file-path validate_ou_names.py \
  --parent-commit-id "$COMMIT_ID" \
  --commit-message "Add validation script" --name "Demo" --email "demo@example.com"
```

Wait 1-2 minutes for the pipelines to trigger and fail, then verify:

```bash
aws codepipeline get-pipeline-state --name codesuite-diag-scenario1-pipeline \
  --query "stageStates[*].{stage:stageName,status:latestExecution.status}" --output table

aws codepipeline get-pipeline-state --name codesuite-diag-scenario3-pipeline \
  --query "stageStates[*].{stage:stageName,status:latestExecution.status}" --output table
```

Expected: Source Succeeded, Deploy/Build Failed.

## Running the Demo

### Start Services

```bash
# Terminal 1: Start the backend (use Python 3.11+)
cd backend
python3.11 -m uvicorn app:app --host 0.0.0.0 --port 8000

# Terminal 2: Start the frontend
cd demo-ui
npm run dev
```

Access the demo at: **http://localhost:5173**

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `BEDROCK_MODEL_ID` | `us.anthropic.claude-haiku-4-5-20251001-v1:0` | Bedrock inference profile ID |
| `BEDROCK_REGION` | `us-east-1` | AWS region for Bedrock API calls |
| `API_HOST` | `0.0.0.0` | Backend server bind address |
| `API_PORT` | `8000` | Backend server port |

### Changing the Bedrock Model

To use a different Claude model, set the environment variable before starting the backend:

```bash
export BEDROCK_MODEL_ID=us.anthropic.claude-sonnet-4-20250514-v1:0
```

Check available inference profiles in your account:
```bash
aws bedrock list-inference-profiles --query "inferenceProfileSummaries[?contains(inferenceProfileId,'claude')].{id:inferenceProfileId,status:status}" --output table
```

## Demo Walkthrough

### How It Works

1. Open http://localhost:5173
2. The pipeline list shows all pipelines in your account that have a failed latest execution
3. Click a failed pipeline to see its stage visualization and execution history
4. Click **"Analyze"** on a failed execution
5. The Bedrock Agent investigates using MCP tools (takes 30-60 seconds)
6. The Analysis Panel displays: root cause category, description, affected resource, and recommended fix

### Scenario 1: Missing appspec.yml (Configuration Issue)

- Pipeline: `codesuite-diag-scenario1-pipeline`
- Failure: Deploy stage fails because `appspec.yml` is missing from the CodeCommit repo
- Agent investigates: gets pipeline state → reads error → lists repo files → confirms appspec is absent

### Scenario 2: Missing IAM Permission (Permission Issue)

- Pipeline: `codesuite-diag-scenario2-pipeline`
- Failure: Source stage fails due to AccessDenied (missing `codecommit:GitPull`)
- Agent investigates: gets pipeline state → reads error → inspects IAM role policies → identifies missing permission

### Scenario 3: LZA Config OU Mismatch (Infrastructure Issue)

- Pipeline: `codesuite-diag-scenario3-pipeline`
- Failure: Build stage fails because `accounts-config.yaml` references OU "Workloads-Production" (should be "Workloads-Prod")
- Agent investigates: gets pipeline state → reads build logs → reads config file → identifies OU mismatch

## Verifying the Setup

```bash
# Backend health check
curl http://localhost:8000/health
# Expected: {"status":"healthy","service":"codesuite-diagnostics-backend"}

# List failed pipelines
curl http://localhost:8000/api/pipelines | python3 -m json.tool

# Trigger a diagnosis
curl -X POST http://localhost:8000/api/pipelines/codesuite-diag-scenario1-pipeline/executions/latest/diagnose
```

## Running Tests

```bash
# Unit tests (no AWS credentials needed)
python3.11 -m pytest tests/test_codecommit_handlers.py tests/test_codepipeline_handlers.py -v

# E2E tests (requires running backend + deployed infrastructure)
RUN_E2E_TESTS=1 python3.11 -m pytest tests/test_e2e_scenarios.py -v
```

## Teardown

Remove all AWS resources:

```bash
cd infrastructure
source .venv/bin/activate
cdk destroy --all
```

This removes all CodeCommit repos, pipelines, EC2 instances, IAM roles, S3 buckets, etc.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'mcp'` | Install with `python3.11 -m pip install mcp` |
| `CDK synth fails with "StackAccountRegionNotSpecified"` | Update `infrastructure/app.py` with your account ID and region |
| Bedrock returns "model is legacy" | Use an inference profile ID (e.g., `us.anthropic.claude-haiku-4-5-20251001-v1:0`) |
| Bedrock returns "Access denied" | Enable model access in the Bedrock console |
| Vite requires Node.js 20.19+ | Upgrade Node: `nvm install 22 && nvm use 22` |
| Frontend can't reach backend | Ensure backend runs on port 8000; frontend proxies to it |
| Pipelines show "branch not found" | Push seed data first (see Step 6 above) |
| `cdk deploy` hangs at VPC lookup | Ensure your AWS credentials are valid and region is correct |

## License

This project is for internal demo purposes.
