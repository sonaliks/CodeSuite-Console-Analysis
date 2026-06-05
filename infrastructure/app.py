#!/usr/bin/env python3
"""CDK app entry point for CodeSuite Diagnostics Demo infrastructure."""

import os
import aws_cdk as cdk

from stacks.shared_stack import SharedStack
from stacks.scenario1_stack import Scenario1Stack
from stacks.scenario2_stack import Scenario2Stack
from stacks.scenario3_stack import Scenario3Stack

app = cdk.App()

env = cdk.Environment(
    account=os.environ.get("CDK_DEFAULT_ACCOUNT", "REPLACE_WITH_YOUR_ACCOUNT_ID"),
    region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1"),
)

shared = SharedStack(app, "CodeSuiteDiagnostics-Shared", env=env)

scenario1 = Scenario1Stack(app, "CodeSuiteDiagnostics-Scenario1", env=env)
scenario1.add_dependency(shared)

scenario2 = Scenario2Stack(app, "CodeSuiteDiagnostics-Scenario2", env=env)
scenario2.add_dependency(shared)

scenario3 = Scenario3Stack(app, "CodeSuiteDiagnostics-Scenario3", env=env)
scenario3.add_dependency(shared)

app.synth()
