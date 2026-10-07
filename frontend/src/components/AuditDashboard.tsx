import React, { useEffect, useState } from 'react';
import { AuditRunSummary } from '../types';
import { api } from '../api/client';

interface AuditDashboardProps {
  onSelectAudit: (runId: number) => void;
  onNavigateImport: () => void;
}

export const AuditDashboard: React.FC<AuditDashboardProps> = ({ onSelectAudit, onNavigateImport }) => {
  const [runs, setRuns] = useState<AuditRunSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchRuns = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.getAuditRuns();
      setRuns(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch audit runs');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchRuns();
  }, []);

  if (isLoading) {
    return <div className="loading-state">Loading audit history from database...</div>;
  }

  if (error) {
    return (
      <div className="error-banner">
        <p>{error}</p>
        <button className="primary-btn" onClick={fetchRuns}>Retry</button>
      </div>
    );
  }

  if (runs.length === 0) {
    return (
      <div className="empty-state">
        <div className="empty-icon">📊</div>
        <h2>No Audit Runs Recorded</h2>
        <p>
          Ingest generated RAG answers and source passages to verify citation attribution,
          detect numeric hallucinations, and inspect evidence.
        </p>
        <button className="primary-btn" onClick={onNavigateImport}>
          Start First Audit
        </button>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <div className="section-header">
        <div>
          <h2>Audited RAG Runs</h2>
          <p className="section-desc">
            Deterministic attribution verification across sentence claims, citation links, and numeric assertions.
          </p>
        </div>
        <button className="secondary-btn" onClick={fetchRuns}>
          Refresh Runs
        </button>
      </div>

      <div className="runs-grid">
        {runs.map((run) => (
          <div key={run.id} className="run-card" onClick={() => onSelectAudit(run.id)}>
            <div className="run-card-header">
              <span className="run-id">Audit #{run.id}</span>
              <span className={`status-tag ${run.faithfulness_score >= 0.8 ? 'tag-green' : run.faithfulness_score >= 0.5 ? 'tag-yellow' : 'tag-red'}`}>
                {(run.faithfulness_score * 100).toFixed(0)}% Faithfulness
              </span>
            </div>

            <div className="metrics-row">
              <div className="metric-box">
                <span className="metric-label">Precision</span>
                <span className="metric-val">{(run.citation_precision * 100).toFixed(0)}%</span>
              </div>
              <div className="metric-box">
                <span className="metric-label">Recall</span>
                <span className="metric-val">{(run.citation_recall * 100).toFixed(0)}%</span>
              </div>
              <div className="metric-box">
                <span className="metric-label">Numeric Acc</span>
                <span className="metric-val">{(run.numeric_accuracy * 100).toFixed(0)}%</span>
              </div>
              <div className="metric-box">
                <span className="metric-label">Total Claims</span>
                <span className="metric-val">{run.total_claims}</span>
              </div>
            </div>

            <div className="breakdown-bar">
              <span className="count-pill supported" title="Supported">
                ✓ {run.supported_count}
              </span>
              <span className="count-pill partial" title="Partially Supported">
                ~ {run.partially_supported_count}
              </span>
              {run.numeric_mismatch_count > 0 && (
                <span className="count-pill mismatch" title="Numeric Mismatches">
                  # {run.numeric_mismatch_count}
                </span>
              )}
              {run.unlinked_count > 0 && (
                <span className="count-pill unlinked" title="Unlinked Citations">
                  ? {run.unlinked_count}
                </span>
              )}
              {run.unsupported_count > 0 && (
                <span className="count-pill unsupported" title="Unsupported Claims">
                  ✕ {run.unsupported_count}
                </span>
              )}
            </div>

            <div className="run-card-footer">
              <span className="timestamp">
                {new Date(run.created_at).toLocaleString()}
              </span>
              <span className="view-link">View Details →</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
