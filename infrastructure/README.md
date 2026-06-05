# CodeSuite Diagnostics Demo - Infrastructure

AWS CDK project for deploying the seeded failure infrastructure used in the CodeSuite Diagnostics Demo.

## Structure

```
infrastructure/
├── app.py                    # CDK app entry point
├── stacks/
│   ├── shared_stack.py       # Shared resources (S3 artifact bucket)
│   ├── scenario1_stack.py    # Missing appspec.yml scenario (future)
│   ├── scenario2_stack.py    # Missing IAM permission scenario (future)
│   └── scenario3_stack.py    # ECS deployment failure scenario
├── cdk.json                  # CDK configuration
├── requirements.txt          # Python dependencies
└── README.md
```

## Prerequisites

- Python 3.11+
- AWS CDK CLI (`npm install -g aws-cdk`)
- AWS credentials configured
- CDK bootstrapped in target account/region (`cdk bootstrap`)

## Setup

```bash
cd infrastructure
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Deploy

```bash
cdk synth    # Synthesize CloudFormation template
cdk deploy   # Deploy all stacks
```

## Teardown

All resources are configured with `RemovalPolicy.DESTROY` and auto-delete for easy cleanup:

```bash
cdk destroy --all
```

## Shared Resources

The shared stack provides:
- **S3 Artifact Bucket**: Used by CodePipeline across all scenarios for storing pipeline artifacts. Configured with encryption, public access blocking, and SSL enforcement.
