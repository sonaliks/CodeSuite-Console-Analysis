import type React from 'react';
import type { AnalysisState, RootCauseCategory, ToolInvocationStep } from '../types';

/** Map tool names to their MCP server */
const TOOL_TO_SERVER: Record<string, { name: string; description: string }> = {
  get_pipeline_state: { name: 'CodePipeline MCP', description: 'Custom - Pipeline state & actions' },
  get_pipeline_execution: { name: 'CodePipeline MCP', description: 'Custom - Pipeline state & actions' },
  get_pipeline_configuration: { name: 'CodePipeline MCP', description: 'Custom - Pipeline state & actions' },
  get_action_execution_details: { name: 'CodePipeline MCP', description: 'Custom - Pipeline state & actions' },
  list_pipeline_executions: { name: 'CodePipeline MCP', description: 'Custom - Pipeline state & actions' },
  list_files: { name: 'CodeCommit MCP', description: 'Custom - Repository file access' },
  get_file_content: { name: 'CodeCommit MCP', description: 'Custom - Repository file access' },
  get_repository_metadata: { name: 'CodeCommit MCP', description: 'Custom - Repository file access' },
  get_role: { name: 'IAM MCP (AWS Labs)', description: 'Pre-built - IAM policy inspection' },
  get_role_policy: { name: 'IAM MCP (AWS Labs)', description: 'Pre-built - IAM policy inspection' },
  list_attached_role_policies: { name: 'IAM MCP (AWS Labs)', description: 'Pre-built - IAM policy inspection' },
  get_policy_version: { name: 'IAM MCP (AWS Labs)', description: 'Pre-built - IAM policy inspection' },
  get_log_events: { name: 'CloudWatch MCP (AWS Labs)', description: 'Pre-built - Log retrieval' },
  filter_log_events: { name: 'CloudWatch MCP (AWS Labs)', description: 'Pre-built - Log retrieval' },
  describe_log_groups: { name: 'CloudWatch MCP (AWS Labs)', description: 'Pre-built - Log retrieval' },
};

function getServerForTool(toolName: string): string {
  const server = TOOL_TO_SERVER[toolName];
  if (server) return server.name;
  if (toolName.includes('pipeline') || toolName.includes('execution')) return 'CodePipeline MCP';
  if (toolName.includes('file') || toolName.includes('repo') || toolName.includes('commit')) return 'CodeCommit MCP';
  if (toolName.includes('iam') || toolName.includes('role') || toolName.includes('policy')) return 'IAM MCP (AWS Labs)';
  if (toolName.includes('log') || toolName.includes('cloudwatch')) return 'CloudWatch MCP (AWS Labs)';
  return 'MCP Server';
}

function getUniqueServers(toolNames: string[]): Array<{ name: string; description: string }> {
  const seen = new Set<string>();
  const servers: Array<{ name: string; description: string }> = [];
  for (const tool of toolNames) {
    const server = TOOL_TO_SERVER[tool] || { name: getServerForTool(tool), description: 'Tool provider' };
    if (!seen.has(server.name)) {
      seen.add(server.name);
      servers.push(server);
    }
  }
  return servers;
}

interface AnalysisPanelProps {
  analysis: AnalysisState;
}

/** Returns Tailwind classes for the category badge based on root cause type */
function getCategoryBadgeClasses(category: RootCauseCategory): string {
  switch (category) {
    case 'Configuration Issue':
      return 'bg-amber-50 text-amber-800 border border-amber-300';
    case 'Permission Issue':
      return 'bg-red-50 text-red-800 border border-red-300';
    case 'Infrastructure Issue':
      return 'bg-blue-50 text-blue-800 border border-blue-300';
    default:
      return 'bg-gray-50 text-gray-800 border border-gray-300';
  }
}

/** Returns an icon character for the category badge */
function getCategoryIcon(category: RootCauseCategory): string {
  switch (category) {
    case 'Configuration Issue':
      return '⚙';
    case 'Permission Issue':
      return '🔒';
    case 'Infrastructure Issue':
      return '🏗';
    default:
      return '•';
  }
}

/**
 * Parses text containing markdown-style code blocks (```...```) and returns
 * an array of segments, each either plain text or a code block.
 */
