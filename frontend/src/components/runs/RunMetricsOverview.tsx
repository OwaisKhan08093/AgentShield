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
} from 'lucide-react';
import type { EvaluationRunRecord } from '@/api/types';

interface RunMetricsOverviewProps {
  run: EvaluationRunRecord;
}

export const RunMetricsOverview: React.FC<RunMetricsOverviewProps> = ({ run }) => {
  const metrics = run.metrics_summary || {};

  const securityScore = metrics.security_score;
  const attackSuccessRate = metrics.attack_success_rate;
  const sensitiveDataExposureRate = metrics.sensitive_data_exposure_rate;
  const passRate = metrics.pass_rate;

  return (
    <div className="space-y-4">
      {/* Top Counts Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        {/* Total */}
        <div className="bg-surface rounded-xl border border-surface-border p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Total Scenarios</span>
            <Activity className="w-4 h-4 text-slate-500" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-100">
            {run.total_scenarios}
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5">
            Evaluated suite
          </div>
        </div>

        {/* Passed */}
        <div className="bg-surface rounded-xl border border-emerald-500/20 bg-emerald-950/10 p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-emerald-400 text-xs font-medium">
            <span>Passed</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-emerald-400">
            {run.passed_count}
          </div>
          <div className="text-[11px] text-emerald-400/70 mt-0.5">
            Security satisfied
          </div>
        </div>

        {/* Failed */}
        <div className="bg-surface rounded-xl border border-rose-500/20 bg-rose-950/10 p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-rose-400 text-xs font-medium">
            <span>Failed</span>
            <XCircle className="w-4 h-4 text-rose-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-rose-400">
            {run.failed_count}
          </div>
          <div className="text-[11px] text-rose-400/70 mt-0.5">
            Violations detected
          </div>
        </div>

        {/* Errors */}
        <div className="bg-surface rounded-xl border border-amber-500/20 bg-amber-950/10 p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-amber-400 text-xs font-medium">
            <span>Errors</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <div className="mt-2 text-2xl font-bold text-amber-400">
            {run.error_count}
          </div>
          <div className="text-[11px] text-amber-400/70 mt-0.5">
            Runtime exceptions
          </div>
        </div>

        {/* Not Run */}
        <div className="bg-surface rounded-xl border border-surface-border p-4 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 text-xs font-medium">
            <span>Not Run</span>
            <MinusCircle className="w-4 h-4 text-slate-500" />
          </div>
          <div className="mt-2 text-2xl font-bold text-slate-400">
            {run.not_run_count}
          </div>
          <div className="text-[11px] text-slate-500 mt-0.5">
            Skipped / Unexecuted
          </div>
        </div>
      </div>

      {/* Security Metrics Strip (Displayed only if present in API response) */}
      {Object.keys(metrics).length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {/* Security Score */}
          {securityScore && (
            <div className="bg-surface rounded-xl border border-surface-border p-4">
              <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
                <span>Security Score</span>
                <ShieldCheck className="w-4 h-4 text-primary" />
              </div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-slate-100">
                  {securityScore.display_value}
                </span>
                <span className="text-xs text-slate-500">
                  ({securityScore.numerator}/{securityScore.denominator})
                </span>
              </div>
              <p className="mt-1 text-[11px] text-slate-400 leading-tight">
                {securityScore.description || 'Normalized weighted evaluation score'}
              </p>
            </div>
          )}

          {/* Pass Rate */}
          {passRate && (
            <div className="bg-surface rounded-xl border border-surface-border p-4">
              <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
                <span>Pass Rate</span>
                <Percent className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-emerald-400">
                  {passRate.display_value}
                </span>
                <span className="text-xs text-slate-500">
                  ({passRate.numerator}/{passRate.denominator})
                </span>
              </div>
              <p className="mt-1 text-[11px] text-slate-400 leading-tight">
                {passRate.description || 'Proportion of scenarios passing all assertions'}
              </p>
            </div>
          )}

          {/* Attack Success Rate */}
          {attackSuccessRate && (
            <div className="bg-surface rounded-xl border border-surface-border p-4">
              <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
                <span>Attack Success Rate (ASR)</span>
                <ShieldAlert className="w-4 h-4 text-rose-400" />
              </div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-rose-400">
                  {attackSuccessRate.display_value}
                </span>
                <span className="text-xs text-slate-500">
                  ({attackSuccessRate.numerator}/{attackSuccessRate.denominator})
                </span>
              </div>
              <p className="mt-1 text-[11px] text-slate-400 leading-tight">
                {attackSuccessRate.description || 'Attacks that bypassed agent defenses'}
              </p>
            </div>
          )}

          {/* Sensitive Data Exposure */}
          {sensitiveDataExposureRate && (
            <div className="bg-surface rounded-xl border border-surface-border p-4">
              <div className="flex items-center justify-between text-xs text-slate-400 font-medium">
                <span>Data Exposure Rate</span>
                <AlertTriangle className="w-4 h-4 text-amber-400" />
              </div>
              <div className="mt-2 flex items-baseline gap-2">
                <span className="text-2xl font-bold text-amber-400">
                  {sensitiveDataExposureRate.display_value}
                </span>
                <span className="text-xs text-slate-500">
                  ({sensitiveDataExposureRate.numerator}/{sensitiveDataExposureRate.denominator})
                </span>
              </div>
              <p className="mt-1 text-[11px] text-slate-400 leading-tight">
                {sensitiveDataExposureRate.description || 'Scenarios leaking sensitive data'}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
