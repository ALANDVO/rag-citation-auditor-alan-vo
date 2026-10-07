import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { AuditDashboard } from '../components/AuditDashboard';
import { api } from '../api/client';

describe('AuditDashboard Component', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders empty state when no runs exist', async () => {
    vi.spyOn(api, 'getAuditRuns').mockResolvedValueOnce([]);

    render(
      <AuditDashboard onSelectAudit={vi.fn()} onNavigateImport={vi.fn()} />
    );

    expect(screen.getByText('Loading audit history from database...')).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText('No Audit Runs Recorded')).toBeInTheDocument();
    });
  });

  it('renders audit run cards with metrics and calls onSelectAudit when clicked', async () => {
    const mockRuns = [
      {
        id: 42,
        answer_id: 10,
        project_id: 1,
        total_claims: 3,
        supported_count: 2,
        partially_supported_count: 0,
        unsupported_count: 0,
        unlinked_count: 1,
        numeric_mismatch_count: 0,
        faithfulness_score: 0.67,
        citation_precision: 0.67,
        citation_recall: 1.0,
        numeric_accuracy: 1.0,
        status: 'COMPLETED',
        created_at: new Date().toISOString()
      }
    ];

    vi.spyOn(api, 'getAuditRuns').mockResolvedValueOnce(mockRuns);
    const onSelectAudit = vi.fn();

    render(
      <AuditDashboard onSelectAudit={onSelectAudit} onNavigateImport={vi.fn()} />
    );

    await waitFor(() => {
      expect(screen.getByText('Audit #42')).toBeInTheDocument();
      expect(screen.getByText('67% Faithfulness')).toBeInTheDocument();
    });

    const card = screen.getByText('Audit #42').closest('.run-card');
    expect(card).not.toBeNull();
    if (card) fireEvent.click(card);

    expect(onSelectAudit).toHaveBeenCalledWith(42);
  });
});
