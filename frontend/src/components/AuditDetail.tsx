import React, { useEffect, useState } from 'react';
import { AuditRunResponse, LLMAdvisoryResponse } from '../types';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';

interface AuditDetailProps {
  runId: number;
  onBack: () => void;
  onNavigateReview?: () => void;
}

export const AuditDetail: React.FC<AuditDetailProps> = ({ runId, onBack, onNavigateReview }) => {
  const { user } = useAuth();
  const [audit, setAudit] = useState<AuditRunResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [advisoryMap, setAdvisoryMap] = useState<Record<number, LLMAdvisoryResponse>>({});
  const [advLoading, setAdvLoading] = useState<Record<number, boolean>>({});

  useEffect(() => {
    setIsLoading(true);
    api.getAuditRun(runId).then(setAudit).catch(e => setError(e.message)).finally(() => setIsLoading(false));
  }, [runId]);

  const handleExport = async (fmt: 'json' | 'markdown' | 'csv') => {
    try {
      const content = await api.exportAudit(runId, fmt);
      const mime = fmt === 'json' ? 'application/json' : (fmt === 'csv' ? 'text/csv' : 'text/markdown');
      const blob = new Blob([content], { type: mime });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = `audit-${runId}.${fmt === 'markdown' ? 'md' : fmt}`;
      a.click(); URL.revokeObjectURL(url);
    } catch (err: any) { alert(`Export failed: ${err.message}`); }
  };

  const handleRequestAdvisory = async (cid: number) => {
    setAdvLoading(p => ({ ...p, [cid]: true }));
    try {
      const adv = await api.getClaimAdvisory(cid);
      setAdvisoryMap(p => ({ ...p, [cid]: adv }));
    } catch (err: any) { alert(`Advisory failed: ${err.message}`); }
    finally { setAdvLoading(p => ({ ...p, [cid]: false })); }
  };

  if (isLoading) return <div className="loading-state">Loading audit detail and claims...</div>;
  if (error || !audit) return <div className="error-banner"><p>{error || 'Audit not found'}</p><button className="primary-btn" onClick={onBack}>Back</button></div>;

  return (
    <div className="detail-container">
      <div className="detail-header">
        <button className="back-btn" onClick={onBack}>← Back to Dashboard</button>
        <div className="header-actions">
          <span className="export-label">Export:</span>
          <button className="export-btn" onClick={() => handleExport('markdown')}>Markdown</button>
          <button className="export-btn" onClick={() => handleExport('csv')}>CSV</button>
          <button className="export-btn" onClick={() => handleExport('json')}>JSON</button>
        </div>
      </div>

      <div className="audit-summary-banner">
        <div className="banner-title">
          <h2>RAG Citation Audit #{audit.id}</h2>
          <span className="date-stamp">Executed: {new Date(audit.created_at).toLocaleString()}</span>
        </div>
        <div className="scores-grid">
          <div className="score-card"><span className="score-label">Faithfulness</span><span className="score-number">{(audit.faithfulness_score * 100).toFixed(1)}%</span></div>
          <div className="score-card"><span className="score-label">Precision</span><span className="score-number">{(audit.citation_precision * 100).toFixed(1)}%</span></div>
          <div className="score-card"><span className="score-label">Recall</span><span className="score-number">{(audit.citation_recall * 100).toFixed(1)}%</span></div>
          <div className="score-card"><span className="score-label">Numeric Acc</span><span className="score-number">{(audit.numeric_accuracy * 100).toFixed(1)}%</span></div>
        </div>
      </div>

      <div className="claims-section">
        <div className="claims-header">
          <h3>Sentence Claim Attribution ({audit.claims.length} Sentences)</h3>
          {onNavigateReview && <button className="secondary-btn" onClick={onNavigateReview}>Evidence Review Queue →</button>}
        </div>

        <div className="claims-list">
          {audit.claims.map((claim) => {
            const adv = advisoryMap[claim.id];
            return (
              <div key={claim.id} className={`claim-card status-${claim.status.toLowerCase()}`}>
                <div className="claim-card-top">
                  <div className="claim-indexing">
                    <span className="sentence-num">Sentence {claim.sentence_index + 1}</span>
                    <span className={`status-pill pill-${claim.status.toLowerCase()}`}>{claim.status.replace('_', ' ')}</span>
                    <span className="confidence-pill">Confidence: {(claim.confidence_score * 100).toFixed(0)}%</span>
                  </div>
                  <div className="review-status-indicator">Review: <strong className={`review-tag ${claim.review_status.toLowerCase()}`}>{claim.review_status}</strong></div>
                </div>

                <div className="claim-body">
                  <div className="original-sentence"><label>Assertion:</label><p>{claim.sentence_text}</p></div>
                  <div className="citations-cited">
                    <label>Citations:</label>
                    {claim.cited_passage_ids.length > 0 ? (
                      <div className="tag-list">{claim.cited_passage_ids.map(cid => <span key={cid} className="cite-badge">[{cid}]</span>)}</div>
                    ) : <span className="muted-text">None</span>}
                  </div>
                  {claim.match_details?.reason && <div className="rationale-box"><label>Auditor Rationale:</label><p>{claim.match_details.reason}</p></div>}
                  {adv && (
                    <div className="advisory-panel">
                      <div className="advisory-header"><span>Advisory ({adv.provider}):</span><span className="advisory-tag">Opt-in</span></div>
                      <p className="advisory-text">{adv.advisory_text}</p>
                    </div>
                  )}
                </div>

                <div className="claim-footer">
                  {user?.roles.some(r => ['analyst', 'admin'].includes(r)) && !adv && (
                    <button className="advisory-btn" onClick={() => handleRequestAdvisory(claim.id)} disabled={advLoading[claim.id]}>
                      {advLoading[claim.id] ? 'Analyzing...' : 'Run Opt-in LLM Advisory'}
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
