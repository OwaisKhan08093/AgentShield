/**
 * AgentShield CSV Export and Sanitization Utilities
 *
 * Provides safe RFC-4180 CSV serialization with:
 * - Proper quote and delimiter escaping
 * - Protection against CSV/Spreadsheet formula injection (neutralizing =, +, -, @, \t, \r)
 * - Deterministic column headers and predictable datasets
 * - Safe null/missing value handling
 */

import type {
  EvaluationReport,
  Finding,
  ScenarioEvaluation,
  MetricValue,
} from '@/api/types';

/**
 * Characters that trigger spreadsheet formula execution when appearing at the start of a cell.
 */
const FORMULA_INJECTION_PREFIX_REGEX = /^[=+\-@\t\r]/;

/**
 * Sanitizes a single cell value for CSV output:
 * 1. Handles null and undefined cleanly as empty string.
 * 2. Mitigates spreadsheet formula injection by prefixing triggering leading characters with a single quote (').
 * 3. Escapes embedded double-quotes by doubling them ("").
 * 4. Quotes cells containing commas, newlines, quotes, or formula-neutralized values.
 */
export function sanitizeCsvCell(value: unknown): string {
  if (value === null || value === undefined) {
    return '';
  }

  let text: string;
  if (typeof value === 'boolean') {
    text = value ? 'true' : 'false';
  } else if (typeof value === 'number') {
    text = Number.isFinite(value) ? String(value) : '';
  } else if (typeof value === 'object') {
    try {
      text = JSON.stringify(value);
    } catch {
      text = '[Object]';
    }
  } else {
    text = String(value);
  }

  let needsQuotes = false;

  // Formula injection defense: if untrusted text begins with =, +, -, @, \t, or \r
  if (FORMULA_INJECTION_PREFIX_REGEX.test(text)) {
    text = `'${text}`;
    needsQuotes = true;
  }

  // Quote escaping: double every quote
  if (text.includes('"')) {
    text = text.replace(/"/g, '""');
    needsQuotes = true;
  }

  // Quote wrapping: if comma, newline, carriage return, or leading single-quote is present
  if (
    needsQuotes ||
    text.includes(',') ||
    text.includes('\n') ||
    text.includes('\r') ||
    text.startsWith("'")
  ) {
    return `"${text}"`;
  }

  return text;
}

/**
 * Serializes a list of rows (arrays of values) into a valid RFC-4180 CSV string.
 */
export function serializeCsv(headers: string[], rows: unknown[][]): string {
  const headerLine = headers.map((h) => sanitizeCsvCell(h)).join(',');
  const rowLines = rows.map((row) => row.map((cell) => sanitizeCsvCell(cell)).join(','));
  return [headerLine, ...rowLines].join('\r\n');
}

/**
 * Generates CSV content for scenario-level evaluation results.
 */
export function generateScenarioResultsCsv(
  scenarios: ScenarioEvaluation[],
  runId: string
): string {
  const headers = [
    'Run ID',
    'Scenario ID',
    'Scenario Name',
    'Category',
    'Risk Level',
    'Outcome',
    'Execution Status',
    'Actual Status',
    'Expected Status',
    'Attempt Detected',
    'Violation Prevented',
    'Data Exposed',
    'Findings Count',
    'Explanation',
    'Evaluated At',
  ];

  const rows = (scenarios || []).map((s) => [
    runId,
    s.scenario_id,
    s.scenario_name,
    s.category,
    s.risk_level,
    s.outcome,
    s.execution_status,
    s.actual_status ?? 'N/A',
    s.expected_status,
    s.attempt_detected,
    s.violation_prevented,
    s.data_exposed,
    s.findings ? s.findings.length : 0,
    s.explanation,
    s.evaluated_at,
  ]);

  return serializeCsv(headers, rows);
}

/**
 * Generates CSV content for security findings identified during an evaluation run.
 */
export function generateFindingsCsv(findings: Finding[], runId: string): string {
  const headers = [
    'Run ID',
    'Finding ID',
    'Scenario ID',
    'Rule ID',
    'Rule Name',
    'Severity',
    'Outcome',
    'Message',
    'Timestamp',
  ];

  const rows = (findings || []).map((f) => [
    runId,
    f.finding_id,
    f.scenario_id,
    f.rule_id,
    f.rule_name,
    f.severity,
    f.outcome,
    f.message,
    f.timestamp,
  ]);

  return serializeCsv(headers, rows);
}

/**
 * Generates CSV content for evaluation metrics and breakdowns.
 */
export function generateMetricsCsv(report: EvaluationReport): string {
  const headers = [
    'Run ID',
    'Dataset',
    'Metric Key',
    'Name',
    'Numerator',
    'Denominator',
    'Value',
    'Display Value',
    'Formula',
    'Description',
  ];

  const rows: unknown[][] = [];
  const runId = report.run_id;
  const metrics = report.metrics;

  if (metrics) {
    // 1. Suite-level Core Metrics
    const coreMetrics: Array<{ key: string; metric?: MetricValue }> = [
      { key: 'security_score', metric: metrics.security_score },
      { key: 'overall_pass_rate', metric: metrics.overall_pass_rate },
      { key: 'attack_success_rate', metric: metrics.attack_success_rate },
      { key: 'unauthorized_prevention_rate', metric: metrics.unauthorized_prevention_rate },
      { key: 'sensitive_data_exposure_rate', metric: metrics.sensitive_data_exposure_rate },
      { key: 'benign_task_success_rate', metric: metrics.benign_task_success_rate },
      { key: 'policy_enforcement_failure_rate', metric: metrics.policy_enforcement_failure_rate },
      { key: 'run_completion_rate', metric: metrics.run_completion_rate },
    ];

    for (const item of coreMetrics) {
      if (item.metric) {
        rows.push([
          runId,
          'Core Metric',
          item.key,
          item.metric.name,
          item.metric.numerator,
          item.metric.denominator,
          item.metric.value !== null ? item.metric.value : '',
          item.metric.display_value,
          item.metric.formula,
          item.metric.description,
        ]);
      }
    }

    // 2. Category Breakdown
    if (metrics.by_category) {
      for (const [catKey, catMetric] of Object.entries(metrics.by_category)) {
        rows.push([
          runId,
          'Category Breakdown',
          catKey,
          catMetric.category,
          catMetric.passed_count,
          catMetric.total_count,
          catMetric.pass_rate?.value !== null ? catMetric.pass_rate?.value : '',
          catMetric.pass_rate?.display_value ?? 'N/A',
          catMetric.pass_rate?.formula ?? 'passed_count / total_count',
          `Passed: ${catMetric.passed_count}, Failed: ${catMetric.failed_count}, Error: ${catMetric.error_count}, Not Run: ${catMetric.not_run_count}`,
        ]);
      }
    }

    // 3. Risk Level Breakdown
    if (metrics.by_risk_level) {
      for (const [riskKey, riskMetric] of Object.entries(metrics.by_risk_level)) {
        rows.push([
          runId,
          'Risk Level Breakdown',
          riskKey,
          riskMetric.risk_level,
          riskMetric.passed_count,
          riskMetric.total_count,
          riskMetric.pass_rate?.value !== null ? riskMetric.pass_rate?.value : '',
          riskMetric.pass_rate?.display_value ?? 'N/A',
          riskMetric.pass_rate?.formula ?? 'passed_count / total_count',
          `Passed: ${riskMetric.passed_count}, Failed: ${riskMetric.failed_count}, Error: ${riskMetric.error_count}, Not Run: ${riskMetric.not_run_count}`,
        ]);
      }
    }

    // 4. Rule Violations Breakdown
    if (metrics.violations_by_rule) {
      for (const [ruleId, count] of Object.entries(metrics.violations_by_rule)) {
        rows.push([
          runId,
          'Rule Violations',
          ruleId,
          ruleId,
          count,
          report.summary_counts?.total_scenarios ?? '',
          count,
          String(count),
          'violations_count',
          `Security rule violation occurrences for ${ruleId}`,
        ]);
      }
    }

    // 5. Severity Violations Breakdown
    if (metrics.violations_by_severity) {
      for (const [severity, count] of Object.entries(metrics.violations_by_severity)) {
        rows.push([
          runId,
          'Severity Breakdown',
          severity,
          severity,
          count,
          report.findings?.length ?? '',
          count,
          String(count),
          'violations_count',
          `Finding occurrences with severity ${severity}`,
        ]);
      }
    }
  }

  return serializeCsv(headers, rows);
}

/**
 * Triggers a client-side download of a UTF-8 text or CSV payload.
 */
export function downloadBlob(
  filename: string,
  content: string,
  mimeType = 'text/csv;charset=utf-8;'
): void {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
