import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { EvaluationView } from '../components/EvaluationView';
import { api } from '../api/client';

const mockBenchmark = {
  precision: 0.875,
  recall: 0.923,
  f1: 0.898,
  numeric_error_detection_rate: 0.95,
  false_alarm_rate: 0.04,
  baseline_overlap_f1: 0.42,
  total_samples: 8,
  execution_time_ms: 124.5
};

const mockDataset = [
  {
    id: 'bench_01',
    description: 'Clean citation with numeric match',
    has_error: false,
    answer: 'The 3nm architecture reached 4.2 GHz [doc_1]. Thermal dissipation fell 15.5% [doc_1].'
  },
  {
    id: 'bench_02',
    description: 'Numeric mismatch - hallucinated percentage',
    has_error: true,
    answer: 'Operating margins surged to 54.0% [doc_fin]. Net profit was $14.5M [doc_fin].'
  },
  {
    id: 'bench_03',
    description: 'Unlinked citation reference',
    has_error: true,
    answer: 'High safety across 1,200 subjects [doc_med]. Secondary efficacy [doc_phantom_99].'
  },
  {
    id: 'bench_04',
    description: 'Partial support - some claims verified',
    has_error: true,
    answer: 'Revenue hit $14.5M [doc_fin]. Margins expanded to 40% [doc_fin].'
  },
  {
    id: 'bench_05',
    description: 'Extreme paraphrasing - zero lexical overlap',
    has_error: true,
    answer: 'The system achieved unprecedented efficiency gains [doc_1].'
  },
  {
    id: 'bench_06',
    description: 'Implicit unit conversion required',
    has_error: true,
    answer: 'Power draw was 1.2 kW [doc_hw].'
  },
  {
    id: 'bench_07',
    description: 'Multiple numbers, some match',
    has_error: true,
    answer: 'Growth was 25% in Q1, 30% in Q2, and 45% in Q3 [doc_q].'
  },
  {
    id: 'bench_08',
    description: 'Factual error - wrong entity',
    has_error: true,
    answer: 'Apple reported $14.5M net profit [doc_fin].'
  }
];

