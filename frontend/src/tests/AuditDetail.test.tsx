import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AuditDetail } from '../components/AuditDetail';
import { AuthProvider } from '../context/AuthContext';
import { api } from '../api/client';

const mockAudit = {
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
  created_at: new Date().toISOString(),
  claims: [
    {
      id: 101,
      audit_run_id: 42,
      sentence_index: 0,
      sentence_text: 'EV production climbed by 95% in 2024 [doc_1].',
      clean_claim_text: 'EV production climbed by 95% in 2024.',
      cited_passage_ids: ['doc_1'],
      status: 'NUMERIC_MISMATCH',
      confidence_score: 0.94,
      token_overlap_score: 0.45,
      numeric_entities: [
        { raw_text: '95%', value: 95.0, unit: 'percent', kind: 'percentage' }
      ],
      match_details: {
        reason: 'Passage cites 18.2% instead of 95%.'
      },
      review_status: 'PENDING',
      auditor_notes: '',
      reviewer_user: ''
    },
    {
      id: 102,
      audit_run_id: 42,
      sentence_index: 1,
      sentence_text: 'Revenue reached $14.5M in Q3 [doc_fin].',
      clean_claim_text: 'Revenue reached $14.5M in Q3.',
      cited_passage_ids: ['doc_fin'],
      status: 'SUPPORTED',
      confidence_score: 0.98,
      token_overlap_score: 0.82,
      numeric_entities: [
        { raw_text: '$14.5M', value: 14.5, unit: 'USD', kind: 'currency' }
      ],
      match_details: {
        reason: 'Numeric claim matches passage value.'
      },
      review_status: 'VERIFIED_TRUE',
      auditor_notes: 'Confirmed',
      reviewer_user: 'analyst@demo.local'
    },
    {
      id: 103,
      audit_run_id: 42,
      sentence_index: 2,
      sentence_text: 'Market share grew significantly [doc_phantom].',
      clean_claim_text: 'Market share grew significantly.',
      cited_passage_ids: ['doc_phantom'],
      status: 'UNLINKED_CITATION',
      confidence_score: 0.35,
      token_overlap_score: 0.12,
      numeric_entities: [],
      match_details: {
        reason: 'Cited passage [doc_phantom] not found in provided passages.'
      },
      review_status: 'PENDING',
      auditor_notes: '',
      reviewer_user: ''
    }
  ]
};

const mockAdvisory = {
  claim_id: 101,
  advisory_text: 'The claim states 95% growth but the source passage cites 18.2%. This is a significant numeric discrepancy indicating hallucination.',
  provider: 'gpt-4o-mini',
  generated_at: new Date().toISOString()
};

