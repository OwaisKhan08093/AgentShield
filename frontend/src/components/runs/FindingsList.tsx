import React, { useState } from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  Clock,
  Search,
} from 'lucide-react';
import { SeverityBadge, OutcomeBadge } from '@/components/ui/StatusBadge';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { EmptyState } from '@/components/ui/EmptyState';
import type { ScenarioResultResponse, FindingSummaryResponse } from '@/api/types';

interface FlattenedFinding extends FindingSummaryResponse {
  scenario_id: string;
  scenario_name: string;
}

interface FindingsListProps {
  results: ScenarioResultResponse[];
  onSelectScenario?: (scenarioId: string) => void;
}

export const FindingsList: React.FC<FindingsListProps> = ({
  results,
  onSelectScenario,
}) => {
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Flatten all findings across scenario results
  const allFindings: FlattenedFinding[] = [];
  results.forEach((res) => {
    if (res.findings && Array.isArray(res.findings)) {
      res.findings.forEach((f) => {
        allFindings.push({
          ...f,
          scenario_id: res.scenario_id,
          scenario_name: res.scenario_name || res.scenario_id,
        });
      });
    }
  });

  const filteredFindings = allFindings.filter((f) => {
    if (severityFilter !== 'ALL' && f.severity.toUpperCase() !== severityFilter) {
      return false;
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchRule = f.rule_name.toLowerCase().includes(q) || f.rule_id.toLowerCase().includes(q);
      const matchScenario = f.scenario_id.toLowerCase().includes(q) || f.scenario_name.toLowerCase().includes(q);
      const matchMessage = f.message.toLowerCase().includes(q);

      return matchRule || matchScenario || matchMessage;
    }

    return true;
  });

  const severityCounts = allFindings.reduce(
    (acc, f) => {
      const sev = f.severity.toUpperCase();
      acc[sev] = (acc[sev] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  const formatTimestamp = (isoString?: string) => {
    if (!isoString) return '';
    try {
      const d = new Date(isoString);
      return d.toLocaleTimeString(undefined, {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    } catch {
      return isoString;
    }
  };

  return (
    <div className="space-y-4">
      {/* Findings Summary & Filters */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-surface p-3.5 rounded-xl border border-surface-border">
        {/* Severity filter buttons */}
        <div className="flex items-center gap-1.5 overflow-x-auto text-xs">
          <Button
            size="sm"
            variant={severityFilter === 'ALL' ? 'secondary' : 'ghost'}
            onClick={() => setSeverityFilter('ALL')}
            className="text-xs h-7 px-2.5"
          >
            All Findings ({allFindings.length})
          </Button>
          {(severityCounts['CRITICAL'] || 0) > 0 && (
            <Button
              size="sm"
              variant={severityFilter === 'CRITICAL' ? 'secondary' : 'ghost'}
              onClick={() => setSeverityFilter('CRITICAL')}
              className="text-xs h-7 px-2.5 text-rose-400"
            >
              Critical ({severityCounts['CRITICAL'] || 0})
            </Button>
          )}
          {(severityCounts['HIGH'] || 0) > 0 && (
            <Button
              size="sm"
              variant={severityFilter === 'HIGH' ? 'secondary' : 'ghost'}
              onClick={() => setSeverityFilter('HIGH')}
              className="text-xs h-7 px-2.5 text-amber-400"
            >
              High ({severityCounts['HIGH'] || 0})
            </Button>
          )}
          {(severityCounts['MEDIUM'] || 0) > 0 && (
            <Button
              size="sm"
              variant={severityFilter === 'MEDIUM' ? 'secondary' : 'ghost'}
              onClick={() => setSeverityFilter('MEDIUM')}
              className="text-xs h-7 px-2.5 text-yellow-400"
            >
              Medium ({severityCounts['MEDIUM'] || 0})
            </Button>
          )}
          {(severityCounts['LOW'] || 0) > 0 && (
            <Button
              size="sm"
              variant={severityFilter === 'LOW' ? 'secondary' : 'ghost'}
              onClick={() => setSeverityFilter('LOW')}
              className="text-xs h-7 px-2.5 text-blue-400"
            >
              Low ({severityCounts['LOW'] || 0})
            </Button>
          )}
        </div>

        {/* Search */}
        <div className="relative w-full sm:w-64">
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search rule, scenario, message..."
            className="pl-8 text-xs h-8"
            aria-label="Search findings"
          />
        </div>
      </div>

      {/* Findings Listing */}
      {filteredFindings.length === 0 ? (
        <EmptyState
          icon={allFindings.length === 0 ? <ShieldCheck className="w-6 h-6 text-emerald-400" /> : <ShieldAlert className="w-6 h-6 text-amber-400" />}
          title={allFindings.length === 0 ? 'No Security Findings' : 'No Matching Findings'}
          description={
            allFindings.length === 0
              ? 'All evaluated security assertions passed without triggering any rule violations or findings.'
              : 'No findings match the selected severity filter or search terms.'
          }
        />
      ) : (
        <div className="space-y-3">
          {filteredFindings.map((finding) => (
            <div
              key={finding.finding_id}
              className="bg-surface rounded-xl border border-surface-border p-4.5 space-y-2.5 hover:border-slate-700 transition-colors"
            >
              {/* Finding Header */}
              <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-surface-border/50">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="font-semibold text-sm text-slate-100">
                    {finding.rule_name || finding.rule_id}
                  </span>
                  <span className="font-mono text-xs text-slate-400 bg-surface-elevated px-2 py-0.5 rounded border border-surface-border">
                    {finding.rule_id}
                  </span>
                  <SeverityBadge severity={finding.severity} size="sm" />
                  <OutcomeBadge outcome={finding.outcome} size="sm" />
                </div>

                <div className="flex items-center gap-2 text-[11px] text-slate-500 font-mono">
                  {finding.timestamp && (
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {formatTimestamp(finding.timestamp)}
                    </span>
                  )}
                </div>
              </div>

              {/* Finding Evidence / Message */}
              <div className="text-xs text-slate-300 leading-relaxed bg-surface-elevated/40 p-3 rounded-lg border border-surface-border">
                {finding.message}
              </div>

              {/* Associated Scenario */}
              <div className="flex items-center justify-between text-xs text-slate-400 pt-1">
                <div className="flex items-center gap-1.5">
                  <span className="text-slate-500 font-medium">Associated Scenario:</span>
                  <button
                    type="button"
                    onClick={() => onSelectScenario && onSelectScenario(finding.scenario_id)}
                    className="font-mono text-primary hover:text-primary-hover hover:underline focus:outline-none"
                  >
                    {finding.scenario_id} ({finding.scenario_name})
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
