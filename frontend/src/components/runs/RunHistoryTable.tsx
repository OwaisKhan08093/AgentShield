import React from 'react';
import { Link } from 'react-router-dom';
import {
  Calendar,
  ChevronRight,
  Layers,
} from 'lucide-react';
import { OutcomeBadge } from '@/components/ui/StatusBadge';
import { Button } from '@/components/ui/Button';
import type { EvaluationRunRecord } from '@/api/types';

interface RunHistoryTableProps {
  runs: EvaluationRunRecord[];
  onSelectRun?: (runId: string) => void;
}

export const RunHistoryTable: React.FC<RunHistoryTableProps> = ({ runs }) => {
  if (runs.length === 0) {
    return null;
  }

  const formatDate = (isoString?: string) => {
    if (!isoString) return '—';
    try {
      const d = new Date(isoString);
      return d.toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return isoString;
    }
  };

  return (
    <div className="w-full overflow-hidden rounded-xl border border-surface-border bg-surface">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm" role="table" aria-label="Evaluation runs history table">
          <thead className="bg-surface-elevated/80 border-b border-surface-border text-xs uppercase tracking-wider text-slate-400 select-none">
            <tr>
              <th scope="col" className="py-3.5 px-4 font-semibold">Run ID</th>
              <th scope="col" className="py-3.5 px-4 font-semibold">Outcome</th>
              <th scope="col" className="py-3.5 px-4 font-semibold">Status</th>
              <th scope="col" className="py-3.5 px-4 font-semibold">Started</th>
              <th scope="col" className="py-3.5 px-4 font-semibold text-center">Scenarios</th>
              <th scope="col" className="py-3.5 px-4 font-semibold text-center">Score / ASR</th>
              <th scope="col" className="py-3.5 px-4 font-semibold text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-border/50 text-slate-300">
            {runs.map((run) => {
              const securityScore = run.metrics_summary?.security_score?.display_value;
              const asr = run.metrics_summary?.attack_success_rate?.display_value;

              return (
                <tr
                  key={run.run_id}
                  className="hover:bg-surface-elevated/40 transition-colors group"
                >
                  {/* Run ID */}
                  <td className="py-3.5 px-4 font-mono text-xs">
                    <Link
                      to={`/runs/${run.run_id}`}
                      className="text-primary hover:text-primary-hover hover:underline inline-flex items-center gap-1.5 focus:outline-none focus:ring-1 focus:ring-primary rounded font-medium"
                      aria-label={`View details for run ${run.run_id}`}
                    >
                      <Layers className="w-3.5 h-3.5 shrink-0 text-slate-400 group-hover:text-primary" />
                      <span>{run.run_id}</span>
                    </Link>
                    <div className="text-[11px] text-slate-500 font-sans mt-0.5">
                      Suite v{run.suite_version} • eval v{run.evaluator_version}
                    </div>
                  </td>

                  {/* Outcome */}
                  <td className="py-3.5 px-4">
                    <OutcomeBadge outcome={run.overall_outcome} size="sm" />
                  </td>

                  {/* Execution Status */}
                  <td className="py-3.5 px-4">
                    <span className="inline-flex items-center gap-1 text-xs text-slate-300 font-medium">
                      <span
                        className={`w-1.5 h-1.5 rounded-full ${
                          run.status === 'COMPLETED'
                            ? 'bg-emerald-400'
                            : run.status === 'RUNNING'
                            ? 'bg-blue-400 animate-pulse'
                            : 'bg-rose-400'
                        }`}
                      />
                      {run.status}
                    </span>
                  </td>

                  {/* Started At */}
                  <td className="py-3.5 px-4 text-xs text-slate-400 whitespace-nowrap">
                    <span className="inline-flex items-center gap-1.5">
                      <Calendar className="w-3.5 h-3.5 text-slate-500" />
                      {formatDate(run.started_at || run.created_at)}
                    </span>
                  </td>

                  {/* Scenario Breakdown */}
                  <td className="py-3.5 px-4 text-center">
                    <div className="inline-flex items-center gap-1.5 text-xs">
                      <span className="font-semibold text-slate-200" title="Total Scenarios">
                        {run.total_scenarios}
                      </span>
                      <span className="text-slate-600">/</span>
                      <span className="text-emerald-400 font-medium" title="Passed">
                        {run.passed_count}P
                      </span>
                      <span className="text-slate-600">•</span>
                      <span className="text-rose-400 font-medium" title="Failed">
                        {run.failed_count}F
                      </span>
                      {run.error_count > 0 && (
                        <>
                          <span className="text-slate-600">•</span>
                          <span className="text-amber-400 font-medium" title="Errors">
                            {run.error_count}E
                          </span>
                        </>
                      )}
                      {run.not_run_count > 0 && (
                        <>
                          <span className="text-slate-600">•</span>
                          <span className="text-slate-500 font-medium" title="Not Run">
                            {run.not_run_count}NR
                          </span>
                        </>
                      )}
                    </div>
                  </td>

                  {/* Score / ASR */}
                  <td className="py-3.5 px-4 text-center">
                    <div className="inline-flex flex-col items-center">
                      {securityScore ? (
                        <span className="font-semibold text-xs text-slate-200">
                          {securityScore}
                        </span>
                      ) : (
                        <span className="text-xs text-slate-500">—</span>
                      )}
                      {asr && (
                        <span className="text-[10px] text-slate-400">
                          ASR: {asr}
                        </span>
                      )}
                    </div>
                  </td>

                  {/* Actions */}
                  <td className="py-3.5 px-4 text-right">
                    <Link to={`/runs/${run.run_id}`}>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="gap-1 text-xs text-slate-300 hover:text-white"
                        aria-label={`Inspect run ${run.run_id}`}
                      >
                        Inspect
                        <ChevronRight className="w-3.5 h-3.5" />
                      </Button>
                    </Link>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
