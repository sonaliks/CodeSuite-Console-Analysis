/** Pipeline execution status */
export type PipelineStatus = 'Succeeded' | 'Failed' | 'InProgress' | 'Stopped' | 'Superseded';

/** Stage execution status */
export type StageStatus = 'Succeeded' | 'Failed' | 'InProgress' | 'Stopped';

/** Action execution status */
export type ActionStatus = 'Succeeded' | 'Failed' | 'InProgress' | 'Abandoned';

/** Root cause category from diagnosis */
export type RootCauseCategory = 'Configuration Issue' | 'Permission Issue' | 'Infrastructure Issue';

/** Evidence item from diagnosis */
export interface DiagnosisEvidence {
  source: string;
  finding: string;
}

/** Diagnosis result from the Bedrock Agent */
export interface DiagnosisResult {
  root_cause_category: RootCauseCategory;
  root_cause_description: string;
  affected_resource: string;
  recommended_fix: string;
  evidence: DiagnosisEvidence[];
}

/** Pipeline action within a stage */
export interface PipelineAction {
  name: string;
  status: ActionStatus;
  lastStatusChange?: string;
  errorMessage?: string;
}

/** Pipeline stage */
export interface PipelineStage {
  name: string;
  status: StageStatus;
  actions: PipelineAction[];
}

/** Pipeline execution summary */
export interface PipelineExecution {
  executionId: string;
  status: PipelineStatus;
  startTime: string;
  lastUpdateTime?: string;
  trigger?: string;
}

/** Pipeline summary for list view */
export interface PipelineSummary {
  name: string;
  latestExecution?: PipelineExecution;
  stages: PipelineStage[];
}

/** Pipeline detail with full execution history */
export interface PipelineDetail {
  name: string;
  stages: PipelineStage[];
  executions: PipelineExecution[];
}

/** API response wrapper */
export interface ApiResponse<T> {
  data: T;
  error?: string;
}

/** Loading state for async operations */
export interface LoadingState {
  isLoading: boolean;
  error?: string;
}

/** MCP tool invocation step shown during loading */
export type ToolStepStatus = 'pending' | 'in-progress' | 'complete' | 'completed';

export interface ToolInvocationStep {
  id: string;
  label: string;
  status: ToolStepStatus;
}

/** Analysis panel state */
export interface AnalysisState extends LoadingState {
  result?: DiagnosisResult;
  pipelineName?: string;
  executionId?: string;
  toolSteps?: ToolInvocationStep[];
}
