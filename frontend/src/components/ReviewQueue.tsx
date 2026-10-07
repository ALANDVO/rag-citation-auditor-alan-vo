import React, { useEffect, useState } from 'react';
import { ReviewQueueItem } from '../types';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';

export const ReviewQueue: React.FC = () => {
  const { user } = useAuth();
  const [items, setItems] = useState<ReviewQueueItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedItem, setSelectedItem] = useState<ReviewQueueItem | null>(null);
  const [reviewStatus, setReviewStatus] = useState<string>('HALLUCINATION_CONFIRMED');
  const [auditorNotes, setAuditorNotes] = useState<string>('');
  const [correctedCitations, setCorrectedCitations] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successBanner, setSuccessBanner] = useState<string | null>(null);

  const fetchQueue = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.getReviewQueue('PENDING');
      setItems(data);
      setSelectedItem(data.length > 0 ? (selectedItem ? data.find(i => i.id === selectedItem.id) || data[0] : data[0]) : null);
    } catch (err: any) { setError(err.message || 'Failed to fetch queue'); }
    finally { setIsLoading(false); }
  };

  useEffect(() => { fetchQueue(); }, []);

  const handleSelect = (item: ReviewQueueItem) => {
    setSelectedItem(item);
    setAuditorNotes('');
    setCorrectedCitations(item.claim?.cited_passage_ids.join(', ') || '');
    setSuccessBanner(null);
  };

  const handleResolve = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedItem || !selectedItem.claim || !auditorNotes.trim()) return;
    setIsSubmitting(true);
    try {
      const citeList = correctedCitations ? correctedCitations.split(',').map(s => s.trim()).filter(Boolean) : undefined;
      await api.submitReviewAction({ claim_id: selectedItem.claim_id, review_status: reviewStatus, auditor_notes: auditorNotes.trim(), corrected_citation_ids: citeList });
      setSuccessBanner(`Claim #${selectedItem.claim_id} resolved as ${reviewStatus}.`);
      setAuditorNotes('');
      await fetchQueue();
    } catch (err: any) { alert(`Failed: ${err.message}`); }
    finally { setIsSubmitting(false); }
  };

  if (isLoading) return <div className="loading-state">Loading evidence review queue...</div>;
  if (error) return <div className="error-banner"><p>{error}</p><button className="primary-btn" onClick={fetchQueue}>Retry</button></div>;

  return (
    <div className="review-queue-container">
      <div className="section-header">
        <div>
          <h2>Human Evidence Review Queue</h2>
          <p className="section-desc">Inspect flagged statements, discrepancies, and hallucinated citations with human auditor resolution.</p>
        </div>
        <button className="secondary-btn" onClick={fetchQueue}>Refresh Queue ({items.length})</button>
      </div>

      {successBanner && <div className="success-banner">{successBanner}</div>}

      {items.length === 0 ? (
        <div className="empty-state">
          <div className="empty-icon">✅</div>
          <h2>Review Queue Empty</h2>
          <p>All flagged statements and discrepancies have been reviewed and resolved.</p>
        </div>
      ) : (
        <div className="review-split-layout">
          <div className="queue-list-panel">
            <h3>Pending Discrepancies ({items.length})</h3>
            <div className="queue-items">
              {items.map((it) => (
                <div key={it.id} className={`queue-item-card ${selectedItem?.id === it.id ? 'selected' : ''}`} onClick={() => handleSelect(it)}>
                  <div className="queue-item-top">
                    <span className={`priority-badge priority-${it.priority.toLowerCase()}`}>{it.priority} Priority</span>
                    <span className="claim-id-tag">Claim #{it.claim_id}</span>
                  </div>
                  <p className="queue-item-text">{it.claim?.clean_claim_text || 'Claim statement...'}</p>
                  <div className="queue-item-bottom">
                    <span className={`status-pill pill-${it.claim?.status.toLowerCase()}`}>{it.claim?.status.replace('_', ' ')}</span>
                    <span className="cite-count">Citations: {it.claim?.cited_passage_ids.length || 0}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="inspection-panel">
            {selectedItem && selectedItem.claim ? (
              <div className="inspection-content">
                <div className="inspection-header">
                  <h3>Inspect Claim #{selectedItem.claim_id} (Audit Run #{selectedItem.audit_run_id})</h3>
                  <span className={`status-pill pill-${selectedItem.claim.status.toLowerCase()}`}>{selectedItem.claim.status.replace('_', ' ')}</span>
                </div>
                <div className="inspection-field">
                  <label>Original Sentence Assertion:</label>
                  <blockquote className="claim-quote">{selectedItem.claim.sentence_text}</blockquote>
                </div>
                <div className="inspection-field">
                  <label>Cited Passage References:</label>
                  <div className="tag-list">
                    {selectedItem.claim.cited_passage_ids.map(cid => <span key={cid} className="cite-badge">[{cid}]</span>)}
                  </div>
                </div>
                {selectedItem.claim.match_details?.reason && (
                  <div className="inspection-field">
                    <label>Auditor Findings:</label>
                    <div className="audit-reason-box">{selectedItem.claim.match_details.reason}</div>
                  </div>
                )}
                <hr className="divider" />
                <form onSubmit={handleResolve} className="resolution-form">
                  <h4>Auditor Evidence Determination</h4>
                  <div className="form-group">
                    <label>Decision Verdict:</label>
                    <select value={reviewStatus} onChange={e => setReviewStatus(e.target.value)} className="status-select">
                      <option value="HALLUCINATION_CONFIRMED">HALLUCINATION_CONFIRMED (Statement unsupported)</option>
                      <option value="CORRECTED">CORRECTED (Citation or reference adjusted)</option>
                      <option value="FALSE_POSITIVE">FALSE_POSITIVE (Statement verified by context)</option>
                      <option value="VERIFIED_TRUE">VERIFIED_TRUE (Human auditor confirms assertion)</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Corrected Citation IDs (Optional):</label>
                    <input type="text" value={correctedCitations} onChange={e => setCorrectedCitations(e.target.value)} placeholder="doc_1, doc_2" />
                  </div>
                  <div className="form-group">
                    <label>Auditor Rationale & Notes (Required):</label>
                    <textarea required rows={4} value={auditorNotes} onChange={e => setAuditorNotes(e.target.value)} placeholder="Explain your determination..." />
                  </div>
                  <button type="submit" className="primary-btn submit-resolution-btn" disabled={isSubmitting || !user?.roles.some(r => ['analyst', 'admin'].includes(r))}>
                    {isSubmitting ? 'Recording...' : 'Submit Human Verdict'}
                  </button>
                </form>
              </div>
            ) : <div className="empty-selection">Select an item from the queue to inspect evidence.</div>}
          </div>
        </div>
      )}
    </div>
  );
};
