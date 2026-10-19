import React from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  MinusCircle,
  Activity,
  CheckCircle2,
  XCircle,
  Percent,
  Lock,
  EyeOff,
  CheckCheck,
  Ban,
  Info,
} from 'lucide-react';
import { OutcomeBadge } from '@/components/ui/StatusBadge';
import { Badge } from '@/components/ui/Badge';
import type {
  EvaluationReport,
  MetricValue,
  CategoryMetric,
  RiskMetric,
} from '@/api/types';

interface ReportMetricsBreakdownProps {
  report: EvaluationReport;
  className?: string;
}

interface MetricCardProps {
  metricKey: string;
  metric?: MetricValue;
  icon: React.ReactNode;
  accentColor?: 'primary' | 'emerald' | 'rose' | 'amber' | 'cyan' | 'indigo' | 'blue';
}

const MetricCard: React.FC<MetricCardProps> = ({
  metric,
  icon,
  accentColor = 'primary',
}) => {
  if (!metric) {
    return null;
  }

  const isUnavailable = metric.value === null;
  const percentage = metric.value !== null ? Math.round(metric.value * 100) : null;

  const colorStyles = {
    primary: 'border-primary/30 text-primary',
    emerald: 'border-emerald-500/30 text-emerald-400',
    rose: 'border-rose-500/30 text-rose-400',
    amber: 'border-amber-500/30 text-amber-400',
    cyan: 'border-cyan-500/30 text-cyan-400',
    indigo: 'border-indigo-500/30 text-indigo-400',
    blue: 'border-blue-500/30 text-blue-400',
  }[accentColor];

  const barBgStyles = {
    primary: 'bg-primary',
    emerald: 'bg-emerald-500',
    rose: 'bg-rose-500',
    amber: 'bg-amber-500',
    cyan: 'bg-cyan-500',
    indigo: 'bg-indigo-500',
    blue: 'bg-blue-500',
  }[accentColor];

  return (
    <div className="bg-surface rounded-xl border border-surface-border p-4 flex flex-col justify-between hover:border-surface-border/80 transition-colors">
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-300 truncate" title={metric.name}>
            {metric.name}
          </span>
          <div className={`p-1.5 rounded-lg bg-surface-elevated/70 ${colorStyles}`}>
            {icon}
          </div>
        </div>

        <div className="flex items-baseline gap-2">
          <span
            className={`text-2xl font-bold font-mono ${
              isUnavailable ? 'text-slate-500' : 'text-slate-100'
            }`}
          >
            {metric.display_value}
          </span>
          <span className="text-xs font-mono text-slate-500">
            ({metric.numerator}/{metric.denominator})
          </span>
        </div>

        {/* Progress indicator when metric has a valid ratio */}
        <div className="w-full bg-surface-elevated h-1.5 rounded-full overflow-hidden">
          {percentage !== null ? (
            <div
              className={`h-full rounded-full transition-all duration-300 ${barBgStyles}`}
              style={{ width: `${Math.min(Math.max(percentage, 0), 100)}%` }}
            />
          ) : (
            <div className="h-full w-full bg-slate-800" />
          )}
        </div>

        <p className="text-[11px] text-slate-400 leading-relaxed line-clamp-2" title={metric.description}>
          {metric.description}
        </p>
      </div>

      <div className="pt-2 mt-2 border-t border-surface-border/40 flex items-center justify-between text-[10px] text-slate-500">
        <span className="font-mono truncate max-w-[150px]" title={metric.formula}>
          {metric.formula}
        </span>
        {isUnavailable ? (
          <span className="text-amber-400/80">0-denominator (N/A)</span>
        ) : (
          <span className="text-slate-400">{percentage}%</span>
        )}
      </div>
    </div>
  );
};

