import { useEffect, useState } from 'react';

interface BuildProject {
  name: string;
  arn: string;
  description: string;
  source: string;
  lastModified: string;
  latestBuild: {
    buildId: string;
    status: string;
    startTime: string;
    endTime: string;
  } | null;
}

interface BuildProjectDetail {
  name: string;
  arn: string;
  description: string;
  source: { type: string; location: string; buildspec: string };
  environment: { type: string; computeType: string; image: string };
  serviceRole: string;
  lastModified: string;
  created: string;
  builds: Array<{
    buildId: string;
    buildNumber: number;
    status: string;
    startTime: string;
    endTime: string;
    sourceVersion: string;
    initiator: string;
    phases: Array<{ name: string; status: string; duration: number }>;
    logs: { groupName: string; streamName: string; deepLink: string };
  }>;
}

interface DiagnosisResult {
  root_cause_category: string;
  root_cause_description: string;
  affected_resource: string;
  recommended_fix: string;
  evidence: Array<{ source: string; finding: string }>;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function getStatusBadge(status: string) {
  const base = 'px-2 py-0.5 rounded text-xs font-semibold';
  switch (status) {
    case 'SUCCEEDED':
      return `${base} bg-green-100 text-green-800`;
    case 'FAILED':
      return `${base} bg-red-100 text-red-800`;
    case 'IN_PROGRESS':
      return `${base} bg-blue-100 text-blue-800`;
    case 'STOPPED':
      return `${base} bg-gray-100 text-gray-800`;
    default:
      return `${base} bg-gray-100 text-gray-600`;
  }
}

function BuildProjectDetailPanel({ detail }: { detail: BuildProjectDetail }) {
  const [diagnosis, setDiagnosis] = useState<DiagnosisResult | null>(null);
  const [diagnosing, setDiagnosing] = useState(false);

  const failedBuild = detail.builds.find((b) => b.status === 'FAILED');

  const handleAnalyze = () => {
    if (!failedBuild) return;
    setDiagnosing(true);
    setDiagnosis(null);
    fetch(
      `${API_BASE_URL}/api/build-projects/${encodeURIComponent(detail.name)}/builds/${encodeURIComponent(failedBuild.buildId)}/diagnose`,
      { method: 'POST' }
    )
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(setDiagnosis)
      .catch((err) => console.error('Diagnosis failed:', err))
      .finally(() => setDiagnosing(false));
  };

  return (
    <div className="aws-panel mt-4">
      <div className="aws-panel-header flex items-center justify-between">
        <span>Project: {detail.name}</span>
        {failedBuild && (
          <button
            onClick={handleAnalyze}
            disabled={diagnosing}
            className="px-3 py-1 text-xs font-semibold bg-aws-orange text-white rounded hover:bg-orange-600 disabled:opacity-50"
          >
            {diagnosing ? 'Analyzing...' : '🔍 Analyze Failed Build'}
          </button>
        )}
      </div>
      <div className="aws-panel-body space-y-4">
        {/* Project Info */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <label className="text-xs font-bold text-aws-text-secondary uppercase">Description</label>
            <p className="mt-1">{detail.description || '—'}</p>
          </div>
          <div>
            <label className="text-xs font-bold text-aws-text-secondary uppercase">Service Role</label>
            <p className="mt-1 font-mono text-xs break-all">{detail.serviceRole || '—'}</p>
          </div>
          <div>
            <label className="text-xs font-bold text-aws-text-secondary uppercase">Source Type</label>
            <p className="mt-1">{detail.source.type || '—'}</p>
          </div>
          <div>
            <label className="text-xs font-bold text-aws-text-secondary uppercase">Source Location</label>
            <p className="mt-1 text-xs break-all">{detail.source.location || '—'}</p>
          </div>
          <div>
            <label className="text-xs font-bold text-aws-text-secondary uppercase">Environment</label>
            <p className="mt-1">{detail.environment.computeType} / {detail.environment.type}</p>
          </div>
          <div>
            <label className="text-xs font-bold text-aws-text-secondary uppercase">Image</label>
            <p className="mt-1 text-xs break-all">{detail.environment.image || '—'}</p>
          </div>
          <div>
            <label className="text-xs font-bold text-aws-text-secondary uppercase">Created</label>
            <p className="mt-1">{detail.created ? new Date(detail.created).toLocaleString() : '—'}</p>
          </div>
          <div>
            <label className="text-xs font-bold text-aws-text-secondary uppercase">Last Modified</label>
            <p className="mt-1">{detail.lastModified ? new Date(detail.lastModified).toLocaleString() : '—'}</p>
          </div>
        </div>

        {/* Recent Builds */}
        {detail.builds.length > 0 && (
          <div>
            <label className="text-xs font-bold text-aws-text-secondary uppercase">Recent Builds</label>
            <div className="mt-2">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-aws-border bg-gray-50">
                    <th className="text-left px-3 py-1.5 font-semibold text-aws-text-secondary text-xs">Build</th>
                    <th className="text-left px-3 py-1.5 font-semibold text-aws-text-secondary text-xs">Status</th>
                    <th className="text-left px-3 py-1.5 font-semibold text-aws-text-secondary text-xs">Initiator</th>
                    <th className="text-left px-3 py-1.5 font-semibold text-aws-text-secondary text-xs">Started</th>
                  </tr>
                </thead>
                <tbody>
                  {detail.builds.map((build) => (
                    <tr key={build.buildId} className="border-b border-aws-border">
                      <td className="px-3 py-1.5 font-mono text-xs">#{build.buildNumber || build.buildId.split(':').pop()}</td>
                      <td className="px-3 py-1.5">
                        <span className={getStatusBadge(build.status)}>{build.status}</span>
                      </td>
                      <td className="px-3 py-1.5 text-xs text-aws-text-secondary">{build.initiator || '—'}</td>
                      <td className="px-3 py-1.5 text-xs text-aws-text-secondary">
                        {build.startTime ? new Date(build.startTime).toLocaleString() : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Build Phases for latest build */}
        {detail.builds.length > 0 && detail.builds[0].phases.length > 0 && (
          <div>
            <label className="text-xs font-bold text-aws-text-secondary uppercase">Latest Build Phases</label>
            <div className="mt-2 flex flex-wrap gap-2">
              {detail.builds[0].phases
                .filter((p) => p.name && p.name !== 'COMPLETED' && p.name !== 'QUEUED')
                .map((phase, i) => (
                  <div key={i} className="flex items-center gap-1.5 px-2 py-1 bg-gray-50 border rounded text-xs">
                    <span className={getStatusBadge(phase.status)}>{phase.status || '—'}</span>
                    <span>{phase.name}</span>
                    {phase.duration > 0 && (
                      <span className="text-aws-text-secondary">({phase.duration}s)</span>
                    )}
                  </div>
                ))}
            </div>
          </div>
        )}

        {/* Diagnosis Result */}
        {diagnosing && (
          <div className="p-4 bg-orange-50 border border-orange-200 rounded flex items-center gap-3">
            <div className="w-5 h-5 border-2 border-aws-orange border-t-transparent rounded-full animate-spin" />
            <span className="text-sm text-aws-text">Analyzing build failure with MCP servers...</span>
          </div>
        )}
        {diagnosis && (
          <div className="space-y-3 p-4 bg-blue-50 border border-blue-200 rounded">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-blue-700 uppercase">Diagnosis</span>
              <span className="px-2 py-0.5 rounded text-xs font-semibold bg-blue-100 text-blue-800">
                {diagnosis.root_cause_category}
              </span>
            </div>
            <p className="text-sm text-aws-text">{diagnosis.root_cause_description}</p>
            <div>
              <span className="text-xs font-bold text-aws-text-secondary">Affected Resource: </span>
              <code className="text-xs font-mono">{diagnosis.affected_resource}</code>
            </div>
            <div>
              <span className="text-xs font-bold text-aws-text-secondary">Recommended Fix:</span>
              <p className="text-sm mt-1 whitespace-pre-wrap">{diagnosis.recommended_fix}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export function BuildProjectList() {
  const [projects, setProjects] = useState<BuildProject[]>([]);
  const [selectedDetail, setSelectedDetail] = useState<BuildProjectDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState<string>();

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/build-projects`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(setProjects)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const handleSelectProject = (projectName: string) => {
    setDetailLoading(true);
    setSelectedDetail(null);
    fetch(`${API_BASE_URL}/api/build-projects/${encodeURIComponent(projectName)}`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(setSelectedDetail)
      .catch((err) => console.error('Failed to fetch project detail:', err))
      .finally(() => setDetailLoading(false));
  };

  if (loading) {
    return (
      <div className="aws-panel">
        <div className="aws-panel-header">Build Projects</div>
        <div className="aws-panel-body p-8 text-center text-aws-text-secondary">
          Loading build projects...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="aws-panel">
        <div className="aws-panel-header">Build Projects</div>
        <div className="aws-panel-body p-4 text-red-600 text-sm">Error: {error}</div>
      </div>
    );
  }

  return (
    <div>
      <div className="aws-panel">
        <div className="aws-panel-header flex items-center justify-between">
          <span>Build Projects</span>
          <span className="text-xs font-normal text-aws-text-secondary">{projects.length} projects</span>
        </div>
        <div className="aws-panel-body p-0">
          {projects.length === 0 ? (
            <div className="p-6 text-center text-aws-text-secondary text-sm">
              No build projects found
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-aws-border bg-gray-50">
                  <th className="text-left px-4 py-2 font-semibold text-aws-text-secondary">Project Name</th>
                  <th className="text-left px-4 py-2 font-semibold text-aws-text-secondary">Source</th>
                  <th className="text-left px-4 py-2 font-semibold text-aws-text-secondary">Latest Build</th>
                  <th className="text-left px-4 py-2 font-semibold text-aws-text-secondary">Last Modified</th>
                </tr>
              </thead>
              <tbody>
                {projects.map((proj) => (
                  <tr
                    key={proj.name}
                    className="border-b border-aws-border hover:bg-blue-50 cursor-pointer"
                    onClick={() => handleSelectProject(proj.name)}
                  >
                    <td className="px-4 py-2">
                      <div className="font-medium text-aws-link">{proj.name}</div>
                      {proj.description && (
                        <div className="text-xs text-aws-text-secondary mt-0.5">{proj.description}</div>
                      )}
                    </td>
                    <td className="px-4 py-2 text-aws-text-secondary">{proj.source || '—'}</td>
                    <td className="px-4 py-2">
                      {proj.latestBuild ? (
                        <span className={getStatusBadge(proj.latestBuild.status)}>
                          {proj.latestBuild.status}
                        </span>
                      ) : (
                        <span className="text-xs text-aws-text-secondary">No builds</span>
                      )}
                    </td>
                    <td className="px-4 py-2 text-aws-text-secondary text-xs">
                      {proj.lastModified ? new Date(proj.lastModified).toLocaleString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Detail Panel */}
      {detailLoading && (
        <div className="mt-4 aws-panel">
          <div className="aws-panel-body p-8 text-center text-aws-text-secondary">Loading project details...</div>
        </div>
      )}
      {selectedDetail && <BuildProjectDetailPanel detail={selectedDetail} />}
    </div>
  );
}
