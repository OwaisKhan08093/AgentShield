import React, { useState } from 'react';
import { PlayCircle, CheckCircle2, RefreshCw } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { OutcomeBadge } from '@/components/ui/StatusBadge';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorAlert } from '@/components/ui/ErrorAlert';
import { apiClient } from '@/api/client';
import type { EvaluationRunRecord } from '@/api/types';

export const RunsPlaceholder: React.FC = () => {
  const [runs, setRuns] = useState<EvaluationRunRecord[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchLiveRuns = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiClient.listRuns();
      setRuns(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to query runs from backend');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <PlayCircle className="w-5 h-5 text-indigo-400" aria-hidden="true" />
              <CardTitle>Evaluation Runs & Trace Inspector</CardTitle>
            </div>
            <Badge variant="purple" size="sm">
              PRD Days 21–22 Milestone
            </Badge>
          </div>
          <CardDescription>
            The run execution workflow, chronological trace inspector, and security findings drawer will be built in PRD
            Days 21–22.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 text-xs text-slate-300">
          <p className="leading-relaxed">
            The AgentShield backend persists all completed evaluation runs in SQLite, including per-scenario verdicts,
            findings breakdown, sanitization logs, metric calculations (ASR, PSR), and raw JSON reports exportable via{' '}
            <code className="text-brand-blue bg-surface-elevated px-1.5 py-0.5 rounded font-mono text-[11px]">
              GET /api/v1/runs/&#123;id&#125;/report.json
            </code>
            .
          </p>

          <div className="p-4 rounded-xl bg-surface-elevated border border-surface-border space-y-3">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-200">Live SQLite Storage Query</span>
              <Button
                variant="secondary"
                size="sm"
                onClick={fetchLiveRuns}
                isLoading={isLoading}
                leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
              >
                Query Completed Runs from Storage
              </Button>
            </div>

            {error && <ErrorAlert message={error} onRetry={fetchLiveRuns} />}

            {isLoading && <LoadingSpinner message="Querying GET /api/v1/runs from SQLite..." />}

            {!isLoading && runs.length === 0 && !error && (
              <p className="text-slate-400 italic py-2">
                No runs recorded in SQLite yet. Trigger an evaluation run via POST /api/v1/runs or wait for the Day 22 Run Execution Modal.
              </p>
            )}

            {!isLoading && runs.length > 0 && (
              <div className="space-y-2 pt-2">
                <div className="flex items-center gap-1.5 text-emerald-400 font-medium">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Found {runs.length} persisted evaluation run(s) in SQLite</span>
                </div>
                <div className="divide-y divide-surface-border border border-surface-border rounded-lg overflow-hidden max-h-80 overflow-y-auto">
                  {runs.map((r) => (
                    <div key={r.run_id} className="p-3 bg-surface hover:bg-surface-hover flex items-center justify-between gap-3">
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-[11px] font-semibold text-brand-blue">{r.run_id}</span>
                          <span className="text-slate-400 text-[11px]">{new Date(r.created_at).toLocaleString()}</span>
                        </div>
                        <p className="text-[11px] text-slate-300">
                          Scenarios: {r.total_scenarios} | Passed: {r.passed_count} | Failed: {r.failed_count} | Errors: {r.error_count}
                        </p>
                      </div>
                      <OutcomeBadge outcome={r.overall_outcome} />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
