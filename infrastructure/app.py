#!/usr/bin/env python3
"""CDK app entry point for CodeSuite Diagnostics Demo infrastructure."""

import aws_cdk as cdk

from stacks.shared_stack import SharedStack

app = cdk.App()

SharedStack(app, "CodeSuiteDiagnostics-Shared")

app.synth()
