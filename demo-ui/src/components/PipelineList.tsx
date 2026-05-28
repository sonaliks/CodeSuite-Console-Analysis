import { useState, useEffect } from 'react';
import { getPipelines } from '../api/client';
import type { PipelineSummary, PipelineStatus } from '../types';

interface PipelineListProps {
  onSelect: (pipelineName: string) => void;
  selectedPipeline?: string;
}

/** Map pipeline status to color-coded indicator styles */
function getStatusStyles(status: PipelineStatus): { bg: string; text: string; dot: string } {
  switch (status) {
    case 'Succeeded':
      return { bg: 'bg-green-50', text: 'text-aws-success', dot: 'bg-aws-success' };
    case 'Failed':
      return { bg: 'bg-red-50', text: 'text-aws-error', dot: 'bg-aws-error' };
    case 'InProgress':
      return { bg: 'bg-blue-50', text: 'text-aws-info', dot: 'bg-aws-info' };
    case 'Stopped':
      return { bg: 'bg-yellow-50', text: 'text-aws-warning', dot: 'bg-aws-warning' };
    case 'Superseded':
      return { bg: 'bg-gray-50', text: 'text-gray-500', dot: 'bg-gray-400' };
    default:
      return { bg: 'bg-gray-50', text: 'text-gray-500', dot: 'bg-gray-400' };
  }
}

/** Format a status label for display */
function formatStatus(status: PipelineStatus): string {
  switch (status) {
    case 'InProgress':
      return 'In Progress';
    default:
      return status;
  }
}

export function PipelineList({ onSelect, selectedPipeline }: PipelineListProps) {
  const [pipelines, setPipelines] = useState<PipelineSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | undefined>();

  useEffect(() => {
    let cancelled = false;

    async function fetchPipelines() {
      setIsLoading(true);
      setError(undefined);

      try {
        const data = await getPipelines();
        if (!cancelled) {
          setPipelines(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load pipelines');
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    fetchPipelines();

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="aws-panel">
      <div className="aws-panel-header flex items-center justify-between">
        <span>Pipelines</span>
        <span className="text-xs font-normal text-aws-text-secondary">
          {!isLoading && !error && `${pipelines.length} pipeline${pipelines.length !== 1 ? 's' : ''}`}
        </span>
      </div>
      <div className="aws-panel-body p-0">
        {isLoading && (
          <div className="flex items-center justify-center py-8">
            <div className="flex items-center gap-2 text-aws-text-secondary text-sm">
              <svg
                className="animate-spin h-4 w-4 text-aws-info"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                />
              </svg>
              <span>Loading pipelines...</span>
            </div>
          </div>
        )}

        {error && (
          <div className="p-4">
            <div className="rounded border border-aws-error bg-red-50 p-3">
              <div className="flex items-start gap-2">
                <svg
                  className="h-4 w-4 text-aws-error mt-0.5 shrink-0"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                  aria-hidden="true"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z"
                    clipRule="evenodd"
                  />
                </svg>
                <div>
                  <p className="text-sm font-medium text-aws-error">Error loading pipelines</p>
                  <p className="text-xs text-aws-text-secondary mt-1">{error}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {!isLoading && !error && pipelines.length === 0 && (
          <div className="flex flex-col items-center justify-center py-8 text-center px-4">
            <svg
              className="h-10 w-10 text-gray-300 mb-2"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z"
              />
            </svg>
            <p className="text-sm text-aws-text-secondary">No pipelines found.</p>
            <p className="text-xs text-gray-400 mt-1">Pipelines will appear here once configured.</p>
          </div>
        )}

        {!isLoading && !error && pipelines.length > 0 && (
          <ul className="divide-y divide-aws-border" role="list" aria-label="Pipeline list">
            {pipelines.map((pipeline) => {
              const isSelected = selectedPipeline === pipeline.name;
              const execution = pipeline.latestExecution;
              const statusStyles = execution
                ? getStatusStyles(execution.status)
                : null;

              return (
                <li
                  key={pipeline.name}
                  role="button"
                  tabIndex={0}
                  aria-selected={isSelected}
                  className={`px-4 py-3 cursor-pointer transition-colors ${
                    isSelected
                      ? 'bg-blue-50 border-l-[3px] border-l-aws-info'
                      : 'hover:bg-gray-50'
                  }`}
                  onClick={() => onSelect(pipeline.name)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      onSelect(pipeline.name);
                    }
                  }}
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <p className="font-medium text-sm text-aws-text truncate">
                        {pipeline.name}
                      </p>
                      {execution?.lastUpdateTime && (
                        <p className="text-xs text-aws-text-secondary mt-0.5">
                          Last run: {new Date(execution.lastUpdateTime).toLocaleDateString()}
                        </p>
                      )}
                    </div>

                    {execution && statusStyles ? (
                      <div
                        className={`inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs font-semibold ${statusStyles.bg} ${statusStyles.text}`}
                      >
                        <span
                          className={`h-2 w-2 rounded-full ${statusStyles.dot} ${
                            execution.status === 'InProgress' ? 'animate-pulse' : ''
                          }`}
                          aria-hidden="true"
                        />
                        {formatStatus(execution.status)}
                      </div>
                    ) : (
                      <div className="inline-flex items-center gap-1.5 px-2 py-1 rounded text-xs font-semibold bg-gray-50 text-gray-500">
                        <span className="h-2 w-2 rounded-full bg-gray-400" aria-hidden="true" />
                        Not started
                      </div>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}
