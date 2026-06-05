import { useEffect, useState } from 'react';

interface Deployment {
  deploymentId: string;
  applicationName: string;
  deploymentGroupName: string;
  status: string;
  createTime: string;
  completeTime: string;
  description: string;
  errorInformation: { code?: string; message?: string };
}

interface DeploymentDetail {
  deploymentId: string;
  applicationName: string;
  deploymentGroupName: string;
  status: string;
  createTime: string;
  completeTime: string;
  description: string;
  errorInformation: { code?: string; message?: string };
  deploymentOverview: Record<string, number>;
  computePlatform: string;
  creator: string;
  targets: Array<{
    targetId: string;
    status: string;
    lifecycleEvents: Array<{
      name: string;
      status: string;
      startTime: string;
      endTime: string;
      diagnostics: { errorCode?: string; message?: string };
    }>;
  }>;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function getStatusBadge(status: string) {
  const base = 'px-2 py-0.5 rounded text-xs font-semibold';
  switch (status) {
    case 'Succeeded':
      return `${base} bg-green-100 text-green-800`;
    case 'Failed':
      return `${base} bg-red-100 text-red-800`;
    case 'InProgress':
      return `${base} bg-blue-100 text-blue-800`;
    case 'Stopped':
      return `${base} bg-gray-100 text-gray-800`;
    default:
      return `${base} bg-gray-100 text-gray-600`;
  }
}

function DeploymentDetailPanel({ detail }: { detail: DeploymentDetail }) {
  return (
    <div className="aws-panel mt-4">
      <div className="aws-panel-header flex items-center justify-between">
        <span>Deployment: {detail.deploymentId.slice(0, 12)}...</span>
        <span className={getStatusBadge(detail.status)}>{detail.status}</span>
      </div>
      <div className="aws-panel-body space-y-4">
        {/* Overview */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <label className="text-xs font-bold text-aws-text-secondary uppercase">Application</label>
            <p className="mt-1">{detail.applicationName}</p>
          </div>
          <div>
            <label className="text-xs font-bold text-aws-text-secondary uppercase">Deployment Group</label>
            <p className="mt-1">{detail.deploymentGroupName}</p>
          </div>
          <div>
            <label className="text-xs font-bold text-aws-text-secondary uppercase">Compute Platform</label>
            <p className="mt-1">{detail.computePlatform || '—'}</p>
          </div>
          <div>
            <label className="text-xs font-bold text-aws-text-secondary uppercase">Creator</label>
            <p className="mt-1">{detail.creator || '—'}</p>
          </div>
          <div>
            <label className="text-xs font-bold text-aws-text-secondary uppercase">Created</label>
            <p className="mt-1">{detail.createTime ? new Date(detail.createTime).toLocaleString() : '—'}</p>
          </div>
          <div>
            <label className="text-xs font-bold text-aws-text-secondary uppercase">Completed</label>
            <p className="mt-1">{detail.completeTime ? new Date(detail.completeTime).toLocaleString() : '—'}</p>
          </div>
        </div>

        {/* Error Information */}
        {detail.errorInformation?.message && (
          <div className="p-3 bg-red-50 border border-red-200 rounded">
            <label className="text-xs font-bold text-red-700 uppercase">Error</label>
            <p className="mt-1 text-sm text-red-800">
              {detail.errorInformation.code && <strong>[{detail.errorInformation.code}]</strong>}{' '}
              {detail.errorInformation.message}
            </p>
          </div>
        )}

        {/* Deployment Overview */}
        {Object.keys(detail.deploymentOverview).length > 0 && (
          <div>
            <label className="text-xs font-bold text-aws-text-secondary uppercase">Deployment Overview</label>
            <div className="mt-2 flex gap-3">
              {Object.entries(detail.deploymentOverview).map(([key, value]) => (
                <div key={key} className="text-center px-3 py-2 bg-gray-50 rounded border">
                  <div className="text-lg font-bold">{value}</div>
                  <div className="text-xs text-aws-text-secondary capitalize">{key}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Lifecycle Events */}
        {detail.targets.length > 0 && (
          <div>
            <label className="text-xs font-bold text-aws-text-secondary uppercase">Lifecycle Events</label>
            <div className="mt-2 space-y-2">
              {detail.targets.map((target, i) => (
                <div key={i} className="border rounded p-3">
                  <div className="text-xs text-aws-text-secondary mb-2">Target: {target.targetId} — {target.status}</div>
                  <div className="space-y-1">
                    {target.lifecycleEvents.map((evt, j) => (
                      <div key={j} className="flex items-center gap-2 text-sm">
                        <span className={getStatusBadge(evt.status)}>{evt.status}</span>
                        <span>{evt.name}</span>
                        {evt.diagnostics?.message && (
                          <span className="text-xs text-red-600 ml-auto">{evt.diagnostics.message.slice(0, 80)}</span>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export function DeploymentList() {
  const [deployments, setDeployments] = useState<Deployment[]>([]);
  const [selectedDetail, setSelectedDetail] = useState<DeploymentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState<string>();

  useEffect(() => {
    fetch(`${API_BASE_URL}/api/deployments`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(setDeployments)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  const handleSelectDeployment = (deploymentId: string) => {
    setDetailLoading(true);
    setSelectedDetail(null);
    fetch(`${API_BASE_URL}/api/deployments/${deploymentId}`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then(setSelectedDetail)
      .catch((err) => console.error('Failed to fetch deployment detail:', err))
      .finally(() => setDetailLoading(false));
  };

  if (loading) {
    return (
      <div className="aws-panel">
        <div className="aws-panel-header">Deployments</div>
        <div className="aws-panel-body p-8 text-center text-aws-text-secondary">
          Loading deployments...
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="aws-panel">
        <div className="aws-panel-header">Deployments</div>
        <div className="aws-panel-body p-4 text-red-600 text-sm">Error: {error}</div>
      </div>
    );
  }

  return (
    <div>
      <div className="aws-panel">
        <div className="aws-panel-header flex items-center justify-between">
          <span>Deployments</span>
          <span className="text-xs font-normal text-aws-text-secondary">{deployments.length} deployments</span>
        </div>
        <div className="aws-panel-body p-0">
          {deployments.length === 0 ? (
            <div className="p-6 text-center text-aws-text-secondary text-sm">
              No deployments found
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-aws-border bg-gray-50">
                  <th className="text-left px-4 py-2 font-semibold text-aws-text-secondary">Deployment ID</th>
                  <th className="text-left px-4 py-2 font-semibold text-aws-text-secondary">Application</th>
                  <th className="text-left px-4 py-2 font-semibold text-aws-text-secondary">Group</th>
                  <th className="text-left px-4 py-2 font-semibold text-aws-text-secondary">Status</th>
                  <th className="text-left px-4 py-2 font-semibold text-aws-text-secondary">Created</th>
                </tr>
              </thead>
              <tbody>
                {deployments.map((dep) => (
                  <tr
                    key={dep.deploymentId}
                    className="border-b border-aws-border hover:bg-blue-50 cursor-pointer"
                    onClick={() => handleSelectDeployment(dep.deploymentId)}
                  >
                    <td className="px-4 py-2 font-mono text-xs text-aws-link">{dep.deploymentId.slice(0, 12)}...</td>
                    <td className="px-4 py-2">{dep.applicationName}</td>
                    <td className="px-4 py-2 text-aws-text-secondary">{dep.deploymentGroupName}</td>
                    <td className="px-4 py-2">
                      <span className={getStatusBadge(dep.status)}>{dep.status}</span>
                    </td>
                    <td className="px-4 py-2 text-aws-text-secondary text-xs">
                      {dep.createTime ? new Date(dep.createTime).toLocaleString() : '—'}
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
          <div className="aws-panel-body p-8 text-center text-aws-text-secondary">Loading deployment details...</div>
        </div>
      )}
      {selectedDetail && <DeploymentDetailPanel detail={selectedDetail} />}
    </div>
  );
}
