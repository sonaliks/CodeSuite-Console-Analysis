import type { PipelineStage, PipelineAction, ActionStatus } from '../types';

interface StageVisualizationProps {
  stages: PipelineStage[];
}

export function StageVisualization({ stages }: StageVisualizationProps) {
  return (
    <div>
      <h3 className="text-sm font-bold mb-3 text-aws-text-primary">Pipeline Stages</h3>
      <div className="flex items-start gap-2 overflow-x-auto pb-2">
        {stages.map((stage, index) => (
          <div key={stage.name} className="flex items-start">
            {/* Stage box */}
            <div
              className={`rounded border text-xs font-medium min-w-[140px] ${getStageStyles(stage.status)}`}
            >
              {/* Stage header */}
              <div className="px-4 py-2 border-b border-inherit text-center">
                <div className="font-bold">{stage.name}</div>
                <div className="mt-0.5 opacity-75">{stage.status}</div>
              </div>
              {/* Actions within stage */}
              {stage.actions.length > 0 && (
                <div className="px-3 py-2 space-y-1.5">
                  {stage.actions.map((action) => (
                    <ActionItem key={action.name} action={action} />
                  ))}
                </div>
              )}
            </div>
            {/* Arrow connector */}
            {index < stages.length - 1 && (
              <div className="mx-2 mt-4 text-aws-text-secondary text-lg">→</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function ActionItem({ action }: { action: PipelineAction }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className={`inline-block w-2 h-2 rounded-full flex-shrink-0 ${getActionDotColor(action.status)}`} />
      <span className="truncate" title={action.name}>{action.name}</span>
      {action.errorMessage && (
        <span
          className="ml-auto text-red-600 cursor-help flex-shrink-0"
          title={action.errorMessage}
        >
          ⚠
        </span>
      )}
    </div>
  );
}

function getStageStyles(status: string): string {
  switch (status) {
    case 'Succeeded':
      return 'border-green-600 bg-green-50 text-green-800';
    case 'Failed':
      return 'border-red-600 bg-red-50 text-red-800';
    case 'InProgress':
      return 'border-blue-600 bg-blue-50 text-blue-800';
    default:
      return 'border-gray-300 bg-gray-50 text-gray-600';
  }
}

function getActionDotColor(status: ActionStatus): string {
  switch (status) {
    case 'Succeeded':
      return 'bg-green-500';
    case 'Failed':
      return 'bg-red-500';
    case 'InProgress':
      return 'bg-blue-500';
    case 'Abandoned':
      return 'bg-gray-400';
    default:
      return 'bg-gray-400';
  }
}