export const ReportMetricsBreakdown: React.FC<ReportMetricsBreakdownProps> = ({
  report,
  className = '',
}) => {
  const counts = report.summary_counts || {
    total_scenarios: 0,
    passed_count: 0,
    failed_count: 0,
    error_count: 0,
    not_run_count: 0,
  };

  const metrics = report.metrics || {};
  const categories: [string, CategoryMetric][] = Object.entries(metrics.by_category || {});
  const riskLevels: [string, RiskMetric][] = Object.entries(metrics.by_risk_level || {});
  const ruleViolations = Object.entries(metrics.violations_by_rule || {});
  const severityViolations = Object.entries(metrics.violations_by_severity || {});

  return (
    <div className={`space-y-6 ${className}`}>
      {/* 1. Summary Outcome Counts Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        <div className="bg-surface rounded-xl border border-surface-border p-4">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Total Evaluated</span>
            <Activity className="w-4 h-4 text-slate-500" />
          </div>
          <div className="mt-2 text-2xl font-bold font-mono text-slate-100">
            {counts.total_scenarios}
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5">Scenarios in test suite</div>
        </div>

        <div className="bg-surface rounded-xl border border-emerald-500/20 bg-emerald-950/10 p-4">
          <div className="flex items-center justify-between text-emerald-400 text-xs font-medium">
            <span>Passed (PASS)</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-2 text-2xl font-bold font-mono text-emerald-400">
            {counts.passed_count}
          </div>
          <div className="text-[11px] text-emerald-400/70 mt-0.5">All security checks satisfied</div>
        </div>

        <div className="bg-surface rounded-xl border border-rose-500/20 bg-rose-950/10 p-4">
          <div className="flex items-center justify-between text-rose-400 text-xs font-medium">
            <span>Failed (FAIL)</span>
            <XCircle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="mt-2 text-2xl font-bold font-mono text-rose-400">
            {counts.failed_count}
          </div>
          <div className="text-[11px] text-rose-400/70 mt-0.5">Security violations detected</div>
        </div>

        <div className="bg-surface rounded-xl border border-amber-500/20 bg-amber-950/10 p-4">
          <div className="flex items-center justify-between text-amber-400 text-xs font-medium">
            <span>Errors (ERROR)</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-2 text-2xl font-bold font-mono text-amber-400">
            {counts.error_count}
          </div>
          <div className="text-[11px] text-amber-400/70 mt-0.5">Execution/runtime faults</div>
        </div>

        <div className="bg-surface rounded-xl border border-surface-border p-4">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Not Run (NOT_RUN)</span>
            <MinusCircle className="w-4 h-4 text-slate-500" />
          </div>
          <div className="mt-2 text-2xl font-bold font-mono text-slate-400">
            {counts.not_run_count}
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5">Skipped or excluded</div>
        </div>
      </div>

      {/* 2. Suite-Level Core Security Metrics Grid */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-slate-200">Suite-Level Security Metrics</h3>
          <span className="text-xs text-slate-400">
            Overall Verdict: <OutcomeBadge outcome={report.overall_outcome} size="sm" />
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <MetricCard
            metricKey="security_score"
            metric={metrics.security_score}
            icon={<ShieldCheck className="w-4 h-4" />}
            accentColor="primary"
          />
          <MetricCard
            metricKey="overall_pass_rate"
            metric={metrics.overall_pass_rate}
            icon={<Percent className="w-4 h-4" />}
            accentColor="emerald"
          />
          <MetricCard
            metricKey="attack_success_rate"
            metric={metrics.attack_success_rate}
            icon={<ShieldAlert className="w-4 h-4" />}
            accentColor="rose"
          />
          <MetricCard
            metricKey="unauthorized_prevention_rate"
            metric={metrics.unauthorized_prevention_rate}
            icon={<Lock className="w-4 h-4" />}
            accentColor="indigo"
          />
          <MetricCard
            metricKey="sensitive_data_exposure_rate"
            metric={metrics.sensitive_data_exposure_rate}
            icon={<EyeOff className="w-4 h-4" />}
            accentColor="amber"
          />
          <MetricCard
            metricKey="benign_task_success_rate"
            metric={metrics.benign_task_success_rate}
            icon={<CheckCheck className="w-4 h-4" />}
            accentColor="cyan"
          />
          <MetricCard
            metricKey="policy_enforcement_failure_rate"
            metric={metrics.policy_enforcement_failure_rate}
            icon={<Ban className="w-4 h-4" />}
            accentColor="rose"
          />
          <MetricCard
            metricKey="run_completion_rate"
            metric={metrics.run_completion_rate}
            icon={<Activity className="w-4 h-4" />}
            accentColor="blue"
          />
        </div>
      </div>

      {/* 3. Category & Risk Breakdowns */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Category Breakdown */}
        <div className="bg-surface rounded-xl border border-surface-border p-4 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-surface-border/50">
            <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
              Category Breakdown
            </h4>
            <span className="text-xs text-slate-500 font-mono">
              {categories.length} categories
            </span>
          </div>

          {categories.length === 0 ? (
            <p className="text-xs text-slate-500 py-3 text-center">
              No category breakdowns recorded in report.
            </p>
          ) : (
            <div className="space-y-2.5">
              {categories.map(([key, cat]) => {
                const passRatePct =
                  cat.pass_rate?.value !== null && cat.pass_rate?.value !== undefined
                    ? Math.round(cat.pass_rate.value * 100)
                    : null;
                return (
                  <div
                    key={key}
                    className="p-2.5 rounded-lg bg-surface-elevated/40 border border-surface-border/40 space-y-1.5"
                  >
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-medium text-slate-200 capitalize">
                        {cat.category?.replace(/_/g, ' ') || key}
                      </span>
                      <div className="flex items-center gap-2">
                        <span className="text-slate-400 font-mono text-[11px]">
                          {cat.passed_count}/{cat.total_count} passed
                        </span>
                        <Badge
                          variant={
                            cat.failed_count > 0
                              ? 'fail'
                              : cat.error_count > 0
                              ? 'warning'
                              : 'pass'
                          }
                          size="sm"
                        >
                          {cat.pass_rate?.display_value || 'N/A'}
                        </Badge>
                      </div>
                    </div>

                    <div className="w-full bg-surface h-1 rounded-full overflow-hidden">
                      {passRatePct !== null ? (
                        <div
                          className={`h-full rounded-full transition-all ${
                            passRatePct === 100
                              ? 'bg-emerald-500'
                              : passRatePct >= 75
                              ? 'bg-primary'
                              : passRatePct >= 50
                              ? 'bg-amber-500'
                              : 'bg-rose-500'
                          }`}
                          style={{ width: `${passRatePct}%` }}
                        />
                      ) : (
                        <div className="h-full w-full bg-slate-800" />
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Risk Level Breakdown */}
        <div className="bg-surface rounded-xl border border-surface-border p-4 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-surface-border/50">
            <h4 className="text-xs font-semibold text-slate-200 uppercase tracking-wider">
              Risk Level Breakdown
            </h4>
            <span className="text-xs text-slate-500 font-mono">
              {riskLevels.length} tiers
            </span>
          </div>

          {riskLevels.length === 0 ? (
            <p className="text-xs text-slate-500 py-3 text-center">
              No risk-level breakdowns recorded in report.
            </p>
          ) : (
            <div className="space-y-2.5">
              {riskLevels.map(([key, risk]) => {
                const passRatePct =
                  risk.pass_rate?.value !== null && risk.pass_rate?.value !== undefined
                    ? Math.round(risk.pass_rate.value * 100)
                    : null;
                return (
                  <div
                    key={key}
                    className="p-2.5 rounded-lg bg-surface-elevated/40 border border-surface-border/40 space-y-1.5"
                  >
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-medium text-slate-200 uppercase font-mono text-[11px]">
                        {risk.risk_level || key}
                      </span>
                      <div className="flex items-center gap-2">
                        <span className="text-slate-400 font-mono text-[11px]">
                          {risk.passed_count}/{risk.total_count} passed
                        </span>
                        <Badge
                          variant={
                            risk.failed_count > 0
                              ? 'fail'
                              : risk.error_count > 0
                              ? 'warning'
                              : 'pass'
                          }
                          size="sm"
                        >
                          {risk.pass_rate?.display_value || 'N/A'}
                        </Badge>
                      </div>
                    </div>

                    <div className="w-full bg-surface h-1 rounded-full overflow-hidden">
                      {passRatePct !== null ? (
                        <div
                          className={`h-full rounded-full transition-all ${
                            passRatePct === 100
                              ? 'bg-emerald-500'
                              : passRatePct >= 75
                              ? 'bg-primary'
                              : passRatePct >= 50
                              ? 'bg-amber-500'
                              : 'bg-rose-500'
                          }`}
                          style={{ width: `${passRatePct}%` }}
                        />
                      ) : (
                        <div className="h-full w-full bg-slate-800" />
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* 4. Violations Summary (Rules & Severity) */}
      {(ruleViolations.length > 0 || severityViolations.length > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {ruleViolations.length > 0 && (
            <div className="bg-surface rounded-xl border border-surface-border p-4 space-y-2">
              <h4 className="text-xs font-semibold text-slate-200">Rule Violations Breakdown</h4>
              <div className="flex flex-wrap gap-2 pt-1">
                {ruleViolations.map(([rule, count]) => (
                  <div
                    key={rule}
                    className="px-2.5 py-1 rounded bg-surface-elevated border border-surface-border flex items-center gap-2 text-xs"
                  >
                    <span className="font-mono text-slate-300">{rule}</span>
                    <Badge variant={count > 0 ? 'fail' : 'default'} size="sm">
                      {count}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          )}

          {severityViolations.length > 0 && (
            <div className="bg-surface rounded-xl border border-surface-border p-4 space-y-2">
              <h4 className="text-xs font-semibold text-slate-200">Violations By Severity</h4>
              <div className="flex flex-wrap gap-2 pt-1">
                {severityViolations.map(([sev, count]) => (
                  <div
                    key={sev}
                    className="px-2.5 py-1 rounded bg-surface-elevated border border-surface-border flex items-center gap-2 text-xs"
                  >
                    <span className="capitalize font-medium text-slate-300">{sev}</span>
                    <Badge variant={count > 0 ? 'fail' : 'default'} size="sm">
                      {count}
                    </Badge>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* 5. Limitation Statement Disclaimer Banner */}
      <div className="p-3.5 rounded-lg bg-surface-elevated/40 border border-surface-border flex items-start gap-3 text-xs text-slate-400">
        <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <p className="font-semibold text-slate-300">Evaluation Scope and Limitation Disclosure</p>
          <p className="leading-relaxed">
            {report.limitation_statement ||
              'Evaluation results apply exclusively to the synthetic test suite and tested configuration. Passing synthetic scenarios does not certify that an AI agent is universally secure or resistant to novel or unrestricted real-world attacks.'}
          </p>
        </div>
      </div>
    </div>
  );
};
