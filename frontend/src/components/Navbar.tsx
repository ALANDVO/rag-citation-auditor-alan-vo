import React from 'react';
import { useAuth } from '../context/AuthContext';

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  pendingReviewCount?: number;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab, pendingReviewCount = 0 }) => {
  const { user, loginDemo, logout } = useAuth();

  const handleRoleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    loginDemo(e.target.value);
  };

  return (
    <header className="navbar">
      <div className="nav-brand">
        <div className="logo-badge">RAG</div>
        <div>
          <h1>Citation & Faithfulness Auditor</h1>
          <span className="sub-title">Alan Vo | AI & Machine Learning</span>
        </div>
      </div>

      <nav className="nav-tabs">
        <button
          className={`tab-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
          onClick={() => setActiveTab('dashboard')}
        >
          Audit Dashboard
        </button>
        <button
          className={`tab-btn ${activeTab === 'import' ? 'active' : ''}`}
          onClick={() => setActiveTab('import')}
        >
          Ingest & Audit
        </button>
        <button
          className={`tab-btn ${activeTab === 'review' ? 'active' : ''}`}
          onClick={() => setActiveTab('review')}
        >
          Evidence Review
          {pendingReviewCount > 0 && <span className="counter-badge">{pendingReviewCount}</span>}
        </button>
        <button
          className={`tab-btn ${activeTab === 'benchmark' ? 'active' : ''}`}
          onClick={() => setActiveTab('benchmark')}
        >
          AI/ML Evaluation
        </button>
        {user?.roles.includes('admin') && (
          <button
            className={`tab-btn ${activeTab === 'audit-logs' ? 'active' : ''}`}
            onClick={() => setActiveTab('audit-logs')}
          >
            Audit Trail
          </button>
        )}
      </nav>

      <div className="nav-user">
        <div className="user-role-control">
          <label htmlFor="role-select">Role:</label>
          <select
            id="role-select"
            value={user?.roles[0] || 'analyst'}
            onChange={handleRoleChange}
            className="role-selector"
          >
            <option value="viewer">Viewer</option>
            <option value="analyst">Analyst</option>
            <option value="admin">Admin</option>
          </select>
        </div>
        <div className="user-info">
          <span className="user-badge">{user?.user_id || 'guest'}</span>
          {user?.is_authenticated && (
            <button className="logout-btn" onClick={logout} title="Logout">
              Logout
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