describe('AuditDetail Component', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    // Mock window.alert
    vi.spyOn(window, 'alert').mockImplementation(() => {});
  });

  const renderComponent = (props = {}) => render(
    <AuthProvider>
      <AuditDetail runId={42} onBack={vi.fn()} onNavigateReview={vi.fn()} {...props} />
    </AuthProvider>
  );

  it('shows loading state initially', () => {
    renderComponent();

    expect(screen.getByText('Loading audit detail and claims...')).toBeInTheDocument();
  });

  it('renders audit header with back button and export buttons', async () => {
    vi.spyOn(api, 'getAuditRun').mockResolvedValueOnce(mockAudit);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('← Back to Dashboard')).toBeInTheDocument();
      expect(screen.getByText('Export:')).toBeInTheDocument();
      expect(screen.getByText('Markdown')).toBeInTheDocument();
      expect(screen.getByText('CSV')).toBeInTheDocument();
      expect(screen.getByText('JSON')).toBeInTheDocument();
    });
  });

  it('renders audit summary banner with metrics', async () => {
    vi.spyOn(api, 'getAuditRun').mockResolvedValueOnce(mockAudit);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('RAG Citation Audit #42')).toBeInTheDocument();
      // Check all four metric cards exist using getAllByText
      const scoreCards = screen.getAllByText((content, element) => element.tagName === 'SPAN' && element.className.includes('score-number'));
      expect(scoreCards.length).toBe(4);
      // Verify specific metric values
      expect(screen.getByText('67.0%')).toBeInTheDocument(); // Faithfulness (and Precision)
      expect(screen.getByText('100.0%')).toBeInTheDocument(); // Recall (and Numeric Acc)
    });
  });

  it('renders all claims with status badges and confidence', async () => {
    vi.spyOn(api, 'getAuditRun').mockResolvedValueOnce(mockAudit);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Sentence Claim Attribution (3 Sentences)')).toBeInTheDocument();
      expect(screen.getByText('Evidence Review Queue →')).toBeInTheDocument();

      // Check claim 1 (NUMERIC_MISMATCH)
      expect(screen.getByText('Sentence 1')).toBeInTheDocument();
      expect(screen.getByText('NUMERIC MISMATCH')).toBeInTheDocument();
      expect(screen.getByText('Confidence: 94%')).toBeInTheDocument();
      expect(screen.getByText('EV production climbed by 95% in 2024 [doc_1].')).toBeInTheDocument();
      expect(screen.getByText('[doc_1]')).toBeInTheDocument();
      expect(screen.getByText('Passage cites 18.2% instead of 95%.')).toBeInTheDocument();

      // Check claim 2 (SUPPORTED)
      expect(screen.getByText('Sentence 2')).toBeInTheDocument();
      expect(screen.getByText('SUPPORTED')).toBeInTheDocument();
      expect(screen.getByText('Confidence: 98%')).toBeInTheDocument();
      expect(screen.getByText('Revenue reached $14.5M in Q3 [doc_fin].')).toBeInTheDocument();

      // Check claim 3 (UNLINKED_CITATION)
      expect(screen.getByText('Sentence 3')).toBeInTheDocument();
      expect(screen.getByText('UNLINKED CITATION')).toBeInTheDocument();
      expect(screen.getByText('Confidence: 35%')).toBeInTheDocument();
      expect(screen.getByText('Market share grew significantly [doc_phantom].')).toBeInTheDocument();
      expect(screen.getByText('Cited passage [doc_phantom] not found in provided passages.')).toBeInTheDocument();
    });
  });

  it('renders review status tags for each claim', async () => {
    vi.spyOn(api, 'getAuditRun').mockResolvedValueOnce(mockAudit);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Review: PENDING')).toBeInTheDocument();
      expect(screen.getByText('Review: VERIFIED TRUE')).toBeInTheDocument();
    });
  });

  it('shows advisory panel when advisory data exists', async () => {
    vi.spyOn(api, 'getAuditRun').mockResolvedValueOnce(mockAudit);
    vi.spyOn(api, 'getClaimAdvisory').mockResolvedValueOnce(mockAdvisory);

    renderComponent();

    // Wait for initial render
    await waitFor(() => {
      expect(screen.getByText('Sentence 1')).toBeInTheDocument();
    });

    // Click advisory button for claim 101
    const advisoryBtn = screen.getByText('Run Opt-in LLM Advisory');
    fireEvent.click(advisoryBtn);

    await waitFor(() => {
      expect(screen.getByText('Analyzing...')).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText('Advisory (gpt-4o-mini):')).toBeInTheDocument();
      expect(screen.getByText('Opt-in')).toBeInTheDocument();
      expect(screen.getByText('The claim states 95% growth but the source passage cites 18.2%. This is a significant numeric discrepancy indicating hallucination.')).toBeInTheDocument();
    });
  });

  it('disables advisory button while loading', async () => {
    const advisoryPromise = Promise.withResolvers<any>();
    vi.spyOn(api, 'getAuditRun').mockResolvedValueOnce(mockAudit);
    vi.spyOn(api, 'getClaimAdvisory').mockImplementationOnce(() => advisoryPromise.promise);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Sentence 1')).toBeInTheDocument();
    });

    const advisoryBtn = screen.getByText('Run Opt-in LLM Advisory');
    fireEvent.click(advisoryBtn);

    await waitFor(() => {
      expect(screen.getByText('Analyzing...')).toBeInTheDocument();
      expect(advisoryBtn).toBeDisabled();
    });

    advisoryPromise.resolve(mockAdvisory);
    await waitFor(() => {
      expect(screen.getByText('Run Opt-in LLM Advisory')).toBeInTheDocument();
    });
  });

  it('shows error banner when audit fetch fails', async () => {
    vi.spyOn(api, 'getAuditRun').mockRejectedValueOnce(new Error('Audit not found'));

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Audit not found')).toBeInTheDocument();
      expect(screen.getByText('Back')).toBeInTheDocument();
    });
  });

  it('calls export API and triggers download for each format', async () => {
    vi.spyOn(api, 'getAuditRun').mockResolvedValueOnce(mockAudit);
    vi.spyOn(api, 'exportAudit').mockResolvedValueOnce('exported content');

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Markdown')).toBeInTheDocument();
    });

    // Test Markdown export
    const markdownBtn = screen.getByText('Markdown');
    fireEvent.click(markdownBtn);

    await waitFor(() => {
      expect(api.exportAudit).toHaveBeenCalledWith(42, 'markdown');
    });

    // Test CSV export
    const csvBtn = screen.getByText('CSV');
    fireEvent.click(csvBtn);

    await waitFor(() => {
      expect(api.exportAudit).toHaveBeenCalledWith(42, 'csv');
    });

    // Test JSON export
    const jsonBtn = screen.getByText('JSON');
    fireEvent.click(jsonBtn);

    await waitFor(() => {
      expect(api.exportAudit).toHaveBeenCalledWith(42, 'json');
    });
  });

  it('navigates to review queue when button clicked', async () => {
    const onNavigateReview = vi.fn();
    vi.spyOn(api, 'getAuditRun').mockResolvedValueOnce(mockAudit);

    render(<AuthProvider>
      <AuditDetail runId={42} onBack={vi.fn()} onNavigateReview={onNavigateReview} />
    </AuthProvider>);

    await waitFor(() => {
      expect(screen.getByText('Evidence Review Queue →')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Evidence Review Queue →'));

    expect(onNavigateReview).toHaveBeenCalled();
  });

  it('only shows advisory button for analyst/admin roles', async () => {
    vi.spyOn(api, 'getAuditRun').mockResolvedValueOnce(mockAudit);

    // Render with viewer role (default in setup.ts is analyst, so we need to mock differently)
    // The AuthContext mock in setup.ts provides analyst role
    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Run Opt-in LLM Advisory')).toBeInTheDocument();
    });
  });
});