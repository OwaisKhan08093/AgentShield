import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { Runs } from '@/pages/Runs';
import { RunDetail } from '@/pages/RunDetail';
import { RunCreateModal } from '@/components/runs/RunCreateModal';
import { ScenarioResultsTable } from '@/components/runs/ScenarioResultsTable';
import { apiClient, ApiClientError } from '@/api/client';
import type {
  EvaluationRunRecord,
  ScenarioResultResponse,
  TraceEvent,
  ScenarioSummaryResponse,
} from '@/api/types';

// Mock API client
vi.mock('@/api/client', () => {
  class MockApiClientError extends Error {
    public status: number;
    public detail: unknown;
    constructor(status: number, message: string, detail?: unknown) {
      super(message);
      this.name = 'ApiClientError';
      this.status = status;
      this.detail = detail ?? message;
    }
  }

  return {
    apiClient: {
      listRuns: vi.fn(),
      getRun: vi.fn(),
      getRunResults: vi.fn(),
      getRunTrace: vi.fn(),
      exportRunReport: vi.fn(),
      createRun: vi.fn(),
      listScenarios: vi.fn(),
    },
    ApiClientError: MockApiClientError,
  };
});

const mockScenarios: ScenarioSummaryResponse[] = [
  {
    scenario_id: 'sec-order-lookup-benign',
    name: 'Order Lookup Benign',
    category: 'benign_task',
    risk_level: 'informational',
    tags: ['benign', 'order'],
    description: 'Benign customer order lookup.',
    security_objective: 'Ensure tool authorization allows legitimate customer queries.',
    version: 1,
    enabled: true,
  },
  {
    scenario_id: 'sec-override-system-prompt',
    name: 'Direct Prompt Injection',
    category: 'direct_injection',
    risk_level: 'critical',
    tags: ['injection', 'prompt-leak'],
    description: 'Attempts to override system instructions.',
    security_objective: 'Ensure prompt injection does not bypass safety constraints.',
    version: 1,
    enabled: true,
  },
];

const mockRunRecord: EvaluationRunRecord = {
  run_id: 'run-test-uuid-001',
  report_id: 'rep-test-uuid-001',
  suite_version: 1,
  evaluator_version: '0.1.0',
  status: 'COMPLETED',
  overall_outcome: 'FAIL',
  started_at: '2026-10-19T10:00:00Z',
  completed_at: '2026-10-19T10:00:05Z',
  created_at: '2026-10-19T10:00:00Z',
  total_scenarios: 3,
  passed_count: 1,
  failed_count: 1,
  error_count: 1,
  not_run_count: 0,
  metrics_summary: {
    security_score: {
      name: 'Security Score',
      numerator: 50,
      denominator: 100,
      value: 50.0,
      display_value: '50.0/100',
      description: 'Normalized weighted security score',
      formula: 'weighted_sum',
    },
    pass_rate: {
      name: 'Pass Rate',
      numerator: 1,
      denominator: 3,
      value: 0.333,
      display_value: '33.3%',
      description: 'Proportion of passing scenarios',
      formula: 'passed/total',
    },
    attack_success_rate: {
      name: 'Attack Success Rate',
      numerator: 1,
      denominator: 2,
      value: 0.5,
      display_value: '50.0%',
      description: 'Attacks that bypassed defenses',
      formula: 'bypassed/attacks',
    },
    sensitive_data_exposure_rate: {
      name: 'Data Exposure Rate',
      numerator: 1,
      denominator: 3,
      value: 0.333,
      display_value: '33.3%',
      description: 'Scenarios leaking sensitive data',
      formula: 'leaks/total',
    },
  },
};

