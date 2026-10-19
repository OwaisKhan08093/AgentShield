import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { JsonReportVisualizer } from '@/components/runs/JsonReportVisualizer';
import { ReportMetricsBreakdown } from '@/components/runs/ReportMetricsBreakdown';
import { ReportExportControls } from '@/components/runs/ReportExportControls';
import { RunDetail } from '@/pages/RunDetail';
import type {
  EvaluationReport,
  EvaluationReportExportResponse,
} from '@/api/types';

const mockReport: EvaluationReport = {
  report_id: 'rep-test-001',
  run_id: 'run-test-123',
  evaluator_version: '1.0.0',
  suite_version: 1,
  started_at: '2026-03-31T12:00:00Z',
  completed_at: '2026-03-31T12:05:00Z',
  overall_outcome: 'pass',
  summary_counts: {
    total_scenarios: 4,
    passed_count: 3,
    failed_count: 1,
    error_count: 0,
    not_run_count: 0,
  },
  metrics: {
    security_score: {
      name: 'Composite Security Score',
      numerator: 85,
      denominator: 100,
      value: 0.85,
      display_value: '85.0%',
      formula: 'weighted_sum',
      description: 'Normalized weighted security score',
    },
    overall_pass_rate: {
      name: 'Overall Pass Rate',
      numerator: 3,
      denominator: 4,
      value: 0.75,
      display_value: '75.0%',
      formula: 'passed / total',
      description: 'Proportion of scenarios passing',
    },
    attack_success_rate: {
      name: 'Attack Success Rate',
      numerator: 1,
      denominator: 4,
      value: 0.25,
      display_value: '25.0%',
      formula: 'bypassed / attacks',
      description: 'Rate of successful adversary exploits',
    },
    unauthorized_prevention_rate: {
      name: 'Unauthorized Prevention Rate',
      numerator: 3,
      denominator: 4,
      value: 0.75,
      display_value: '75.0%',
      formula: 'blocked / attempted',
      description: 'Rate of unauthorized tools blocked',
    },
    sensitive_data_exposure_rate: {
      name: 'Data Exposure Rate',
      numerator: 0,
      denominator: 4,
      value: 0.0,
      display_value: '0.0%',
      formula: 'leaked / total',
      description: 'Scenarios that leaked secrets',
    },
    benign_task_success_rate: {
      name: 'Benign Task Success Rate',
      numerator: 0,
      denominator: 0,
      value: null,
      display_value: 'N/A',
      formula: 'benign_passed / benign_total',
      description: 'Zero denominator benign metric',
    },
    policy_enforcement_failure_rate: {
      name: 'Policy Enforcement Failure Rate',
      numerator: 1,
      denominator: 4,
      value: 0.25,
      display_value: '25.0%',
      formula: 'failures / total',
      description: 'Policy failure rate',
    },
    run_completion_rate: {
      name: 'Run Completion Rate',
      numerator: 4,
      denominator: 4,
      value: 1.0,
      display_value: '100.0%',
      formula: 'completed / total',
      description: 'Scenarios completed without crash',
    },
    by_category: {
      direct_injection: {
        category: 'direct_injection',
        total_count: 2,
        passed_count: 2,
        failed_count: 0,
        error_count: 0,
        not_run_count: 0,
        pass_rate: {
          name: 'Pass Rate',
          numerator: 2,
          denominator: 2,
          value: 1.0,
          display_value: '100.0%',
          formula: 'passed / total',
          description: 'Category pass rate',
        },
      },
      unauthorized_access: {
        category: 'unauthorized_access',
        total_count: 2,
        passed_count: 1,
        failed_count: 1,
        error_count: 0,
        not_run_count: 0,
        pass_rate: {
          name: 'Pass Rate',
          numerator: 1,
          denominator: 2,
          value: 0.5,
          display_value: '50.0%',
          formula: 'passed / total',
          description: 'Category pass rate',
        },
      },
    },
    by_risk_level: {
      critical: {
        risk_level: 'critical',
        total_count: 1,
        passed_count: 1,
        failed_count: 0,
        error_count: 0,
        not_run_count: 0,
        pass_rate: {
          name: 'Pass Rate',
          numerator: 1,
          denominator: 1,
          value: 1.0,
          display_value: '100.0%',
          formula: 'passed / total',
          description: 'Risk pass rate',
        },
      },
      high: {
        risk_level: 'high',
        total_count: 3,
        passed_count: 2,
        failed_count: 1,
        error_count: 0,
        not_run_count: 0,
        pass_rate: {
          name: 'Pass Rate',
          numerator: 2,
          denominator: 3,
          value: 0.67,
          display_value: '66.7%',
          formula: 'passed / total',
          description: 'Risk pass rate',
        },
      },
    },
    violations_by_rule: {
      'RULE-AUTHZ-001': 1,
    },
    violations_by_severity: {
      high: 1,
    },
  },
  scenario_evaluations: [
    {
      scenario_id: 'SEC-01',
      scenario_name: 'Direct Prompt Injection Test',
      category: 'direct_injection',
      risk_level: 'high',
      outcome: 'pass',
      findings: [],
      execution_status: 'completed',
      actual_status: 'denied',
      expected_status: 'denied',
      attempt_detected: true,
      violation_prevented: true,
      data_exposed: false,
      explanation: 'Prompt injection was recognized and blocked.',
      evaluated_at: '2026-03-31T12:01:00Z',
    },
    {
      scenario_id: 'SEC-02',
      scenario_name: 'Privilege Escalation Test',
      category: 'unauthorized_access',
      risk_level: 'high',
      outcome: 'fail',
      findings: [
        {
          finding_id: 'FIND-001',
          scenario_id: 'SEC-02',
          rule_id: 'RULE-AUTHZ-001',
          rule_name: 'Tool Authorization Check',
          severity: 'high',
          outcome: 'fail',
          message: 'Tool call exceeded granted permissions',
          evidence: {},
          timestamp: '2026-03-31T12:02:00Z',
        },
      ],
      execution_status: 'completed',
      actual_status: 'success',
      expected_status: 'denied',
      attempt_detected: true,
      violation_prevented: false,
      data_exposed: false,
      explanation: 'Tool call was improperly permitted.',
      evaluated_at: '2026-03-31T12:02:00Z',
    },
  ],
  findings: [
    {
      finding_id: 'FIND-001',
      scenario_id: 'SEC-02',
      rule_id: 'RULE-AUTHZ-001',
      rule_name: 'Tool Authorization Check',
      severity: 'high',
      outcome: 'fail',
      message: 'Tool call exceeded granted permissions',
      evidence: {},
      timestamp: '2026-03-31T12:02:00Z',
    },
  ],
  limitation_statement:
    'Evaluation results apply exclusively to the synthetic test suite and tested configuration. Passing synthetic scenarios does not certify that an AI agent is universally secure.',
};

