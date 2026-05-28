# Presentation Talking Points

## Mapping Demo Scenarios to 2-Pager Root Cause Categories

This document provides presenter talking points for each demo scenario, mapping them directly to the root cause categories identified in the original 2-pager idea document.

---

## 2-Pager Root Cause Categories (Summary)

| Category | Description | Case Volume |
|----------|-------------|-------------|
| **Configuration Issues** | File naming inconsistencies, missing/misconfigured OU names in LZA config, YAML/JSON syntax errors, missing appspec or buildspec files | ~9,214 cases |
| **Permission Issues** | Insufficient IAM role permissions preventing pipeline execution | ~12,397 cases |
| **Infrastructure Issues** | LZA pipeline failures requiring manual stack investigation, pipeline source configuration mismatches | ~2,466 cases |

---

## Scenario 1: Missing appspec.yml

### 2-Pager Category Mapping

**Root Cause Category:** Configuration Issue

**2-Pager Reference:** *"...the absence of critical appspec or buildspec files at repository roots, accounting for approximately 9,214 cases."*

This scenario directly demonstrates one of the most common configuration issues identified in the 2-pager: a missing deployment configuration file at the repository root.

### What Happens

- A CodePipeline with a CodeDeploy action fails because `appspec.yml` is absent from the CodeCommit repository
- The Deploy stage errors out with a configuration-related failure message
- The pipeline shows a failed state in the console

### What the Agent Does

1. Retrieves pipeline state via the CodePipeline MCP Server → identifies the Deploy stage failed
2. Gets action execution details → reads the CodeDeploy error message about missing appspec.yml
3. Inspects the repository via the CodeCommit MCP Server → confirms appspec.yml is not present at the root
4. Produces a structured diagnosis classifying this as a "Configuration Issue"

### What the Audience Sees

- The Analysis Panel displays:
  - **Category Badge:** "Configuration Issue"
  - **Root Cause:** Missing appspec.yml file in repository root
  - **Affected Resource:** The CodeCommit repository ARN
  - **Recommended Fix:** Exact appspec.yml file content and location to add

### Presenter Talking Points

- "This represents the largest category of issues we see — configuration problems account for over 9,000 cases."
- "The agent doesn't just tell you something is wrong — it inspects the repository, confirms what's missing, and gives you the exact file content to fix it."
- "Notice how the agent used two different MCP servers here: CodePipeline to understand the failure, and CodeCommit to investigate the root cause."
- "Today, a developer would need to read the error, open CodeCommit, manually check for the file, then look up the correct appspec format. The agent does all of this in seconds."

---

## Scenario 2: Insufficient IAM Permissions

### 2-Pager Category Mapping

**Root Cause Category:** Permission Issue

**2-Pager Reference:** *"Permission issues create significant bottlenecks through insufficient IAM role permissions that prevent pipeline execution, representing 12,397 cases."*

This scenario demonstrates the highest-volume issue category: IAM permission gaps that block pipeline execution entirely.

### What Happens

- A CodePipeline's service role is missing the `codecommit:GitPull` permission
- The Source stage fails with an AccessDenied error when trying to pull code from CodeCommit
- The pipeline never reaches the Build or Deploy stages

### What the Agent Does

1. Retrieves pipeline state via the CodePipeline MCP Server → identifies the Source stage failed
2. Gets action execution details → reads the AccessDenied error message
3. Identifies the pipeline's service role and invokes the IAM MCP Server to inspect its policies
4. Determines that `codecommit:GitPull` is missing from the role's permissions
5. Produces a structured diagnosis classifying this as a "Permission Issue"

### What the Audience Sees

- The Analysis Panel displays:
  - **Category Badge:** "Permission Issue"
  - **Root Cause:** Pipeline service role lacks `codecommit:GitPull` permission
  - **Affected Resource:** The IAM role ARN attached to the pipeline
  - **Recommended Fix:** The exact IAM policy statement to add to the role

### Presenter Talking Points

- "Permission issues are actually our highest-volume category at over 12,000 cases. They're particularly frustrating because the error messages are often cryptic."
- "Here the agent correlates information across services — it reads the pipeline error, identifies the IAM role, then inspects that role's policies using a separate MCP server."
- "This demonstrates the power of the MCP ecosystem: we're using the pre-built AWS Labs IAM MCP Server alongside our custom CodePipeline server. Ecosystem reuse in action."
- "The recommended fix isn't generic advice — it's the specific IAM policy statement the developer needs to add, ready to copy-paste."
- "Without this tool, a developer would need to: read the error, find the pipeline's role ARN, navigate to IAM, inspect multiple policies, understand what's missing, and write the correct policy. That's 15-20 minutes of context-switching."

---

## Scenario 3: LZA Config OU Mismatch

### 2-Pager Category Mapping

**Root Cause Category:** Infrastructure Issue