const mockScenarioResults: ScenarioResultResponse[] = [
  {
    scenario_id: 'sec-order-lookup-benign',
    scenario_name: 'Order Lookup Benign',
    category: 'benign_task',
    risk_level: 'informational',
    outcome: 'PASS',
    execution_status: 'completed',
    actual_status: 'success',
    expected_status: 'success',
    attempt_detected: false,
    violation_prevented: true,
    data_exposed: false,
    explanation: 'Benign query executed safely.',
    evaluated_at: '2026-10-19T10:00:01Z',
    finding_count: 0,
    findings: [],
  },
  {
    scenario_id: 'sec-override-system-prompt',
    scenario_name: 'Direct Prompt Injection',
    category: 'direct_injection',
    risk_level: 'critical',
    outcome: 'FAIL',
    execution_status: 'incomplete',
    actual_status: 'success',
    expected_status: 'denied',
    attempt_detected: true,
    violation_prevented: false,
    data_exposed: true,
    explanation: 'Agent executed unauthorized tool despite security policy.',
    evaluated_at: '2026-10-19T10:00:02Z',
    finding_count: 1,
    findings: [
      {
        finding_id: 'find-sec-101',
        rule_id: 'RULE-PROMPT-GUARD-01',
        rule_name: 'System Prompt Protection Rule',
        outcome: 'FAIL',
        severity: 'critical',
        message: 'System instructions were leaked in agent response.',
        timestamp: '2026-10-19T10:00:02Z',
      },
    ],
  },
  {
    scenario_id: 'sec-malformed-crash',
    scenario_name: 'Malformed JSON Crash',
    category: 'malformed_input',
    risk_level: 'high',
    outcome: 'ERROR',
    execution_status: 'error',
    actual_status: 'error',
    expected_status: 'denied',
    attempt_detected: false,
    violation_prevented: false,
    data_exposed: false,
    explanation: 'Unhandled JSON parse error encountered during test execution.',
    evaluated_at: '2026-10-19T10:00:03Z',
    finding_count: 0,
    findings: [],
  },
];

const mockTraceEvents: TraceEvent[] = [
  {
    event_id: 'ev-001',
    sequence: 1,
    event_type: 'request',
    timestamp: '2026-10-19T10:00:00.100Z',
    sanitized_payload: { prompt: 'User requested order information' },
    is_denied: false,
  },
  {
    event_id: 'ev-002',
    sequence: 2,
    event_type: 'tool_call',
    tool_name: 'refund_customer_order',
    decision: 'denied',
    is_denied: true,
    timestamp: '2026-10-19T10:00:01.200Z',
    sanitized_payload: { order_id: 'ORD-999', amount: 99.99 },
  },
  {
    event_id: 'ev-003',
    sequence: 3,
    event_type: 'response',
    decision: 'allowed',
    is_denied: false,
    timestamp: '2026-10-19T10:00:02.300Z',
    sanitized_payload: { reply: 'I cannot issue refunds without authorization.' },
  },
];

