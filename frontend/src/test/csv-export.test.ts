import { describe, it, expect, vi } from 'vitest';
import {
  sanitizeCsvCell,
  serializeCsv,
  generateScenarioResultsCsv,
  generateFindingsCsv,
  generateMetricsCsv,
  downloadBlob,
} from '@/utils/csvExport';
import type {
  EvaluationReport,
  Finding,
  ScenarioEvaluation,
} from '@/api/types';

describe('CSV Export Utilities', () => {
  describe('sanitizeCsvCell', () => {
    it('handles null and undefined safely as empty string', () => {
      expect(sanitizeCsvCell(null)).toBe('');
      expect(sanitizeCsvCell(undefined)).toBe('');
    });

    it('formats booleans and numbers correctly', () => {
      expect(sanitizeCsvCell(true)).toBe('true');
      expect(sanitizeCsvCell(false)).toBe('false');
      expect(sanitizeCsvCell(42)).toBe('42');
      expect(sanitizeCsvCell(0)).toBe('0');
      expect(sanitizeCsvCell(3.1415)).toBe('3.1415');
      expect(sanitizeCsvCell(NaN)).toBe('');
      expect(sanitizeCsvCell(Infinity)).toBe('');
    });

    it('escapes embedded quotes by doubling them and wrapping in quotes', () => {
      expect(sanitizeCsvCell('He said "hello"')).toBe('"He said ""hello"""');
    });

    it('quotes strings containing commas or newlines', () => {
      expect(sanitizeCsvCell('one, two')).toBe('"one, two"');
      expect(sanitizeCsvCell("line1\nline2")).toBe('"line1\nline2"');
      expect(sanitizeCsvCell("line1\r\nline2")).toBe('"line1\r\nline2"');
    });

    it('mitigates spreadsheet formula injection by prefixing triggering characters with single quote', () => {
      // Formula triggers: =, +, -, @, \t, \r
      expect(sanitizeCsvCell('=SUM(A1:A10)')).toBe('"\'=SUM(A1:A10)"');
      expect(sanitizeCsvCell('+cmd|/C calc')).toBe('"\'=cmd|/C calc"'.replace('=', '+'));
      expect(sanitizeCsvCell('-123+456')).toBe('"\'--123+456"'.replace('--', '-'));
      expect(sanitizeCsvCell('@IMPORTXML("url")')).toBe('"\'@IMPORTXML(""url"")"');
      expect(sanitizeCsvCell("\tmalicious_tab")).toBe('"\'\tmalicious_tab"');
    });

    it('leaves standard safe strings untouched', () => {
      expect(sanitizeCsvCell('Safe_Text_123')).toBe('Safe_Text_123');
      expect(sanitizeCsvCell('SEC-001')).toBe('SEC-001');
    });
  });

  describe('serializeCsv', () => {
    it('produces RFC-4180 compliant CSV lines joined by CRLF', () => {
      const headers = ['ID', 'Name', 'Description'];
      const rows = [
        ['1', 'Test', 'Simple description'],
        ['2', 'Formula, Test', '=cmd|calc'],
      ];
      const csv = serializeCsv(headers, rows);
      expect(csv).toContain('ID,Name,Description\r\n');
      expect(csv).toContain('1,Test,Simple description\r\n');
      expect(csv).toContain('2,"Formula, Test","\'=cmd|calc"');
    });
  });

  describe('generateScenarioResultsCsv', () => {
    it('generates correct headers and rows for scenario evaluations', () => {
      const mockScenarios: ScenarioEvaluation[] = [
        {
          scenario_id: 'SEC-01',
          scenario_name: 'Direct Injection, Test',
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
          explanation: 'Attack safely blocked: =1+1',
          evaluated_at: '2026-03-31T12:00:00Z',
        },
      ];

      const csv = generateScenarioResultsCsv(mockScenarios, 'run-123');
      const lines = csv.split('\r\n');

      expect(lines[0]).toBe(
        'Run ID,Scenario ID,Scenario Name,Category,Risk Level,Outcome,Execution Status,Actual Status,Expected Status,Attempt Detected,Violation Prevented,Data Exposed,Findings Count,Explanation,Evaluated At'
      );
      expect(lines[1]).toContain('run-123');
      expect(lines[1]).toContain('SEC-01');
      expect(lines[1]).toContain('"Direct Injection, Test"');
      expect(lines[1]).toContain('direct_injection');
      expect(lines[1]).toContain('high');
      expect(lines[1]).toContain('pass');
      expect(lines[1]).toContain('completed');
      expect(lines[1]).toContain('denied');
      expect(lines[1]).toContain('true');
      expect(lines[1]).toContain('false');
      expect(lines[1]).toContain('Attack safely blocked: =1+1');
      expect(lines[1]).toContain('2026-03-31T12:00:00Z');
    });

    it('handles empty scenarios list gracefully', () => {
      const csv = generateScenarioResultsCsv([], 'run-empty');
      expect(csv).toContain('Run ID,Scenario ID,Scenario Name');
      expect(csv.split('\r\n').length).toBe(1);
    });
  });

  describe('generateFindingsCsv', () => {
    it('generates findings CSV with correct headers and data', () => {
      const mockFindings: Finding[] = [
        {
          finding_id: 'FIND-001',
          scenario_id: 'SEC-02',
          rule_id: 'RULE-AUTHZ-001',
          rule_name: 'Tool Authorization Check',
          severity: 'critical',
          outcome: 'fail',
          message: 'Agent invoked restricted tool "@admin_exec"',
          evidence: {},
          timestamp: '2026-03-31T12:01:00Z',
        },
      ];

      const csv = generateFindingsCsv(mockFindings, 'run-456');
      const lines = csv.split('\r\n');

      expect(lines[0]).toBe(
        'Run ID,Finding ID,Scenario ID,Rule ID,Rule Name,Severity,Outcome,Message,Timestamp'
      );
      expect(lines[1]).toContain('run-456');
      expect(lines[1]).toContain('FIND-001');
      expect(lines[1]).toContain('SEC-02');
      expect(lines[1]).toContain('RULE-AUTHZ-001');
      expect(lines[1]).toContain('critical');
      expect(lines[1]).toContain('fail');
      expect(lines[1]).toContain('Agent invoked restricted tool ""@admin_exec""');
    });

    it('handles empty findings without error', () => {
      const csv = generateFindingsCsv([], 'run-clean');
      expect(csv).toBe(
        'Run ID,Finding ID,Scenario ID,Rule ID,Rule Name,Severity,Outcome,Message,Timestamp'
      );
    });
  });

  describe('generateMetricsCsv', () => {
    it('exports all metric datasets including core, category, risk, and violations', () => {
      const mockReport: EvaluationReport = {
        report_id: 'rep-001',
        run_id: 'run-789',
        evaluator_version: '1.0.0',
        suite_version: 1,
        started_at: '2026-03-31T12:00:00Z',
        completed_at: '2026-03-31T12:05:00Z',
        overall_outcome: 'pass',
        summary_counts: {
          total_scenarios: 2,
          passed_count: 2,
          failed_count: 0,
          error_count: 0,
          not_run_count: 0,
        },
        metrics: {
          security_score: {
            name: 'Security Score',
            numerator: 100,
            denominator: 100,
            value: 1.0,
            display_value: '100.0%',
            formula: 'weighted_sum',
            description: 'Composite score',
          },
          overall_pass_rate: {
            name: 'Overall Pass Rate',
            numerator: 2,
            denominator: 2,
            value: 1.0,
            display_value: '100.0%',
            formula: 'passed / total',
            description: 'Pass rate',
          },
          attack_success_rate: {
            name: 'Attack Success Rate',
            numerator: 0,
            denominator: 2,
            value: 0.0,
            display_value: '0.0%',
            formula: 'attacks_succeeded / attack_scenarios',
            description: 'ASR',
          },
          unauthorized_prevention_rate: {
            name: 'Unauthorized Prevention Rate',
            numerator: 2,
            denominator: 2,
            value: 1.0,
            display_value: '100.0%',
            formula: 'prevented / attempted',
            description: 'Prevention rate',
          },
          sensitive_data_exposure_rate: {
            name: 'Data Exposure Rate',
            numerator: 0,
            denominator: 2,
            value: 0.0,
            display_value: '0.0%',
            formula: 'leaked / total',
            description: 'Exposure rate',
          },
          benign_task_success_rate: {
            name: 'Benign Task Success Rate',
            numerator: 0,
            denominator: 0,
            value: null,
            display_value: 'N/A',
            formula: 'benign_passed / benign_total',
            description: 'Zero denominator benign rate',
          },
          policy_enforcement_failure_rate: {
            name: 'Policy Enforcement Failure Rate',
            numerator: 0,
            denominator: 2,
            value: 0.0,
            display_value: '0.0%',
            formula: 'failures / total',
            description: 'Failure rate',
          },
          run_completion_rate: {
            name: 'Run Completion Rate',
            numerator: 2,
            denominator: 2,
            value: 1.0,
            display_value: '100.0%',
            formula: 'completed / total',
            description: 'Completion rate',
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
          },
          by_risk_level: {
            high: {
              risk_level: 'high',
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
                description: 'Risk pass rate',
              },
            },
          },
          violations_by_rule: {
            'RULE-AUTHZ-001': 0,
          },
          violations_by_severity: {
            critical: 0,
          },
        },
        scenario_evaluations: [],
        findings: [],
      };

      const csv = generateMetricsCsv(mockReport);
      expect(csv).toContain('Core Metric,security_score,Security Score,100,100,1,100.0%');
      expect(csv).toContain('Core Metric,benign_task_success_rate,Benign Task Success Rate,0,0,,N/A');
      expect(csv).toContain('Category Breakdown,direct_injection,direct_injection,2,2,1,100.0%');
      expect(csv).toContain('Risk Level Breakdown,high,high,2,2,1,100.0%');
      expect(csv).toContain('Rule Violations,RULE-AUTHZ-001,RULE-AUTHZ-001,0,2,0,0');
      expect(csv).toContain('Severity Breakdown,critical,critical,0,0,0,0');
    });
  });

  describe('downloadBlob', () => {
    it('creates object URL and triggers click on simulated anchor', () => {
      const mockCreateObjectURL = vi.fn().mockReturnValue('blob:http://localhost/test-uuid');
      const mockRevokeObjectURL = vi.fn();
      window.URL.createObjectURL = mockCreateObjectURL;
      window.URL.revokeObjectURL = mockRevokeObjectURL;

      const clickSpy = vi.fn();
      const appendChildSpy = vi.spyOn(document.body, 'appendChild');
      const removeChildSpy = vi.spyOn(document.body, 'removeChild');

      // Mock createElement for anchor
      const originalCreateElement = document.createElement.bind(document);
      vi.spyOn(document, 'createElement').mockImplementation((tagName: string) => {
        const el = originalCreateElement(tagName);
        if (tagName.toLowerCase() === 'a') {
          el.click = clickSpy;
        }
        return el;
      });

      downloadBlob('test-results.csv', 'Col1,Col2\r\nVal1,Val2');

      expect(mockCreateObjectURL).toHaveBeenCalled();
      expect(appendChildSpy).toHaveBeenCalled();
      expect(clickSpy).toHaveBeenCalled();
      expect(removeChildSpy).toHaveBeenCalled();
      expect(mockRevokeObjectURL).toHaveBeenCalledWith('blob:http://localhost/test-uuid');

      vi.restoreAllMocks();
    });
  });
});
