import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { ReviewQueue } from '../components/ReviewQueue';
import { AuthProvider } from '../context/AuthContext';
import { api } from '../api/client';

describe('ReviewQueue Component', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders review items and presents evidence inspection form', async () => {
    const mockQueue = [
      {
        id: 1,
        claim_id: 101,
        audit_run_id: 5,
        priority: 'HIGH' as const,
        status: 'PENDING' as const,
        assigned_to: '',
        resolution_notes: '',
        resolved_at: null,
        resolved_by: '',
        claim: {
          id: 101,
          audit_run_id: 5,
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
          review_status: 'PENDING' as const,
          auditor_notes: '',
          reviewer_user: ''
        }
      }
    ];

    vi.spyOn(api, 'getReviewQueue').mockResolvedValue(mockQueue);

    render(
      <AuthProvider>
        <ReviewQueue />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByText('HIGH Priority')).toBeInTheDocument();
      expect(screen.getByText('Claim #101')).toBeInTheDocument();
      expect(screen.getByText('EV production climbed by 95% in 2024.')).toBeInTheDocument();
      expect(screen.getByText('Auditor Evidence Determination')).toBeInTheDocument();
    });
  });
});
