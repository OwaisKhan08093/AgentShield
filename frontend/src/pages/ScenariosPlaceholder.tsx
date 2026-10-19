import React, { useState } from 'react';
import { FileCode, CheckCircle2, RefreshCw } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { SeverityBadge } from '@/components/ui/StatusBadge';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorAlert } from '@/components/ui/ErrorAlert';
import { apiClient } from '@/api/client';
import type { ScenarioSummaryResponse } from '@/api/types';

export const ScenariosPlaceholder: React.FC = () => {
  const [scenarios, setScenarios] = useState<ScenarioSummaryResponse[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchLiveScenarios = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiClient.listScenarios();
      setScenarios(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch scenarios from backend');
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
              <FileCode className="w-5 h-5 text-brand-blue" aria-hidden="true" />
              <CardTitle>Scenario Catalog & Explorer</CardTitle>
            </div>
            <Badge variant="purple" size="sm">
              PRD Day 20 Milestone
            </Badge>
          </div>
          <CardDescription>
            The comprehensive scenario filtering, category inspector, and definition browser will be fully assembled in
            PRD Day 20.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 text-xs text-slate-300">
          <p className="leading-relaxed">
            The AgentShield backend currently provides <strong>16 canonical security benchmark scenarios</strong> covering
            positive controls, horizontal privilege escalation (IDOR), refund threshold bypass, malformed input payloads,
            and direct/indirect prompt injection resistance.
          </p>

          <div className="p-4 rounded-xl bg-surface-elevated border border-surface-border space-y-3">
            <div className="flex items-center justify-between">
              <span className="font-semibold text-slate-200">Live API Integration Test</span>
              <Button
                variant="secondary"
                size="sm"
                onClick={fetchLiveScenarios}
                isLoading={isLoading}
                leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
              >
                Fetch Live Scenarios from Backend
              </Button>
            </div>

            {error && <ErrorAlert message={error} onRetry={fetchLiveScenarios} />}

            {isLoading && <LoadingSpinner message="Querying GET /api/v1/scenarios from backend..." />}

            {!isLoading && scenarios.length > 0 && (
              <div className="space-y-2 pt-2">
                <div className="flex items-center gap-1.5 text-emerald-400 font-medium">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Successfully retrieved {scenarios.length} scenarios from backend API</span>
                </div>
                <div className="divide-y divide-surface-border border border-surface-border rounded-lg overflow-hidden max-h-80 overflow-y-auto">
                  {scenarios.map((s) => (
                    <div key={s.scenario_id} className="p-3 bg-surface hover:bg-surface-hover flex items-center justify-between gap-3">
                      <div className="space-y-0.5">
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-[11px] font-semibold text-brand-blue">{s.scenario_id}</span>
                          <span className="text-slate-200 font-medium">{s.name}</span>
                        </div>
                        <p className="text-[11px] text-slate-400">{s.description}</p>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <Badge variant="outline" size="sm">{s.category}</Badge>
                        <SeverityBadge severity={s.risk_level} />
                      </div>
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
