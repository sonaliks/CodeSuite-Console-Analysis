import type { PipelineDetail as PipelineDetailType } from '../types';
import { StageVisualization } from './StageVisualization';

interface PipelineDetailProps {
  pipeline: PipelineDetailType | null;
  onAnalyze: (pipelineName: string, executionId: string) => void;
}

export function PipelineDetail({ pipeline, onAnalyze }: PipelineDetailProps) {
  if (!pipeline) {
    return (
      <div className="aws-panel">
        <div className="aws-panel-body text-center text-aws-text-secondary">
          <p>Select a pipeline to view details</p>
        </div>
      </div>
    );
  }

  return (
    <div className="aws-panel">
      <div className="aws-panel-header">{pipeline.name}</div>
      <div className="aws-panel-body space-y-6">
        {/* Stage Visualization */}
        <StageVisualization stages={pipeline.stages} />

        {/* Execution History */}
        <div>
          <h3 className="text-sm font-bold mb-2 text-aws-text-primary">
            Execution History
          </h3>
          <ul className="divide-y divide-aws-border-secondary">
            {pipeline.executions.map((execution) => (
              <li
                key={execution.executionId}
                className="py-2 flex items-center justify-between"
              >
                <div>
                  <span className="text-sm font-mono text-aws-text-secondary">
                    {execution.executionId.slice(0, 8)}...
                  </span>
                  <span className="ml-2 text-xs text-aws-text-tertiary">
                    {execution.startTime}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`status-badge status-badge--${execution.status.toLowerCase()}`}
                  >
                    {execution.status}
                  </span>
                  {execution.status === 'Failed' && (
                    <button
                      className="aws-btn-primary text-xs"
                      onClick={() => onAnalyze(pipeline.name, execution.executionId)}
                    >
                      Analyze
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
