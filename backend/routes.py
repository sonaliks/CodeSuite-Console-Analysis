"""API route definitions for the CodeSuite Diagnostics Demo."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from agent import diagnose_pipeline_failure
from models import DiagnosisResponse, PipelineInfo, PipelineExecution

router = APIRouter()


# Demo pipeline data (in production this would come from AWS APIs)
DEMO_PIPELINES = {
    "codesuite-diag-scenario1-pipeline": PipelineInfo(
        name="codesuite-diag-scenario1-pipeline",
        status="Failed",
        stages=["Source", "Deploy"],
        description="Demo app deployment (missing appspec.yml)",
    ),
    "codesuite-diag-scenario2-pipeline": PipelineInfo(
        name="codesuite-diag-scenario2-pipeline",
        status="Failed",
        stages=["Source", "Build"],
        description="Demo app build (insufficient IAM permissions)",
    ),
    "codesuite-diag-scenario3-pipeline": PipelineInfo(
        name="codesuite-diag-scenario3-pipeline",
        status="Failed",
        stages=["Source", "Build"],
        description="LZA config validation (invalid OU name)",
    ),
}


@router.get("/pipelines")
async def list_pipelines() -> list[PipelineInfo]:
    """List all demo pipelines with their current status."""
    return list(DEMO_PIPELINES.values())


@router.get("/pipelines/{pipeline_name}")
async def get_pipeline(pipeline_name: str) -> PipelineInfo:
    """Get details for a specific pipeline."""
    if pipeline_name not in DEMO_PIPELINES:
        raise HTTPException(status_code=404, detail=f"Pipeline '{pipeline_name}' not found")
    return DEMO_PIPELINES[pipeline_name]


@router.get("/pipelines/{pipeline_name}/executions/{execution_id}")
async def get_pipeline_execution(
    pipeline_name: str, execution_id: str
) -> PipelineExecution:
    """Get details for a specific pipeline execution."""
    if pipeline_name not in DEMO_PIPELINES:
        raise HTTPException(status_code=404, detail=f"Pipeline '{pipeline_name}' not found")

    return PipelineExecution(
        pipeline_name=pipeline_name,
        execution_id=execution_id,
        status="Failed",
    )


@router.post("/pipelines/{pipeline_name}/executions/{execution_id}/diagnose")
async def diagnose_execution(
    pipeline_name: str, execution_id: str
) -> DiagnosisResponse:
    """Trigger diagnosis of a failed pipeline execution."""
    if pipeline_name not in DEMO_PIPELINES:
        raise HTTPException(status_code=404, detail=f"Pipeline '{pipeline_name}' not found")

    try:
        diagnosis = await diagnose_pipeline_failure(pipeline_name, execution_id)
        return diagnosis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diagnosis failed: {str(e)}")
