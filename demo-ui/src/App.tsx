import { useState } from 'react';
import { Layout } from './components/Layout';
import type { NavPage } from './components/Layout';
import { PipelineList } from './components/PipelineList';
import { PipelineDetail } from './components/PipelineDetail';
import { AnalysisPanel } from './components/AnalysisPanel';
import { DeploymentList } from './components/DeploymentList';
import { BuildProjectList } from './components/BuildProjectList';
import { getPipelineDetail, triggerDiagnosis } from './api/client';
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
  const [activePage, setActivePage] = useState<NavPage>('pipeline');
  const [selectedPipeline, setSelectedPipeline] = useState<string>();
  const [pipelineDetail, setPipelineDetail] = useState<PipelineDetailType | null>(null);
  const [analysis, setAnalysis] = useState<AnalysisState>({
    isLoading: false,
  });

  const handleSelectPipeline = async (name: string) => {
    setSelectedPipeline(name);
    setPipelineDetail(null);
    setAnalysis({ isLoading: false });

    try {
      const detail = await getPipelineDetail(name);
      setPipelineDetail(detail);
    } catch (err) {
      console.error('Failed to fetch pipeline detail:', err);
      setPipelineDetail({
        name,
        stages: [
          { name: 'Source', status: 'Failed', actions: [] },
          { name: 'Build', status: 'Failed', actions: [] },
        ],
        executions: [],
      });
    }
  };

  const handleAnalyze = async (pipelineName: string, executionId: string) => {
    setAnalysis({
      isLoading: true,
      pipelineName,
      executionId,
      toolSteps: DEFAULT_TOOL_STEPS.map((step, i) => ({
        ...step,
        status: i === 0 ? 'in-progress' : 'pending',
      })),
    });

    try {
      const result = await triggerDiagnosis(pipelineName, executionId);
      setAnalysis({
        isLoading: false,
        pipelineName,
        executionId,
        result,
        toolSteps: DEFAULT_TOOL_STEPS.map((step) => ({
          ...step,
          status: 'complete',
        })),
      });
    } catch (err) {
      setAnalysis({
        isLoading: false,
        pipelineName,
        executionId,
        error: err instanceof Error ? err.message : 'Diagnosis failed',
        toolSteps: DEFAULT_TOOL_STEPS.map((step) => ({
          ...step,
          status: 'complete',
        })),
      });
    }
  };

  return (
    <Layout activePage={activePage} onNavigate={setActivePage}>
      {activePage === 'pipeline' && (
        <div className="space-y-6">
          <header className="mb-4">
            <h2 className="text-xl font-bold text-aws-text">Pipelines</h2>
            <p className="text-sm text-aws-text-secondary">
              Monitor and diagnose pipeline failures
            </p>
          </header>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-1">
              <PipelineList
                onSelect={handleSelectPipeline}
                selectedPipeline={selectedPipeline}
              />
            </div>
            <div className="lg:col-span-2 space-y-6">
              <PipelineDetail
                pipeline={pipelineDetail}
                onAnalyze={handleAnalyze}
              />
              <AnalysisPanel analysis={analysis} />
            </div>
          </div>
        </div>
      )}

      {activePage === 'codedeploy' && (
        <div className="space-y-6">
          <header className="mb-4">
            <h2 className="text-xl font-bold text-aws-text">Deployments</h2>
            <p className="text-sm text-aws-text-secondary">
              View recent CodeDeploy deployments
            </p>
          </header>
          <DeploymentList />
        </div>
      )}

      {activePage === 'codebuild' && (
        <div className="space-y-6">
          <header className="mb-4">
            <h2 className="text-xl font-bold text-aws-text">Build Projects</h2>
            <p className="text-sm text-aws-text-secondary">
              View CodeBuild projects and their latest build status
            </p>
          </header>
          <BuildProjectList />
        </div>
      )}
    </Layout>
  );
}

export default App;
