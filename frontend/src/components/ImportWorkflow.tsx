import React, { useState } from 'react';
import { api } from '../api/client';
import { useAuth } from '../context/AuthContext';

export const ImportWorkflow: React.FC<{ onAuditCreated: (runId: number) => void }> = ({ onAuditCreated }) => {
  const { user } = useAuth();
  const [pid, setPid] = useState('doc_1');
  const [pTitle, setPTitle] = useState('Semiconductor Benchmark');
  const [pContent, setPContent] = useState('The 3nm architecture reached 4.2 GHz clock frequency with a 15.5% reduction in thermal dissipation.');
  const [pUrl, setPUrl] = useState('https://benchmarks.internal/semicon-3nm');
  const [query, setQuery] = useState('What clock speed and thermal efficiency was achieved by the 3nm architecture?');
  const [answer, setAnswer] = useState('The 3nm architecture demonstrated 4.2 GHz operating frequency [doc_1]. Thermal dissipation decreased by 15.5% [doc_1].');
  const [model, setModel] = useState('rag-pipeline-v2');
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const loadPreset = (t: string) => {
    if (t === 'clean') {
      setPid('doc_1'); setPTitle('Semiconductor Benchmark'); setPContent('The 3nm architecture reached 4.2 GHz clock frequency with a 15.5% reduction in thermal dissipation.');
      setQuery('What clock speed and thermal efficiency was achieved?'); setAnswer('The 3nm architecture reached 4.2 GHz [doc_1]. Thermal dissipation fell 15.5% [doc_1].');
    } else if (t === 'num_err') {
      setPid('doc_fin'); setPTitle('Q3 Financial Report'); setPContent('Operating margins reached 28.4% while net quarterly profit totaled $14.5M.');
      setQuery('What were the Q3 financial results?'); setAnswer('Operating margins surged to 54.0% [doc_fin]. Net profit was $14.5M [doc_fin].');
    } else {
      setPid('doc_med'); setPTitle('Trial Summary'); setPContent('Tolerance established across 1,200 cohort patients.');
      setQuery('Summarize clinical trial endpoints.'); setAnswer('High safety established across 1,200 subjects [doc_med]. Secondary efficacy confirmed [doc_phantom_99].');
    }
  };

  const handleIngestAndAudit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user?.roles.some(r => ['analyst', 'admin'].includes(r))) {
      setErrorMsg('Analyst or Admin role required to run audits.'); return;
    }
    setSubmitting(true); setErrorMsg(null);
    try {
      await api.ingestPassage({ passage_id: pid.trim(), title: pTitle.trim(), content: pContent.trim(), url: pUrl.trim() });
      const ans = await api.ingestAnswer({ query: query.trim(), generated_text: answer.trim(), model_name: model.trim() });
      const run = await api.runAudit(ans.id);
      onAuditCreated(run.id);
    } catch (err: any) { setErrorMsg(err.message || 'Audit failed'); }
    finally { setSubmitting(false); }
  };

  return (
    <div className="import-container">
      <div className="section-header">
        <div>
          <h2>Ingest Evidence & Run Audit</h2>
          <p className="section-desc">Provide retrieved passages and generated answers with bracketed citation markers (e.g. [doc_1]).</p>
        </div>
        <div className="presets-bar">
          <span className="preset-label">Presets:</span>
          <button type="button" className="preset-btn" onClick={() => loadPreset('clean')}>Clean Citations</button>
          <button type="button" className="preset-btn" onClick={() => loadPreset('num_err')}>Numeric Mismatch</button>
          <button type="button" className="preset-btn" onClick={() => loadPreset('unlinked')}>Unlinked Citation</button>
        </div>
      </div>

      {errorMsg && <div className="error-banner">{errorMsg}</div>}

      <form onSubmit={handleIngestAndAudit} className="import-form">
        <div className="form-columns">
          <div className="form-card">
            <h3>1. Ground-Truth Passage Context</h3>
            <div className="form-group"><label>Passage ID:</label><input required value={pid} onChange={e => setPid(e.target.value)} /></div>
            <div className="form-group"><label>Title:</label><input value={pTitle} onChange={e => setPTitle(e.target.value)} /></div>
            <div className="form-group"><label>Passage Content:</label><textarea required rows={5} value={pContent} onChange={e => setPContent(e.target.value)} /></div>
            <div className="form-group"><label>Source URL:</label><input value={pUrl} onChange={e => setPUrl(e.target.value)} /></div>
          </div>

          <div className="form-card">
            <h3>2. Generated Answer & Query</h3>
            <div className="form-group"><label>Prompt Query:</label><input required value={query} onChange={e => setQuery(e.target.value)} /></div>
            <div className="form-group"><label>Answer Text:</label><textarea required rows={5} value={answer} onChange={e => setAnswer(e.target.value)} /></div>
            <div className="form-group"><label>Model ID:</label><input value={model} onChange={e => setModel(e.target.value)} /></div>
          </div>
        </div>

        <div className="form-footer">
          <button type="submit" className="primary-btn submit-btn" disabled={submitting}>{submitting ? 'Auditing...' : 'Ingest & Trigger Verification Audit'}</button>
        </div>
      </form>
    </div>
  );
};