function parseCodeBlocks(text: string): Array<{ type: 'text' | 'code'; content: string; language?: string }> {
  const segments: Array<{ type: 'text' | 'code'; content: string; language?: string }> = [];
  const codeBlockRegex = /```(\w*)\n?([\s\S]*?)```/g;

  let lastIndex = 0;
  let match: RegExpExecArray | null;

  while ((match = codeBlockRegex.exec(text)) !== null) {
    // Add text before the code block
    if (match.index > lastIndex) {
      const textContent = text.slice(lastIndex, match.index).trim();
      if (textContent) {
        segments.push({ type: 'text', content: textContent });
      }
    }

    // Add the code block
    segments.push({
      type: 'code',
      content: match[2].trim(),
      language: match[1] || undefined,
    });

    lastIndex = match.index + match[0].length;
  }

  // Add remaining text after the last code block
  if (lastIndex < text.length) {
    const remaining = text.slice(lastIndex).trim();
    if (remaining) {
      segments.push({ type: 'text', content: remaining });
    }
  }

  // If no code blocks were found, return the whole text as a single segment
  if (segments.length === 0) {
    segments.push({ type: 'text', content: text });
  }

  return segments;
}

/** Renders the recommended fix with code block support */
function RecommendedFix({ text }: { text: string }) {
  const segments = parseCodeBlocks(text);

  return (
    <div className="space-y-3">
      {segments.map((segment, index) => {
        if (segment.type === 'code') {
          return (
            <div key={index} className="relative">
              {segment.language && (
                <div className="absolute top-0 right-0 px-2 py-0.5 text-[10px] font-mono uppercase tracking-wider text-gray-400 bg-gray-800 rounded-bl rounded-tr">
                  {segment.language}
                </div>
              )}
              <pre className="bg-[#1e1e1e] text-gray-100 p-4 rounded-md overflow-x-auto text-sm font-mono leading-relaxed border border-gray-700">
                <code>{segment.content}</code>
              </pre>
            </div>
          );
        }
        return (
          <div key={index} className="text-sm text-aws-text leading-relaxed">
            {segment.content.split('\n').map((line, lineIndex) => {
              // Handle markdown headers
              if (line.startsWith('### ')) {
                return <h4 key={lineIndex} className="font-bold text-aws-text mt-3 mb-1">{line.replace(/^###\s*\*?\*?/, '').replace(/\*?\*?\s*$/, '')}</h4>;
              }
              if (line.startsWith('## ')) {
                return <h3 key={lineIndex} className="font-bold text-aws-text mt-4 mb-1 text-base">{line.replace(/^##\s*\*?\*?/, '').replace(/\*?\*?\s*$/, '')}</h3>;
              }
              // Handle bullet points
              if (line.match(/^\s*[-*]\s/)) {
                return <li key={lineIndex} className="ml-4 list-disc text-sm">{renderInlineMarkdown(line.replace(/^\s*[-*]\s/, ''))}</li>;
              }
              // Handle numbered lists
              if (line.match(/^\s*\d+\.\s/)) {
                return <li key={lineIndex} className="ml-4 list-decimal text-sm">{renderInlineMarkdown(line.replace(/^\s*\d+\.\s/, ''))}</li>;
              }
              // Empty lines become spacing
              if (line.trim() === '') {
                return <div key={lineIndex} className="h-2" />;
              }
              // Regular text
              return <p key={lineIndex} className="text-sm">{renderInlineMarkdown(line)}</p>;
            })}
          </div>
        );
      })}
    </div>
  );
}

/** Renders inline markdown (bold, code, etc.) within a line */
function renderInlineMarkdown(text: string): React.ReactNode {
  // Split by bold markers (**text**) and inline code (`text`)
  const parts = text.split(/(\*\*[^*]+\*\*|`[^`]+`)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <strong key={i} className="font-semibold">{part.slice(2, -2)}</strong>;
    }
    if (part.startsWith('`') && part.endsWith('`')) {
      return <code key={i} className="bg-gray-200 px-1 py-0.5 rounded text-xs font-mono">{part.slice(1, -1)}</code>;
    }
    return <span key={i}>{part}</span>;
  });
}

/** Calculates progress bar width based on completed tool steps */
function getProgressWidth(toolSteps?: ToolInvocationStep[]): string {
  if (!toolSteps || toolSteps.length === 0) return '10%';
  const completed = toolSteps.filter((s) => s.status === 'completed').length;
  const inProgress = toolSteps.filter((s) => s.status === 'in-progress').length;
  const total = toolSteps.length;
  const progress = ((completed + inProgress * 0.5) / total) * 100;
  return `${Math.max(10, Math.min(95, progress))}%`;
}

/** Renders a single tool invocation step with appropriate status icon and animation */
function ToolStep({ step }: { step: ToolInvocationStep }) {
  return (
    <div className="flex items-center gap-3 py-1.5">
      {step.status === 'completed' && (
        <svg className="w-4 h-4 text-aws-success flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      )}
      {step.status === 'in-progress' && (
        <div className="w-4 h-4 flex-shrink-0">
          <div className="w-4 h-4 border-2 border-aws-orange border-t-transparent rounded-full animate-spin" />
        </div>
      )}
      {step.status === 'pending' && (
        <div className="w-4 h-4 flex-shrink-0 flex items-center justify-center">
          <div className="w-2 h-2 rounded-full bg-gray-300" />
        </div>
      )}
      <span
        className={`text-sm ${
          step.status === 'completed'
            ? 'text-aws-text-secondary'
            : step.status === 'in-progress'
            ? 'text-aws-text font-medium'
            : 'text-aws-text-tertiary'
        }`}
      >
        {step.label}
      </span>
    </div>
  );
}

/** Animated pulsing dots for the "Analyzing" header */
function PulsingDots() {
  return (
    <span className="inline-flex gap-0.5 ml-1">
      <span className="w-1 h-1 rounded-full bg-aws-orange animate-bounce" style={{ animationDelay: '0ms' }} />
      <span className="w-1 h-1 rounded-full bg-aws-orange animate-bounce" style={{ animationDelay: '150ms' }} />
      <span className="w-1 h-1 rounded-full bg-aws-orange animate-bounce" style={{ animationDelay: '300ms' }} />
    </span>
  );
}

export function AnalysisPanel({ analysis }: AnalysisPanelProps) {
  if (!analysis.pipelineName && !analysis.isLoading) {
    return null;
  }

  return (
    <div className="aws-panel">
      <div className="aws-panel-header flex items-center gap-2">
        <svg className="w-5 h-5 text-aws-orange" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
        </svg>
        <span>Diagnosis Results</span>
        {analysis.pipelineName && (
          <span className="ml-auto text-sm font-normal text-aws-text-secondary">
            {analysis.pipelineName}
          </span>
        )}
      </div>

      <div className="aws-panel-body">
        {/* Loading State with MCP Tool Progress */}
        {analysis.isLoading && (
          <div className="space-y-4 py-2">
            {/* Animated header */}
            <div className="flex items-center gap-3">
              <div className="w-5 h-5 border-2 border-aws-orange border-t-transparent rounded-full animate-spin" />
              <span className="text-sm text-aws-text font-semibold">
                Analyzing pipeline failure
                <PulsingDots />
              </span>
            </div>

            {/* Tool invocation steps */}
            {analysis.toolSteps && analysis.toolSteps.length > 0 && (
              <div className="ml-2 pl-4 border-l-2 border-aws-border-secondary space-y-0.5">
                {analysis.toolSteps.map((step) => (
                  <ToolStep key={step.id} step={step} />
                ))}
              </div>
            )}

            {/* Fallback when no tool steps are provided yet */}
            {(!analysis.toolSteps || analysis.toolSteps.length === 0) && (
              <div className="ml-2 pl-4 border-l-2 border-aws-border-secondary">
                <div className="flex items-center gap-3 py-1.5">
                  <div className="w-4 h-4 border-2 border-aws-info border-t-transparent rounded-full animate-spin" />
                  <span className="text-sm text-aws-text-secondary">
                    Connecting to diagnostic agent...
                  </span>
                </div>
              </div>
            )}

            {/* Progress bar */}
            <div className="mt-3">
              <div className="h-1 w-full bg-gray-100 rounded-full overflow-hidden">
                <div className="h-full bg-aws-orange rounded-full animate-pulse" style={{ width: getProgressWidth(analysis.toolSteps) }} />
              </div>
            </div>
          </div>
        )}

        {/* Error State */}
        {analysis.error && (
          <div className="flex items-start gap-2 text-sm p-3 bg-red-50 rounded border border-red-200">
            <span className="text-aws-error font-bold mt-0.5">✕</span>
            <span className="text-aws-error">{analysis.error}</span>
          </div>
        )}

        {/* Diagnosis Results */}
        {analysis.result && (
          <div className="space-y-5">
            {/* Root Cause Category Badge */}
            <div>
              <label className="text-xs font-bold text-aws-text-secondary uppercase tracking-wide">
                Root Cause Category
              </label>
              <div className="mt-2">
                <span
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-semibold ${getCategoryBadgeClasses(analysis.result.root_cause_category)}`}
                >
                  <span>{getCategoryIcon(analysis.result.root_cause_category)}</span>
                  {analysis.result.root_cause_category}
                </span>
              </div>
            </div>

            {/* Root Cause Description */}
            <div>
              <label className="text-xs font-bold text-aws-text-secondary uppercase tracking-wide">
                Description
              </label>
              <div className="mt-2 text-sm text-aws-text leading-relaxed prose prose-sm max-w-none">
                <RecommendedFix text={analysis.result.root_cause_description} />
              </div>
            </div>

            {/* Affected Resource */}
            <div>
              <label className="text-xs font-bold text-aws-text-secondary uppercase tracking-wide">
                Affected Resource
              </label>
              <div className="mt-2 flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-md px-3 py-2">
                <svg className="w-4 h-4 text-aws-text-secondary flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2" />
                </svg>
                <code className="text-sm font-mono text-aws-text break-all">
                  {analysis.result.affected_resource}
                </code>
              </div>
            </div>

            {/* Recommended Fix */}
            <div>
              <label className="text-xs font-bold text-aws-text-secondary uppercase tracking-wide">
                Recommended Fix
              </label>
              <div className="mt-2 p-4 bg-gray-50 border border-gray-200 rounded-md">
                <RecommendedFix text={analysis.result.recommended_fix} />
              </div>
            </div>

            {/* Evidence */}
            {analysis.result.evidence && analysis.result.evidence.length > 0 && (
              <div>
                <label className="text-xs font-bold text-aws-text-secondary uppercase tracking-wide">
                  Evidence
                </label>
                <div className="mt-2 space-y-2">
                  {analysis.result.evidence.map((item, index) => (
                    <div
                      key={index}
                      className="flex items-start gap-3 p-3 bg-gray-50 border border-gray-200 rounded-md"
                    >
                      <span className="inline-flex items-center justify-center w-5 h-5 rounded bg-aws-nav text-white text-[10px] font-bold flex-shrink-0 mt-0.5">
                        {index + 1}
                      </span>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-semibold text-aws-text-secondary uppercase tracking-wide">
                            {item.source}
                          </span>
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200 font-medium">
                            {getServerForTool(item.source)}
                          </span>
                        </div>
                        <p className="text-sm text-aws-text mt-0.5 leading-relaxed">
                          {item.finding}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* MCP Servers Used */}
            {analysis.result.evidence && analysis.result.evidence.length > 0 && (
              <div>
                <label className="text-xs font-bold text-aws-text-secondary uppercase tracking-wide">
                  MCP Servers Used
                </label>
                <div className="mt-2 flex flex-wrap gap-2">
                  {getUniqueServers(analysis.result.evidence.map(e => e.source)).map((server) => (
                    <div
                      key={server.name}
                      className="flex items-center gap-2 px-3 py-2 bg-indigo-50 border border-indigo-200 rounded-md"
                    >
                      <div className="w-2 h-2 rounded-full bg-indigo-500" />
                      <div>
                        <div className="text-xs font-semibold text-indigo-800">{server.name}</div>
                        <div className="text-[10px] text-indigo-600">{server.description}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
