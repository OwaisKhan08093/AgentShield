/**
 * TypeScript domain and API schemas for AgentShield.
 * Faithfully mirrors the FastAPI and Pydantic v2 schemas from backend/app/api/schemas.py.
 */

export type ScenarioCategory =
  | 'benign_task'
  | 'unauthorized_access'
  | 'approval_bypass'
  | 'data_exposure'
  | 'malformed_input'
  | 'direct_injection'
  | 'indirect_injection';

export type RiskLevel =
  | 'informational'
  | 'low'
  | 'medium'
  | 'high'
  | 'critical'
  | 'INFORMATIONAL'
  | 'LOW'
  | 'MEDIUM'
  | 'HIGH'
  | 'CRITICAL'
  | 'info'
  | 'INFO';

export type EvaluationOutcome =
  | 'pass'
  | 'fail'
  | 'error'
  | 'not_run'
  | 'PASS'
  | 'FAIL'
  | 'ERROR'
  | 'NOT_RUN';

export type ScenarioExecutionStatus =
  | 'completed'
  | 'error'
  | 'incomplete';

export type ExecutionStatus =
  | 'success'
  | 'denied'
  | 'error';

export type TraceEventType =
  | 'request'
  | 'tool_call'
  | 'tool_result'
  | 'response';

export interface ExpectedBehavior {
  expected_status: ExecutionStatus;
  must_have_authorization_denial: boolean;
  must_not_expose_resource_owner?: string | null;
  must_not_return_order_details: boolean;
  expected_tool_name?: string | null;
  description?: string | null;
}

export interface ScenarioSummaryResponse {
  scenario_id: string;
  name: string;
  category: ScenarioCategory;
  description: string;
  security_objective: string;
  risk_level: RiskLevel;
  tags: string[];
  version: number;
  enabled: boolean;
}

export interface ScenarioDetailResponse extends ScenarioSummaryResponse {
  expected_behavior: ExpectedBehavior;
  success_condition: string;
  failure_condition: string;
}

export interface RunOptions {
  continue_on_error: boolean;
  record_trace: boolean;
  timeout_seconds?: number | null;
}

export interface CreateRunRequest {
  suite_id?: string;
  agent_id?: string;
  scenario_ids?: string[] | null;
  options?: RunOptions;
}

export interface SummaryCounts {
  total_scenarios: number;
  passed_count: number;
  failed_count: number;
  error_count: number;
  not_run_count: number;
}

export interface MetricValue {
  name: string;
  numerator: number;
  denominator: number;
  value: number | null;
  display_value: string;
  description: string;
  formula: string;
}

export interface RunCreateResponse {
  run_id: string;
  report_id: string;
  suite_id: string;
  status: string;
  overall_outcome: EvaluationOutcome;
  started_at: string;
  completed_at: string;
  total_scenarios: number;
  passed_count: number;
  failed_count: number;
  error_count: number;
  not_run_count: number;
  summary_counts: SummaryCounts;
  metrics_summary: Record<string, MetricValue>;
}

export interface EvaluationRunRecord {
  run_id: string;
  report_id: string;
  suite_id?: string;
  suite_version: number;
  evaluator_version: string;
  status: string;
  overall_outcome: EvaluationOutcome;
  started_at: string;
  completed_at: string;
  created_at: string;
  total_scenarios: number;
  passed_count: number;
  failed_count: number;
  error_count: number;
  not_run_count: number;
  metrics_summary: Record<string, MetricValue>;
}

export interface FindingSummaryResponse {
  finding_id: string;
  rule_id: string;
  rule_name: string;
  outcome: EvaluationOutcome;
  severity: RiskLevel;
  message: string;
  timestamp: string;
}

export interface ScenarioResultResponse {
  scenario_id: string;
  scenario_name: string;
  category: ScenarioCategory;
  risk_level: RiskLevel;
  outcome: EvaluationOutcome;
  execution_status: ScenarioExecutionStatus;
  actual_status: ExecutionStatus | null;
  expected_status: ExecutionStatus;
  attempt_detected: boolean;
  violation_prevented: boolean;
  data_exposed: boolean;
  explanation: string;
  evaluated_at: string;
  duration_ms?: number | null;
  finding_count: number;
  findings: FindingSummaryResponse[];
}

export interface TraceEvent {
  event_id: string;
  sequence: number;
  event_type: TraceEventType;
  tool_name?: string | null;
  decision?: string | null;
  is_denied: boolean;
  sanitized_payload?: Record<string, unknown> | null;
  timestamp: string;
}

export interface Finding {
  finding_id: string;
  scenario_id: string;
  rule_id: string;
  rule_name: string;
  outcome: EvaluationOutcome;
  severity: RiskLevel;
  message: string;
  evidence?: Record<string, unknown>;
  timestamp: string;
}

export interface ScenarioEvaluation {
  scenario_id: string;
  scenario_name: string;
  category: ScenarioCategory;
  risk_level: RiskLevel;
  outcome: EvaluationOutcome;
  findings: Finding[];
  execution_status: ScenarioExecutionStatus;
  actual_status: ExecutionStatus | null;
  expected_status: ExecutionStatus;
  attempt_detected: boolean;
  violation_prevented: boolean;
  data_exposed: boolean;
  explanation: string;
  evaluated_at: string;
}

export interface CategoryMetric {
  category: ScenarioCategory;
  total_count: number;
  passed_count: number;
  failed_count: number;
  error_count: number;
  not_run_count: number;
  pass_rate: MetricValue;
}

export interface RiskMetric {
  risk_level: RiskLevel;
  total_count: number;
  passed_count: number;
  failed_count: number;
  error_count: number;
  not_run_count: number;
  pass_rate: MetricValue;
}

export interface EvaluationMetrics {
  overall_pass_rate: MetricValue;
  attack_success_rate: MetricValue;
  unauthorized_prevention_rate: MetricValue;
  sensitive_data_exposure_rate: MetricValue;
  benign_task_success_rate: MetricValue;
  policy_enforcement_failure_rate: MetricValue;
  run_completion_rate: MetricValue;
  security_score: MetricValue;
  by_category?: Record<string, CategoryMetric>;
  by_risk_level?: Record<string, RiskMetric>;
  violations_by_rule?: Record<string, number>;
  violations_by_severity?: Record<string, number>;
}

export interface EvaluationReport {
  report_id: string;
  run_id: string;
  evaluator_version: string;
  suite_version: number;
  started_at: string;
  completed_at: string;
  overall_outcome: EvaluationOutcome;
  summary_counts: SummaryCounts;
  metrics: EvaluationMetrics;
  scenario_evaluations: ScenarioEvaluation[];
  findings: Finding[];
  limitation_statement?: string;
}

export interface EvaluationReportExportResponse {
  schema_version: string;
  exported_at: string;
  report: EvaluationReport;
}

export interface HealthResponse {
  status: string;
}

export interface RootResponse {
  name: string;
  status: string;
  description: string;
  version: string;
}

export interface ApiErrorResponse {
  detail: string | Array<{ loc: string[]; msg: string; type: string }>;
}
