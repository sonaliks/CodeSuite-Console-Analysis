"""Pydantic models for the CodeSuite Diagnostics Demo API."""

from __future__ import annotations

from enum import Enum
from typing import List

from pydantic import BaseModel


class RootCauseCategory(str, Enum):
    """Categories of root causes for pipeline failures."""
    CONFIGURATION = "Configuration Issue"
    PERMISSION = "Permission Issue"
    INFRASTRUCTURE = "Infrastructure Issue"


class EvidenceItem(BaseModel):
    """A piece of evidence gathered during diagnosis."""
    source: str
    finding: str


class DiagnosisResponse(BaseModel):
    """Structured diagnosis output from the Bedrock Agent."""
    root_cause_category: RootCauseCategory
    root_cause_description: str
    affected_resource: str
    recommended_fix: str
    evidence: list[EvidenceItem] = []


class PipelineInfo(BaseModel):
    """Pipeline summary information."""
    name: str
    status: str
    stages: list[str]
    description: str = ""


class PipelineExecution(BaseModel):
    """Pipeline execution details."""
    pipeline_name: str
    execution_id: str
    status: str