describe('EvaluationView Component', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  const renderComponent = () => render(<EvaluationView />);

  it('shows loading state initially', () => {
    renderComponent();

    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('renders benchmark metrics grid after loading', async () => {
    vi.spyOn(api, 'getBenchmark').mockResolvedValueOnce(mockBenchmark);
    vi.spyOn(api, 'getDataset').mockResolvedValueOnce(mockDataset);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('AI/ML Evaluation & Attribution Benchmark')).toBeInTheDocument();
      expect(screen.getByText('Reproducible evaluation measuring precision, recall, and quantitative error detection against labeled RAG ground truth.')).toBeInTheDocument();
      expect(screen.getByText('Rerun Benchmark Suite')).toBeInTheDocument();
    });

    await waitFor(() => {
      // Check metric cards
      expect(screen.getByText('Attribution F1')).toBeInTheDocument();
      expect(screen.getByText('89.8%')).toBeInTheDocument(); // f1 * 100
      expect(screen.getByText('Precision')).toBeInTheDocument();
      expect(screen.getByText('87.5%')).toBeInTheDocument(); // precision * 100
      expect(screen.getByText('Recall')).toBeInTheDocument();
      expect(screen.getByText('92.3%')).toBeInTheDocument(); // recall * 100
      expect(screen.getByText('Numeric Detection')).toBeInTheDocument();
      expect(screen.getByText('95.0%')).toBeInTheDocument(); // numeric_error_detection_rate * 100
      expect(screen.getByText('False Alarm Rate')).toBeInTheDocument();
      expect(screen.getByText('4.0%')).toBeInTheDocument(); // false_alarm_rate * 100
      expect(screen.getByText('Baseline Overlap F1')).toBeInTheDocument();
      expect(screen.getByText('42.0%')).toBeInTheDocument(); // baseline_overlap_f1 * 100
    });
  });

  it('renders benchmark specifications table', async () => {
    vi.spyOn(api, 'getBenchmark').mockResolvedValueOnce(mockBenchmark);
    vi.spyOn(api, 'getDataset').mockResolvedValueOnce(mockDataset);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Benchmark Specifications & Reproducibility')).toBeInTheDocument();
      expect(screen.getByText('Dataset Size:')).toBeInTheDocument();
      expect(screen.getByText('8 labeled RAG instances')).toBeInTheDocument();
      expect(screen.getByText('Execution Time:')).toBeInTheDocument();
      expect(screen.getByText('124.5 ms total')).toBeInTheDocument();
      expect(screen.getByText('CLI Command:')).toBeInTheDocument();
      expect(screen.getByText('PYTHONPATH=backend python -m app.services.evaluation_benchmark')).toBeInTheDocument();
    });
  });

  it('renders dataset samples with first 3 items', async () => {
    vi.spyOn(api, 'getBenchmark').mockResolvedValueOnce(mockBenchmark);
    vi.spyOn(api, 'getDataset').mockResolvedValueOnce(mockDataset);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Curated Benchmark Instances (8)')).toBeInTheDocument();
    });

    // Check first 3 samples are rendered
    await waitFor(() => {
      expect(screen.getByText('bench_01')).toBeInTheDocument();
      expect(screen.getByText('Clean citation with numeric match')).toBeInTheDocument();
      expect(screen.getByText('The 3nm architecture reached 4.2 GHz [doc_1]. Thermal dissipation fell 15.5% [doc_1].')).toBeInTheDocument();

      expect(screen.getByText('bench_02')).toBeInTheDocument();
      expect(screen.getByText('Numeric mismatch - hallucinated percentage')).toBeInTheDocument();
      expect(screen.getByText('Operating margins surged to 54.0% [doc_fin]. Net profit was $14.5M [doc_fin].')).toBeInTheDocument();

      expect(screen.getByText('bench_03')).toBeInTheDocument();
      expect(screen.getByText('Unlinked citation reference')).toBeInTheDocument();
      expect(screen.getByText('High safety across 1,200 subjects [doc_med]. Secondary efficacy [doc_phantom_99].')).toBeInTheDocument();
    });
  });

  it('shows error badge for samples with errors', async () => {
    vi.spyOn(api, 'getBenchmark').mockResolvedValueOnce(mockBenchmark);
    vi.spyOn(api, 'getDataset').mockResolvedValueOnce(mockDataset);

    renderComponent();

    await waitFor(() => {
      // bench_01 is clean (no error)
      const cleanCard = screen.getByText('bench_01').closest('.dataset-sample-card');
      expect(cleanCard).not.toBeNull();
      if (cleanCard) {
        expect(cleanCard.querySelector('.is-clean')).toBeInTheDocument();
      }

      // bench_02 has error
      const errorCard = screen.getByText('bench_02').closest('.dataset-sample-card');
      expect(errorCard).not.toBeNull();
      if (errorCard) {
        expect(errorCard.querySelector('.has-error')).toBeInTheDocument();
      }
    });
  });

  it('disables rerun button while loading', async () => {
    const benchmarkPromise = Promise.withResolvers<any>();
    const datasetPromise = Promise.withResolvers<any>();
    vi.spyOn(api, 'getBenchmark').mockImplementationOnce(() => benchmarkPromise.promise);
    vi.spyOn(api, 'getDataset').mockImplementationOnce(() => datasetPromise.promise);

    renderComponent();

    const rerunBtn = screen.getByText('Running...');
    expect(rerunBtn).toBeDisabled();

    benchmarkPromise.resolve(mockBenchmark);
    datasetPromise.resolve(mockDataset);

    await waitFor(() => {
      expect(screen.getByText('Rerun Benchmark Suite')).toBeInTheDocument();
    });
  });

  it('shows error banner when API calls fail', async () => {
    vi.spyOn(api, 'getBenchmark').mockRejectedValueOnce(new Error('Benchmark failed'));
    vi.spyOn(api, 'getDataset').mockResolvedValueOnce(mockDataset);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Benchmark failed')).toBeInTheDocument();
    });
  });

  it('can rerun benchmark when button clicked', async () => {
    vi.spyOn(api, 'getBenchmark').mockResolvedValueOnce(mockBenchmark);
    vi.spyOn(api, 'getDataset').mockResolvedValueOnce(mockDataset);

    renderComponent();

    await waitFor(() => {
      expect(screen.getByText('Rerun Benchmark Suite')).toBeInTheDocument();
    });

    // Click rerun
    fireEvent.click(screen.getByText('Rerun Benchmark Suite'));

    await waitFor(() => {
      expect(screen.getByText('Running...')).toBeInTheDocument();
    });

    // Wait for second call to complete
    await waitFor(() => {
      expect(api.getBenchmark).toHaveBeenCalledTimes(2);
      expect(api.getDataset).toHaveBeenCalledTimes(2);
    });
  });
});