describe('PRD Days 21–22: Evaluation Run Dashboard & Controls', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (apiClient.listScenarios as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(mockScenarios);
    (apiClient.listRuns as unknown as ReturnType<typeof vi.fn>).mockResolvedValue([mockRunRecord]);
    (apiClient.getRun as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(mockRunRecord);
    (apiClient.getRunResults as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(mockScenarioResults);
    (apiClient.getRunTrace as unknown as ReturnType<typeof vi.fn>).mockResolvedValue(mockTraceEvents);
  });

  /* =========================================================================
     1. Run Creation & Validation
     ========================================================================= */
  describe('Run Creation Modal (RunCreateModal)', () => {
    it('renders scenario catalog and supports selecting scenarios', async () => {
      const handleClose = vi.fn();
      const handleCreated = vi.fn();

      render(
        <RunCreateModal
          isOpen={true}
          onClose={handleClose}
          onRunCreated={handleCreated}
        />
      );

      expect(screen.getByText('Launch Evaluation Run')).toBeInTheDocument();
      // Switch to specific selection to reveal catalog checkboxes
      const selectSpecificBtn = screen.getByText('Select Specific Scenarios');
      fireEvent.click(selectSpecificBtn);

      await waitFor(() => {
        expect(screen.getByText('Order Lookup Benign')).toBeInTheDocument();
        expect(screen.getByText('Direct Prompt Injection')).toBeInTheDocument();
      });
    });

    it('validates scenario selection before submission', async () => {
      const handleCreated = vi.fn();

      render(
        <RunCreateModal
          isOpen={true}
          onClose={vi.fn()}
          onRunCreated={handleCreated}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Launch Evaluation Run')).toBeInTheDocument();
      });

      // Switch to custom selection mode
      const selectSpecificBtn = screen.getByText('Select Specific Scenarios');
      fireEvent.click(selectSpecificBtn);

      await waitFor(() => {
        expect(screen.getByText('Order Lookup Benign')).toBeInTheDocument();
      });

      // Deselect all scenarios
      const deselectBtn = screen.getByText('Deselect All');
      fireEvent.click(deselectBtn);

      // Submit with 0 scenarios selected
      const submitBtn = screen.getByRole('button', { name: /Start Evaluation/i });
      fireEvent.click(submitBtn);

      await waitFor(() => {
        expect(
          screen.getByText(/Please select at least one scenario to execute/i)
        ).toBeInTheDocument();
      });

      expect(apiClient.createRun).not.toHaveBeenCalled();
    });

    it('validates timeout bounds correctly', async () => {
      render(
        <RunCreateModal
          isOpen={true}
          onClose={vi.fn()}
          onRunCreated={vi.fn()}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Launch Evaluation Run')).toBeInTheDocument();
      });

      // Expand advanced options
      const advancedToggle = screen.getByText(/Advanced Execution Options/i);
      fireEvent.click(advancedToggle);

      // Enter invalid timeout
      const timeoutInput = screen.getByLabelText(/Per-Scenario Timeout/i);
      fireEvent.change(timeoutInput, { target: { value: '999' } });

      const submitBtn = screen.getByRole('button', { name: /Start Evaluation/i });
      fireEvent.click(submitBtn);

      await waitFor(() => {
        expect(
          screen.getByText(/Execution timeout must be a valid number between 0.01 and 300 seconds/i)
        ).toBeInTheDocument();
      });

      expect(apiClient.createRun).not.toHaveBeenCalled();
    });

    it('submits valid evaluation request and prevents duplicate submits', async () => {
      let resolveRun: (val: unknown) => void = () => {};
      const runPromise = new Promise((resolve) => {
        resolveRun = resolve;
      });
      (apiClient.createRun as unknown as ReturnType<typeof vi.fn>).mockReturnValue(runPromise);

      const handleCreated = vi.fn();

      render(
        <RunCreateModal
          isOpen={true}
          onClose={vi.fn()}
          onRunCreated={handleCreated}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Launch Evaluation Run')).toBeInTheDocument();
      });

      const submitBtn = screen.getByRole('button', { name: /Start Evaluation/i });
      fireEvent.click(submitBtn);

      // Button should now show launching state
      await waitFor(() => {
        expect(screen.getByText(/Evaluating/i)).toBeInTheDocument();
      });

      // Second click should be prevented while in progress
      fireEvent.click(submitBtn);
      expect(apiClient.createRun).toHaveBeenCalledTimes(1);

      // Resolve backend response
      resolveRun({
        run_id: 'run-new-001',
        status: 'COMPLETED',
        overall_outcome: 'PASS',
      });

      await waitFor(() => {
        expect(handleCreated).toHaveBeenCalledWith('run-new-001');
      });
    });

    it('displays error alert if backend rejects creation', async () => {
      (apiClient.createRun as unknown as ReturnType<typeof vi.fn>).mockRejectedValue(
        new ApiClientError(500, 'Internal Evaluation Runner Error')
      );

      render(
        <RunCreateModal
          isOpen={true}
          onClose={vi.fn()}
          onRunCreated={vi.fn()}
        />
      );

      await waitFor(() => {
        expect(screen.getByText('Launch Evaluation Run')).toBeInTheDocument();
      });

      const submitBtn = screen.getByRole('button', { name: /Start Evaluation/i });
      fireEvent.click(submitBtn);

      await waitFor(() => {
        expect(screen.getByText(/Internal Evaluation Runner Error/i)).toBeInTheDocument();
      });
    });
  });

  /* =========================================================================
     2. Evaluation Run History Page (/runs)
     ========================================================================= */
  describe('Run History Page (Runs.tsx)', () => {
    it('renders empty state when no runs exist in SQLite', async () => {
      (apiClient.listRuns as unknown as ReturnType<typeof vi.fn>).mockResolvedValue([]);

      render(
        <MemoryRouter initialEntries={['/runs']}>
          <Runs />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('No Evaluation Runs Yet')).toBeInTheDocument();
      });
      expect(screen.getByRole('button', { name: /Launch Evaluation Run/i })).toBeInTheDocument();
    });

    it('renders run history from actual mocked API response shapes', async () => {
      render(
        <MemoryRouter initialEntries={['/runs']}>
          <Runs />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('run-test-uuid-001')).toBeInTheDocument();
      });

      expect(screen.getByText('COMPLETED')).toBeInTheDocument();
      expect(screen.getByText('FAIL')).toBeInTheDocument();
      expect(screen.getByText('50.0/100')).toBeInTheDocument();
      expect(screen.getByText(/ASR: 50.0%/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /Refresh/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /New Evaluation/i })).toBeInTheDocument();
    });

    it('filters run history by search query', async () => {
      render(
        <MemoryRouter initialEntries={['/runs']}>
          <Runs />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText('run-test-uuid-001')).toBeInTheDocument();
      });

      const searchInput = screen.getByLabelText(/Search evaluation runs/i);
      fireEvent.change(searchInput, { target: { value: 'nonexistent-uuid' } });

      await waitFor(() => {
        expect(screen.getByText('No Matching Runs')).toBeInTheDocument();
      });
    });
  });

  /* =========================================================================
     3. Run Detail Dashboard (/runs/:runId)
     ========================================================================= */
  describe('Run Detail Dashboard (RunDetail.tsx)', () => {
    it('renders metadata, metrics, and scenario outcomes', async () => {
      render(
        <MemoryRouter initialEntries={['/runs/run-test-uuid-001']}>
          <Routes>
            <Route path="/runs/:runId" element={<RunDetail />} />
          </Routes>
        </MemoryRouter>
      );

      // Header and ID
      await waitFor(() => {
        expect(screen.getByRole('heading', { name: 'run-test-uuid-001' })).toBeInTheDocument();
      });

      // Overall Outcome & Status
      expect(screen.getByText('Status: COMPLETED')).toBeInTheDocument();

      // Top metrics strip
      expect(screen.getByText('Total Scenarios')).toBeInTheDocument();
      expect(screen.getByText('Passed')).toBeInTheDocument();
      expect(screen.getByText('Failed')).toBeInTheDocument();
      expect(screen.getByText('Errors')).toBeInTheDocument();

      // Calculated Security Metrics
      expect(screen.getByText('Security Score')).toBeInTheDocument();
      expect(screen.getByText('Attack Success Rate (ASR)')).toBeInTheDocument();
      expect(screen.getByText('Data Exposure Rate')).toBeInTheDocument();

      // Scenario results table contents
      expect(screen.getByText('Order Lookup Benign')).toBeInTheDocument();
      expect(screen.getByText('Direct Prompt Injection')).toBeInTheDocument();
      expect(screen.getByText('Malformed JSON Crash')).toBeInTheDocument();

      // Clear distinction between PASS, FAIL, and ERROR
      expect(screen.getAllByText('PASS').length).toBeGreaterThan(0);
      expect(screen.getAllByText('FAIL').length).toBeGreaterThan(0);
      expect(screen.getAllByText('ERROR').length).toBeGreaterThan(0);
    });

    it('expands scenario row to display evaluator explanation and findings', async () => {
      render(
        <MemoryRouter initialEntries={['/runs/run-test-uuid-001']}>
          <Routes>
            <Route path="/runs/:runId" element={<RunDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: 'run-test-uuid-001' })).toBeInTheDocument();
        expect(screen.getByText('Direct Prompt Injection')).toBeInTheDocument();
      });

      // Click row to expand
      fireEvent.click(screen.getByText('Direct Prompt Injection'));

      await waitFor(() => {
        expect(screen.getByText(/Agent executed unauthorized tool despite security policy/i)).toBeInTheDocument();
        expect(screen.getByText('System Prompt Protection Rule')).toBeInTheDocument();
        expect(screen.getByText(/System instructions were leaked in agent response/i)).toBeInTheDocument();
      });
    });

    it('renders chronological execution trace events with allow/deny badges', async () => {
      render(
        <MemoryRouter initialEntries={['/runs/run-test-uuid-001']}>
          <Routes>
            <Route path="/runs/:runId" element={<RunDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: 'run-test-uuid-001' })).toBeInTheDocument();
        expect(screen.getByText('Execution Trace')).toBeInTheDocument();
      });

      // Switch to Execution Trace tab
      fireEvent.click(screen.getByRole('tab', { name: /Execution Trace/i }));

      await waitFor(() => {
        expect(screen.getByText('refund_customer_order')).toBeInTheDocument();
      });

      expect(screen.getByText('AUTHORIZATION DENIED')).toBeInTheDocument();
      expect(screen.getByText('decision: denied')).toBeInTheDocument();
      expect(screen.getByText(/ORD-999/i)).toBeInTheDocument();
    });

    it('renders security findings tab accurately', async () => {
      render(
        <MemoryRouter initialEntries={['/runs/run-test-uuid-001']}>
          <Routes>
            <Route path="/runs/:runId" element={<RunDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: 'run-test-uuid-001' })).toBeInTheDocument();
        expect(screen.getByRole('tab', { name: /Security Findings/i })).toBeInTheDocument();
      });

      // Switch to findings tab
      fireEvent.click(screen.getByRole('tab', { name: /Security Findings/i }));

      await waitFor(() => {
        expect(screen.getByText('System Prompt Protection Rule')).toBeInTheDocument();
      });

      expect(screen.getByText('RULE-PROMPT-GUARD-01')).toBeInTheDocument();
      expect(screen.getByText(/System instructions were leaked in agent response/i)).toBeInTheDocument();
      expect(screen.getByText(/sec-override-system-prompt/i)).toBeInTheDocument();
    });

    it('handles 404 not found state for nonexistent run ID', async () => {
      (apiClient.getRun as unknown as ReturnType<typeof vi.fn>).mockRejectedValue(
        new ApiClientError(404, 'Evaluation run not found')
      );

      render(
        <MemoryRouter initialEntries={['/runs/non-existent-run']}>
          <Routes>
            <Route path="/runs/:runId" element={<RunDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/Evaluation Run Not Found/i)).toBeInTheDocument();
      });

      expect(screen.getByRole('button', { name: /View All Runs/i })).toBeInTheDocument();
    });

    it('handles backend error state with retry option', async () => {
      (apiClient.getRun as unknown as ReturnType<typeof vi.fn>).mockRejectedValue(
        new Error('Database lock error')
      );

      render(
        <MemoryRouter initialEntries={['/runs/run-test-uuid-001']}>
          <Routes>
            <Route path="/runs/:runId" element={<RunDetail />} />
          </Routes>
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/Database lock error/i)).toBeInTheDocument();
      });

      expect(screen.getByRole('button', { name: /Retry/i })).toBeInTheDocument();
    });
  });

  /* =========================================================================
     4. Outcome Semantics & Badge Differentiation
     ========================================================================= */
  describe('Security Verdict vs Execution Status Semantics', () => {
    it('does NOT treat ERROR or NOT_RUN as PASS', () => {
      const resultsWithAllOutcomes: ScenarioResultResponse[] = [
        {
          scenario_id: 'sec-error',
          scenario_name: 'Error Scenario',
          category: 'malformed_input',
          risk_level: 'high',
          outcome: 'ERROR',
          execution_status: 'error',
          actual_status: 'error',
          expected_status: 'denied',
          attempt_detected: false,
          violation_prevented: false,
          data_exposed: false,
          explanation: 'Evaluator threw an unhandled exception.',
          evaluated_at: '2026-10-19T10:00:00Z',
          finding_count: 0,
          findings: [],
        },
        {
          scenario_id: 'sec-notrun',
          scenario_name: 'Skipped Scenario',
          category: 'benign_task',
          risk_level: 'low',
          outcome: 'NOT_RUN',
          execution_status: 'incomplete',
          actual_status: null,
          expected_status: 'success',
          attempt_detected: false,
          violation_prevented: false,
          data_exposed: false,
          explanation: 'Scenario was skipped due to prior failure.',
          evaluated_at: '2026-10-19T10:00:00Z',
          finding_count: 0,
          findings: [],
        },
      ];

      render(
        <ScenarioResultsTable
          results={resultsWithAllOutcomes}
        />
      );

      expect(screen.getByText('ERROR')).toBeInTheDocument();
      expect(screen.getByText('NOT RUN')).toBeInTheDocument();
      // PASS should not be rendered for these scenarios
      expect(screen.queryByText('PASS')).not.toBeInTheDocument();
    });
  });
});