const mockExportResponse: EvaluationReportExportResponse = {
  schema_version: '1.0.0',
  exported_at: '2026-03-31T12:05:00Z',
  report: mockReport,
};

describe('PRD Day 23: Machine-Readable JSON Report Visualizer, Metrics & Exports', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  describe('JsonReportVisualizer Component', () => {
    it('renders metadata header with schema version, report ID, evaluator version, and export time', () => {
      render(
        <JsonReportVisualizer
          runId="run-test-123"
          exportResponse={mockExportResponse}
        />
      );

      expect(screen.getByText(/Schema v1.0.0/i)).toBeInTheDocument();
      expect(screen.getByText(/Report ID: rep-test-001/i)).toBeInTheDocument();
      expect(screen.getByText(/Evaluator v1.0.0/i)).toBeInTheDocument();
      expect(screen.getByText(/Suite v1/i)).toBeInTheDocument();
      expect(screen.getByText(/Endpoint: GET \/api\/v1\/runs\/run-test-123\/report.json/i)).toBeInTheDocument();
    });

    it('toggles between Tree View and Raw JSON View', () => {
      render(
        <JsonReportVisualizer
          runId="run-test-123"
          exportResponse={mockExportResponse}
        />
      );

      // Default is Tree View
      expect(screen.getByLabelText(/Interactive Tree View/i)).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/Search keys or values/i)).toBeInTheDocument();

      // Click Raw JSON view button
      fireEvent.click(screen.getByRole('button', { name: /Raw Formatted JSON View/i }));

      // Now preformatted JSON block is rendered and tree search is hidden
      expect(screen.queryByPlaceholderText(/Search keys or values/i)).not.toBeInTheDocument();
      expect(screen.getByText(/"schema_version": "1.0.0"/i)).toBeInTheDocument();

      // Switch back to Tree view
      fireEvent.click(screen.getByRole('button', { name: /Interactive Tree View/i }));
      expect(screen.getByPlaceholderText(/Search keys or values/i)).toBeInTheDocument();
    });

    it('filters nodes based on search input', () => {
      render(
        <JsonReportVisualizer
          runId="run-test-123"
          exportResponse={mockExportResponse}
        />
      );

      const searchInput = screen.getByPlaceholderText(/Search keys or values/i);
      fireEvent.change(searchInput, { target: { value: 'security_score' } });
      expect(searchInput).toHaveValue('security_score');

      // Clear search button works
      const clearBtn = screen.getByRole('button', { name: /Clear search/i });
      fireEvent.click(clearBtn);
      expect(searchInput).toHaveValue('');
    });

    it('handles Expand All and Collapse All buttons', () => {
      render(
        <JsonReportVisualizer
          runId="run-test-123"
          exportResponse={mockExportResponse}
        />
      );

      const expandAllBtn = screen.getByRole('button', { name: /Expand all JSON nodes/i });
      fireEvent.click(expandAllBtn);

      const collapseAllBtn = screen.getByRole('button', { name: /Collapse all JSON nodes/i });
      fireEvent.click(collapseAllBtn);
    });

    it('copies JSON to clipboard with feedback', async () => {
      const writeTextMock = vi.fn().mockResolvedValue(undefined);
      Object.assign(navigator, {
        clipboard: {
          writeText: writeTextMock,
        },
      });

      render(
        <JsonReportVisualizer
          runId="run-test-123"
          exportResponse={mockExportResponse}
        />
      );

      const copyBtn = screen.getByRole('button', { name: /Copy report JSON/i });
      fireEvent.click(copyBtn);

      await waitFor(() => {
        expect(writeTextMock).toHaveBeenCalled();
        expect(screen.getByText('Copied')).toBeInTheDocument();
      });
    });

    it('renders error and loading states properly', () => {
      const { rerender } = render(
        <JsonReportVisualizer
          runId="run-test-123"
          isLoading={true}
        />
      );
      expect(screen.getByText(/Loading machine-readable evaluation report/i)).toBeInTheDocument();

      rerender(
        <JsonReportVisualizer
          runId="run-test-123"
          error="Failed to connect to backend: 500"
        />
      );
      expect(screen.getByText(/Evaluation Report Retrieval Error/i)).toBeInTheDocument();
      expect(screen.getByText(/Failed to connect to backend: 500/i)).toBeInTheDocument();
    });
  });

  describe('ReportMetricsBreakdown Component', () => {
    it('renders summary counts preserving PASS, FAIL, ERROR, and NOT_RUN distinction', () => {
      render(<ReportMetricsBreakdown report={mockReport} />);

      expect(screen.getByText('Total Evaluated')).toBeInTheDocument();
      expect(screen.getByText('Passed (PASS)')).toBeInTheDocument();
      expect(screen.getByText('Failed (FAIL)')).toBeInTheDocument();
      expect(screen.getByText('Errors (ERROR)')).toBeInTheDocument();
      expect(screen.getByText('Not Run (NOT_RUN)')).toBeInTheDocument();

      expect(screen.getAllByText('3').length).toBeGreaterThanOrEqual(1); // Passed
      expect(screen.getAllByText('1').length).toBeGreaterThanOrEqual(1); // Failed
    });

    it('renders suite-level metrics and handles zero-denominator safely', () => {
      render(<ReportMetricsBreakdown report={mockReport} />);

      expect(screen.getByText('Composite Security Score')).toBeInTheDocument();
      expect(screen.getByText('85.0%')).toBeInTheDocument();
      expect(screen.getByText('(85/100)')).toBeInTheDocument();

      expect(screen.getByText('Overall Pass Rate')).toBeInTheDocument();
      expect(screen.getAllByText('75.0%').length).toBeGreaterThanOrEqual(1);

      expect(screen.getByText('Attack Success Rate')).toBeInTheDocument();
      expect(screen.getAllByText('25.0%').length).toBeGreaterThanOrEqual(1);

      // Zero-denominator benign rate should render N/A safely without crashing
      expect(screen.getByText('Benign Task Success Rate')).toBeInTheDocument();
      expect(screen.getAllByText('N/A').length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText('(0/0)')).toBeInTheDocument();
    });

    it('renders category and risk level breakdowns', () => {
      render(<ReportMetricsBreakdown report={mockReport} />);

      expect(screen.getByText(/Category Breakdown/i)).toBeInTheDocument();
      expect(screen.getByText(/direct injection/i)).toBeInTheDocument();
      expect(screen.getByText(/unauthorized access/i)).toBeInTheDocument();

      expect(screen.getByText(/Risk Level Breakdown/i)).toBeInTheDocument();
      expect(screen.getAllByText(/critical/i).length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText(/high/i).length).toBeGreaterThanOrEqual(1);
    });

    it('renders rule and severity violations tallies', () => {
      render(<ReportMetricsBreakdown report={mockReport} />);

      expect(screen.getByText(/Rule Violations Breakdown/i)).toBeInTheDocument();
      expect(screen.getByText('RULE-AUTHZ-001')).toBeInTheDocument();

      expect(screen.getByText(/Violations By Severity/i)).toBeInTheDocument();
    });

    it('displays evaluation limitation statement disclaimer', () => {
      render(<ReportMetricsBreakdown report={mockReport} />);

      expect(screen.getByText(/Evaluation Scope and Limitation Disclosure/i)).toBeInTheDocument();
      expect(
        screen.getByText(/Evaluation results apply exclusively to the synthetic test suite/i)
      ).toBeInTheDocument();
    });
  });

  describe('ReportExportControls Component', () => {
    it('renders export buttons and triggers downloads', () => {
      const mockCreateObjectURL = vi.fn().mockReturnValue('blob:test');
      const mockRevokeObjectURL = vi.fn();
      window.URL.createObjectURL = mockCreateObjectURL;
      window.URL.revokeObjectURL = mockRevokeObjectURL;

      render(
        <ReportExportControls
          runId="run-test-123"
          report={mockReport}
          exportData={mockExportResponse as unknown as Record<string, unknown>}
        />
      );

      // JSON report button
      const jsonBtn = screen.getByRole('button', { name: /Download raw JSON report/i });
      expect(jsonBtn).toBeEnabled();
      fireEvent.click(jsonBtn);
      expect(mockCreateObjectURL).toHaveBeenCalled();

      // Scenarios CSV button
      const scenariosBtn = screen.getByRole('button', { name: /Download scenario evaluation results CSV/i });
      expect(scenariosBtn).toBeEnabled();
      fireEvent.click(scenariosBtn);

      // Findings CSV button (has 1 finding)
      const findingsBtn = screen.getByRole('button', { name: /Download security findings CSV/i });
      expect(findingsBtn).toBeEnabled();
      expect(findingsBtn).toHaveTextContent('Findings CSV (1)');

      // Metrics CSV button
      const metricsBtn = screen.getByRole('button', { name: /Download evaluation metrics CSV/i });
      expect(metricsBtn).toBeEnabled();
      fireEvent.click(metricsBtn);
    });

    it('disables findings CSV button when there are no findings', () => {
      const cleanReport: EvaluationReport = {
        ...mockReport,
        findings: [],
      };

      render(
        <ReportExportControls
          runId="run-test-clean"
          report={cleanReport}
          exportData={{ schema_version: '1.0.0', report: cleanReport }}
        />
      );

      const findingsBtn = screen.getByRole('button', { name: /Download security findings CSV/i });
      expect(findingsBtn).toBeDisabled();
      expect(findingsBtn).toHaveTextContent('Findings CSV (0)');
    });
  });

  describe('RunDetail Page Integration with Day 23 Features', () => {
    it('loads run detail and navigates to Report & Visualizer tab', async () => {
      // Mock fetch responses for run detail, results, and report export
      vi.spyOn(globalThis, 'fetch').mockImplementation((url: string | URL | Request) => {
        const urlStr = String(url);
        if (urlStr.includes('/runs/run-test-123/report.json')) {
          return Promise.resolve({
            ok: true,
            status: 200,
            headers: new Headers({ 'content-type': 'application/json' }),
            json: async () => mockExportResponse,
          } as unknown as Response);
        }
        if (urlStr.includes('/runs/run-test-123/results')) {
          return Promise.resolve({
            ok: true,
            status: 200,
            headers: new Headers({ 'content-type': 'application/json' }),
            json: async () => mockReport.scenario_evaluations,
          } as unknown as Response);
        }
        if (urlStr.includes('/runs/run-test-123')) {
          return Promise.resolve({
            ok: true,
            status: 200,
            headers: new Headers({ 'content-type': 'application/json' }),
            json: async () => ({
              run_id: 'run-test-123',
              report_id: 'rep-test-001',
              suite_version: 1,
              evaluator_version: '1.0.0',
              status: 'completed',
              overall_outcome: 'pass',
              started_at: '2026-03-31T12:00:00Z',
              completed_at: '2026-03-31T12:05:00Z',
              created_at: '2026-03-31T12:00:00Z',
              total_scenarios: 4,
              passed_count: 3,
              failed_count: 1,
              error_count: 0,
              not_run_count: 0,
              metrics_summary: mockReport.metrics,
            }),
          } as unknown as Response);
        }
        return Promise.resolve({
          ok: true,
          status: 200,
          headers: new Headers({ 'content-type': 'application/json' }),
          json: async () => [],
        } as unknown as Response);
      });

      render(
        <MemoryRouter initialEntries={['/runs/run-test-123']}>
          <Routes>
            <Route path="/runs/:runId" element={<RunDetail />} />
          </Routes>
        </MemoryRouter>
      );

      // Wait for run header to load
      await waitFor(() => {
        expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('run-test-123');
      });

      // Switch to Report & Visualizer tab
      const reportTabBtn = screen.getByRole('tab', { name: /Report & Visualizer/i });
      fireEvent.click(reportTabBtn);

      // Verify export controls and visualizer rendered inside tab
      await waitFor(() => {
        expect(screen.getByRole('toolbar', { name: /Report export and copy actions/i })).toBeInTheDocument();
        expect(screen.getByText(/Suite-Level Security Metrics/i)).toBeInTheDocument();
        expect(screen.getByText(/Schema v1.0.0/i)).toBeInTheDocument();
      });
    });
  });
});
