import { useState } from 'react';
import { Layout } from './components/Layout';
import { PipelineList } from './components/PipelineList';
import { PipelineDetail } from './components/PipelineDetail';
import { AnalysisPanel } from './components/AnalysisPanel';
import type { PipelineDetail as PipelineDetailType, AnalysisState, ToolInvocationStep } from './types';

/** Default MCP tool invocation steps shown during diagnosis loading */
const DEFAULT_TOOL_STEPS: ToolInvocationStep[] = [
  { id: 'pipeline-state', label: 'Retrieving pipeline state...', status: 'pending' },
  { id: 'action-details', label: 'Inspecting failed action details...', status: 'pending' },
  { id: 'repo-files', label: 'Inspecting repository files...', status: 'pending' },
  { id: 'iam-policies', label: 'Checking IAM policies...', status: 'pending' },
  { id: 'cloudwatch-logs', label: 'Reviewing CloudWatch logs...', status: 'pending' },
];

function App() {
  const [selectedPipeline, setSelectedPipeline] = useState<string>();
  const [pipelineDetail, setPipelineDetail] = useState<PipelineDetailType | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisState>({
    isLoading: false,
  });

  const handleSelectPipeline = (name: string) => {
    setSelectedPipeline(name);
    // Pipeline detail fetching will be implemented in task 5.6
    setPipelineDetail(null);
  };

  const handleAnalyze = (pipelineName: string, executionId: string) => {
    setAnalysis({
      isLoading: true,
      pipelineName,
      executionId,
      toolSteps: DEFAULT_TOOL_STEPS.map((step, i) => ({
        ...step,
        status: i === 0 ? 'in-progress' : 'pending',
      })),
    });
    // Diagnosis triggering will be implemented in task 5.6
  };

  return (
    <Layout>
      <div className="p-6 space-y-6">
        <header className="mb-4">
          <h2 className="text-xl font-bold text-aws-text">CodePipeline</h2>
          <p className="text-sm text-aws-text-secondary">
            Monitor and diagnose pipeline failures
          </p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Pipeline List */}
          <div className="lg:col-span-1">
            <PipelineList
              onSelect={handleSelectPipeline}
              selectedPipeline={selectedPipeline}
            />
          </div>

          {/* Pipeline Detail + Analysis */}
          <div className="lg:col-span-2 space-y-6">
            <PipelineDetail
              pipeline={pipelineDetail}
              onAnalyze={handleAnalyze}
            />
            <AnalysisPanel analysis={analysis} />
          </div>
        </div>
      </div>
    </Layout>
  );
}

export default App;
