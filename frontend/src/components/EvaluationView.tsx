import React, { useEffect, useState } from 'react';
import { BenchmarkRunResponse } from '../types';
import { api } from '../api/client';

export const EvaluationView: React.FC = () => {
  const [benchmark, setBenchmark] = useState<BenchmarkRunResponse | null>(null);
  const [dataset, setDataset] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const runEval = async () => {
    setIsLoading(true); setError(null);
    try {
      const [bData, dData] = await Promise.all([api.getBenchmark(), api.getDataset()]);
      setBenchmark(bData); setDataset(dData);
    } catch (err: any) { setError(err.message || 'Evaluation failed'); }
    finally { setIsLoading(false); }
  };

  useEffect(() => { runEval(); }, []);

  return (
    <div className="eval-container">
      <div className="section-header">
        <div>
          <h2>AI/ML Evaluation & Attribution Benchmark</h2>
          <p className="section-desc">Reproducible evaluation measuring precision, recall, and quantitative error detection against labeled RAG ground truth.</p>
        </div>
        <button className="primary-btn" onClick={runEval} disabled={isLoading}>{isLoading ? 'Running...' : 'Rerun Benchmark Suite'}</button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {benchmark && (
        <>
          <div className="benchmark-metrics-grid">
            <div className="eval-metric-card primary-card"><span className="eval-metric-title">Attribution F1</span><span className="eval-metric-number">{(benchmark.f1 * 100).toFixed(1)}%</span><span className="eval-metric-sub">Harmonic mean</span></div>
            <div className="eval-metric-card"><span className="eval-metric-title">Precision</span><span className="eval-metric-number">{(benchmark.precision * 100).toFixed(1)}%</span><span className="eval-metric-sub">Verified true</span></div>
            <div className="eval-metric-card"><span className="eval-metric-title">Recall</span><span className="eval-metric-number">{(benchmark.recall * 100).toFixed(1)}%</span><span className="eval-metric-sub">Hallucinations caught</span></div>
            <div className="eval-metric-card highlight-card"><span className="eval-metric-title">Numeric Detection</span><span className="eval-metric-number">{(benchmark.numeric_error_detection_rate * 100).toFixed(1)}%</span><span className="eval-metric-sub">Quantitative errors</span></div>
            <div className="eval-metric-card"><span className="eval-metric-title">False Alarm Rate</span><span className="eval-metric-number">{(benchmark.false_alarm_rate * 100).toFixed(1)}%</span><span className="eval-metric-sub">False positives</span></div>
            <div className="eval-metric-card"><span className="eval-metric-title">Baseline Overlap F1</span><span className="eval-metric-number">{(benchmark.baseline_overlap_f1 * 100).toFixed(1)}%</span><span className="eval-metric-sub">Naive unigram baseline</span></div>
          </div>

          <div className="eval-details-card">
            <h3>Benchmark Specifications & Reproducibility</h3>
            <div className="spec-table">
              <div className="spec-row"><span className="spec-name">Dataset Size:</span><span className="spec-val">{benchmark.total_samples} labeled RAG instances</span></div>
              <div className="spec-row"><span className="spec-name">Execution Time:</span><span className="spec-val">{benchmark.execution_time_ms.toFixed(1)} ms total</span></div>
              <div className="spec-row"><span className="spec-name">CLI Command:</span><code className="spec-code">PYTHONPATH=backend python -m app.services.evaluation_benchmark</code></div>
            </div>
          </div>

          <div className="dataset-section">
            <h3>Curated Benchmark Instances ({dataset.length})</h3>
            <div className="dataset-samples">
              {dataset.slice(0, 3).map((d) => (
                <div key={d.id} className="dataset-sample-card">
                  <div className="sample-card-header"><span className="sample-id">{d.id}</span><span className={`sample-type ${d.has_error ? 'has-error' : 'is-clean'}`}>{d.has_error ? 'Error' : 'Clean'}</span></div>
                  <p className="sample-desc"><strong>Desc:</strong> {d.description}</p>
                  <p className="sample-answer"><strong>Answer:</strong> {d.answer}</p>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
};
