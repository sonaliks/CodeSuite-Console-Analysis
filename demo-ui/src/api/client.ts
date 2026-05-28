import type {
  PipelineSummary,
  PipelineDetail,
  PipelineExecution,
  DiagnosisResult,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${url}`, {
    headers: {
      'Content-Type': 'application/json',
    },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

/** Fetch all pipelines with their latest execution status */
export async function getPipelines(): Promise<PipelineSummary[]> {
  return fetchJson<PipelineSummary[]>('/api/pipelines');
}

/** Fetch pipeline detail with stages and execution history */
export async function getPipelineDetail(name: string): Promise<PipelineDetail> {
  return fetchJson<PipelineDetail>(`/api/pipelines/${encodeURIComponent(name)}`);
}

/** Fetch a specific execution */
export async function getExecution(
  pipelineName: string,
  executionId: string
): Promise<PipelineExecution> {
  return fetchJson<PipelineExecution>(
    `/api/pipelines/${encodeURIComponent(pipelineName)}/executions/${encodeURIComponent(executionId)}`
  );
}

/** Trigger diagnosis for a failed execution */
export async function triggerDiagnosis(
  pipelineName: string,
  executionId: string
): Promise<DiagnosisResult> {
  return fetchJson<DiagnosisResult>(
    `/api/pipelines/${encodeURIComponent(pipelineName)}/executions/${encodeURIComponent(executionId)}/diagnose`,
    { method: 'POST' }
  );
}
