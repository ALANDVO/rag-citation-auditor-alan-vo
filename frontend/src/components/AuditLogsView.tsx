import React, { useEffect, useState } from 'react';
import { AuditLog } from '../types';
import { api } from '../api/client';

export const AuditLogsView: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchLogs = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.getAuditLogs();
      setLogs(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch audit logs');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  if (isLoading) {
    return <div className="loading-state">Loading immutable audit logs...</div>;
  }

  if (error) {
    return (
      <div className="error-banner">
        <p>{error}</p>
        <button className="primary-btn" onClick={fetchLogs}>Retry</button>
      </div>
    );
  }

  return (
    <div className="audit-logs-container">
      <div className="section-header">
        <div>
          <h2>System Audit Trail</h2>
          <p className="section-desc">
            Immutable log of all data mutations, logins, audits, and human evidence determinations.
          </p>
        </div>
        <button className="secondary-btn" onClick={fetchLogs}>
          Refresh Logs ({logs.length})
        </button>
      </div>

      <div className="table-responsive">
        <table className="audit-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Action</th>
              <th>User</th>
              <th>Role</th>
              <th>Target Entity</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <tr key={log.id}>
                <td className="timestamp-cell">{new Date(log.timestamp).toLocaleString()}</td>
                <td><span className="action-tag">{log.action}</span></td>
                <td>{log.user_email || log.user_id}</td>
                <td><span className="role-tag">{log.user_role}</span></td>
                <td>{log.entity_type} #{log.entity_id}</td>
                <td className="details-cell">
                  <pre>{JSON.stringify(log.details, null, 1)}</pre>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