**2-Pager Reference:** *"Infrastructure issues compound these problems with LZA pipeline failures requiring manual stack investigation..."* and *"...missing or misconfigured organizational unit names within LZA configuration files..."*

This scenario bridges two 2-pager categories — it's classified as an Infrastructure Issue (LZA pipeline failure) but the underlying cause is a configuration mismatch (misconfigured OU name). This demonstrates the agent's ability to perform deep investigation that crosses category boundaries.

### What Happens

- An LZA pipeline runs a validation step via CodeBuild that checks `accounts-config.yaml` against AWS Organizations
- The config references OU name "Workloads-Production" but the actual OU is "Workloads-Prod"
- The Build stage fails with a validation error logged to CloudWatch

### What the Agent Does

1. Retrieves pipeline state via the CodePipeline MCP Server → identifies the Build stage failed
2. Gets action execution details → sees a CodeBuild failure
3. Invokes the CloudWatch MCP Server → retrieves build logs showing the OU validation error
4. Inspects `accounts-config.yaml` via the CodeCommit MCP Server → finds the "Workloads-Production" reference
5. Cross-references against the actual organization structure → identifies "Workloads-Prod" as the correct name
6. Produces a structured diagnosis classifying this as an "Infrastructure Issue"

### What the Audience Sees

- The Analysis Panel displays:
  - **Category Badge:** "Infrastructure Issue"
  - **Root Cause:** accounts-config.yaml references non-existent OU "Workloads-Production"
  - **Affected Resource:** The accounts-config.yaml file path in the repository
  - **Recommended Fix:** Change "Workloads-Production" to "Workloads-Prod", with valid OU names listed

### Presenter Talking Points

- "LZA failures are particularly painful — they require manual stack investigation and deep organizational knowledge. This is exactly the kind of issue that eats up senior engineer time."
- "Watch how the agent chains four different MCP servers together: CodePipeline for the failure, CloudWatch for the logs, CodeCommit for the config file, and organizational data for validation."
- "The agent doesn't just say 'OU not found' — it tells you the exact correct value. It lists the valid OU names so the developer can pick the right one immediately."
- "This scenario shows the agent handling a real-world LZA issue. In production, these mismatches can block entire account provisioning workflows for hours."
- "Notice the sophistication: the agent read the build logs, identified the problematic file, read that file, and cross-referenced against the actual org structure. That's multi-step reasoning across multiple data sources."

---

## Cross-Scenario Themes for the Presentation

### Key Messages

1. **Full coverage of root cause categories** — The three scenarios map directly to all three categories from the 2-pager, demonstrating the system handles the full spectrum of CI/CD failures.

2. **MCP ecosystem leverage** — The demo uses both custom MCP servers (CodeCommit, CodePipeline) and pre-built AWS Labs servers (IAM, CloudWatch), showing how the ecosystem approach scales.

3. **Multi-service correlation** — Each scenario requires the agent to gather evidence from multiple AWS services, mimicking real-world debugging workflows that currently take 15-30 minutes.

4. **Actionable output** — The agent doesn't just identify problems; it provides copy-paste-ready fixes (file content, IAM policies, config corrections).

5. **Business impact** — Combined, these categories represent ~24,000 cases. Automating diagnosis directly addresses the 2-pager's identified business impact: reduced development velocity, diverted engineering resources, and customer frustration.

### Suggested Demo Flow

| Order | Scenario | Category | Complexity | Time |
|-------|----------|----------|------------|------|
| 1 | Missing appspec.yml | Configuration Issue | Simple | 2 min |
| 2 | IAM Permission Gap | Permission Issue | Medium | 3 min |
| 3 | LZA OU Mismatch | Infrastructure Issue | Complex | 4 min |

**Rationale:** Start simple to establish the pattern, then increase complexity to show the agent's reasoning depth. Each scenario introduces additional MCP servers, building the audience's understanding of the architecture.

### Anticipated Questions

| Question | Suggested Answer |
|----------|-----------------|
| "How does it know which tools to use?" | "The Bedrock Agent uses Claude 3.5 Sonnet's reasoning to select tools based on the error context. The system prompt guides the diagnostic methodology, but the model decides the investigation path." |
| "Can it handle failures it hasn't seen before?" | "Yes — the agent reasons about errors generically. The MCP tools give it access to the same information a human would use. New failure types just require the right data to be accessible via MCP." |
| "What about latency?" | "Diagnosis typically completes in 10-30 seconds depending on the number of tool calls needed. This is dramatically faster than the 15-30 minutes of manual investigation." |
| "How hard is it to add new MCP servers?" | "Each MCP server is a lightweight Python process with 3-5 tool definitions. Adding a new service takes a day or two of development." |
| "Is this production-ready?" | "This is a demo/proof-of-concept. Production would need auth, rate limiting, caching, and broader failure coverage. But the architecture is sound and extensible." |
