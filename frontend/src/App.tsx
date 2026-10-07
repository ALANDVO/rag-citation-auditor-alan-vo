import React, { useState, useEffect } from 'react';
import { useAuth } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { AuditDashboard } from './components/AuditDashboard';
import { AuditDetail } from './components/AuditDetail';
import { ImportWorkflow } from './components/ImportWorkflow';
import { ReviewQueue } from './components/ReviewQueue';
import { EvaluationView } from './components/EvaluationView';
import { AuditLogsView } from './components/AuditLogsView';
import { api } from './api/client';

export const App: React.FC = () => {
  const { user, isLoading } = useAuth();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedRunId, setSelectedRunId] = useState<number | null>(null);
  const [pendingCount, setPendingCount] = useState(0);

  const fetchPendingCount = async () => {
    try {
      const queue = await api.getReviewQueue('PENDING');
      setPendingCount(queue.length);
    } catch {
      // ignore
    }
  };

  useEffect(() => {
    if (user?.is_authenticated) {
      fetchPendingCount();
    }
  }, [user, activeTab]);

  const handleSelectAudit = (runId: number) => {
    setSelectedRunId(runId);
  };

  const handleAuditCreated = (runId: number) => {
    setSelectedRunId(runId);
    setActiveTab('dashboard');
    fetchPendingCount();
  };

  const handleTabChange = (tab: string) => {
    setActiveTab(tab);
    setSelectedRunId(null);
  };

  if (isLoading) {
    return (
      <div className="app-loading-screen">
        <div className="spinner"></div>
        <p>Initializing RAG Citation Auditor session...</p>
      </div>
    );
  }

  return (
    <div className="app-root">
      <Navbar
        activeTab={selectedRunId ? '' : activeTab}
        setActiveTab={handleTabChange}
        pendingReviewCount={pendingCount}
      />

      <main className="main-content">
        {selectedRunId ? (
          <AuditDetail
            runId={selectedRunId}
            onBack={() => setSelectedRunId(null)}
            onNavigateReview={() => {
              setSelectedRunId(null);
              setActiveTab('review');
            }}
          />
        ) : (
          <>
            {activeTab === 'dashboard' && (
              <AuditDashboard
                onSelectAudit={handleSelectAudit}
                onNavigateImport={() => setActiveTab('import')}
              />
            )}
            {activeTab === 'import' && (
              <ImportWorkflow onAuditCreated={handleAuditCreated} />
            )}
            {activeTab === 'review' && <ReviewQueue />}
            {activeTab === 'benchmark' && <EvaluationView />}
            {activeTab === 'audit-logs' && <AuditLogsView />}
          </>
        )}
      </main>

      <footer className="app-footer">
        <div className="footer-content">
          <span>RAG Citation & Faithfulness Auditor v1.0.0</span>
          <span>Designed & Built by Alan Vo (<a href="mailto:alanvo@gmail.com">alanvo@gmail.com</a>) &bull; GitHub ALANDVO</span>
        </div>
      </footer>
    </div>
  );
};

export default App;
