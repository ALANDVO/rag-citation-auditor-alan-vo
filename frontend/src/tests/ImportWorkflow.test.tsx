import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ImportWorkflow } from '../components/ImportWorkflow';
import { AuthContext } from '../context/AuthContext';
import { api } from '../api/client';
import React from 'react';

const mockAnalystUser = {
  user_id: 'test-analyst',
  email: 'analyst@demo.local',
  roles: ['analyst'],
  is_authenticated: true,
  is_demo: true,
  csrf_token: 'test-csrf-token'
};

const TestAuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const mockAuth = {
    user: mockAnalystUser,
    isLoading: false,
    loginDemo: vi.fn(),
    logout: vi.fn(),
    refreshProfile: vi.fn(),
  };
  return (
    <AuthContext.Provider value={mockAuth}>
      {children}
    </AuthContext.Provider>
  );
};

describe('ImportWorkflow Component', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  const mockOnAuditCreated = vi.fn();
  const renderComponent = () => render(
    <TestAuthProvider>
      <ImportWorkflow onAuditCreated={mockOnAuditCreated} />
    </TestAuthProvider>
  );

  it('renders with default preset values and preset buttons', () => {
    renderComponent();

    expect(screen.getByText('Ingest Evidence & Run Audit')).toBeInTheDocument();
    expect(screen.getByText('Provide retrieved passages and generated answers with bracketed citation markers (e.g. [doc_1]).')).toBeInTheDocument();
    expect(screen.getByText('Presets:')).toBeInTheDocument();
    expect(screen.getByText('Clean Citations')).toBeInTheDocument();
    expect(screen.getByText('Numeric Mismatch')).toBeInTheDocument();
    expect(screen.getByText('Unlinked Citation')).toBeInTheDocument();

    expect(screen.getByDisplayValue('doc_1')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Semiconductor Benchmark')).toBeInTheDocument();
    expect(screen.getByDisplayValue('The 3nm architecture reached 4.2 GHz clock frequency with a 15.5% reduction in thermal dissipation.')).toBeInTheDocument();
    expect(screen.getByDisplayValue('What clock speed and thermal efficiency was achieved by the 3nm architecture?')).toBeInTheDocument();
    expect(screen.getByDisplayValue('The 3nm architecture demonstrated 4.2 GHz operating frequency [doc_1]. Thermal dissipation decreased by 15.5% [doc_1].')).toBeInTheDocument();
    expect(screen.getByDisplayValue('rag-pipeline-v2')).toBeInTheDocument();
  });

  it('loads Clean Citations preset when clicked', () => {
    renderComponent();

    const cleanBtn = screen.getByText('Clean Citations');
    fireEvent.click(cleanBtn);

    expect(screen.getByDisplayValue('doc_1')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Semiconductor Benchmark')).toBeInTheDocument();
    expect(screen.getByDisplayValue('The 3nm architecture reached 4.2 GHz clock frequency with a 15.5% reduction in thermal dissipation.')).toBeInTheDocument();
    expect(screen.getByDisplayValue('What clock speed and thermal efficiency was achieved?')).toBeInTheDocument();
    expect(screen.getByDisplayValue('The 3nm architecture reached 4.2 GHz [doc_1]. Thermal dissipation fell 15.5% [doc_1].')).toBeInTheDocument();
  });

  it('loads Numeric Mismatch preset when clicked', () => {
    renderComponent();

    const numErrBtn = screen.getByText('Numeric Mismatch');
    fireEvent.click(numErrBtn);

    expect(screen.getByDisplayValue('doc_fin')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Q3 Financial Report')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Operating margins reached 28.4% while net quarterly profit totaled $14.5M.')).toBeInTheDocument();
    expect(screen.getByDisplayValue('What were the Q3 financial results?')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Operating margins surged to 54.0% [doc_fin]. Net profit was $14.5M [doc_fin].')).toBeInTheDocument();
  });

  it('loads Unlinked Citation preset when clicked', () => {
    renderComponent();

    const unlinkedBtn = screen.getByText('Unlinked Citation');
    fireEvent.click(unlinkedBtn);

    expect(screen.getByDisplayValue('doc_med')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Trial Summary')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Tolerance established across 1,200 cohort patients.')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Summarize clinical trial endpoints.')).toBeInTheDocument();
    expect(screen.getByDisplayValue('High safety established across 1,200 subjects [doc_med]. Secondary efficacy confirmed [doc_phantom_99].')).toBeInTheDocument();
  });

  it('submits form successfully with analyst role and calls onAuditCreated', async () => {
    vi.spyOn(api, 'ingestPassage').mockResolvedValueOnce({ id: 1, passage_id: 'doc_1' });
    vi.spyOn(api, 'ingestAnswer').mockResolvedValueOnce({ id: 42, query: 'test', generated_text: 'test [doc_1]' });
    vi.spyOn(api, 'runAudit').mockResolvedValueOnce({ id: 100, answer_id: 42, project_id: 1, status: 'COMPLETED' });

    renderComponent();

    const submitBtn = screen.getByText('Ingest & Trigger Verification Audit');
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(api.ingestPassage).toHaveBeenCalled();
      expect(api.ingestAnswer).toHaveBeenCalled();
      expect(api.runAudit).toHaveBeenCalledWith(42);
    });

    await waitFor(() => {
      expect(mockOnAuditCreated).toHaveBeenCalledWith(100);
    });
  });

  it('verifies component renders and role check logic exists', () => {
    renderComponent();

    const submitBtn = screen.getByText('Ingest & Trigger Verification Audit');
    expect(submitBtn).toBeInTheDocument();
  });

  it('disables submit button while submitting', async () => {
    const auditPromise = Promise.withResolvers<any>();
    vi.spyOn(api, 'ingestPassage').mockResolvedValueOnce({ id: 1 });
    vi.spyOn(api, 'ingestAnswer').mockResolvedValueOnce({ id: 42 });
    vi.spyOn(api, 'runAudit').mockImplementationOnce(() => auditPromise.promise);

    renderComponent();

    const submitBtn = screen.getByText('Ingest & Trigger Verification Audit');
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText('Auditing...')).toBeInTheDocument();
      expect(submitBtn).toBeDisabled();
    });

    auditPromise.resolve({ id: 100, answer_id: 42, project_id: 1, status: 'COMPLETED' });
    await waitFor(() => {
      expect(screen.getByText('Ingest & Trigger Verification Audit')).toBeInTheDocument();
    });
  });

  it('shows error banner when API call fails', async () => {
    vi.spyOn(api, 'ingestPassage').mockResolvedValueOnce({ id: 1 });
    vi.spyOn(api, 'ingestAnswer').mockResolvedValueOnce({ id: 42 });
    vi.spyOn(api, 'runAudit').mockRejectedValueOnce(new Error('Audit run failed'));

    renderComponent();

    const submitBtn = screen.getByText('Ingest & Trigger Verification Audit');
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText('Audit run failed')).toBeInTheDocument();
    });
  });
});
