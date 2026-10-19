import React, { useState } from 'react';
import {
  ChevronDown,
  ChevronRight,
  ShieldAlert,
  Info,
  Search,
} from 'lucide-react';
import {
  OutcomeBadge,
  SeverityBadge,
  CategoryBadge,
  ExecutionStatusBadge,
} from '@/components/ui/StatusBadge';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import type { ScenarioResultResponse } from '@/api/types';

interface ScenarioResultsTableProps {
  results: ScenarioResultResponse[];
  onSelectScenarioForTrace?: (scenarioId: string) => void;
}

export const ScenarioResultsTable: React.FC<ScenarioResultsTableProps> = ({
  results,
  onSelectScenarioForTrace,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [outcomeFilter, setOutcomeFilter] = useState<string>('ALL');
  const [expandedRows, setExpandedRows] = useState<Record<string, boolean>>({});

  const toggleRow = (scenarioId: string) => {
    setExpandedRows((prev) => ({
      ...prev,
      [scenarioId]: !prev[scenarioId],
    }));
  };

  const filteredResults = results.filter((res) => {
    const matchesSearch =
      res.scenario_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      res.scenario_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      res.explanation.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesOutcome =
      outcomeFilter === 'ALL' || res.outcome.toUpperCase() === outcomeFilter;

    return matchesSearch && matchesOutcome;
  });

  const outcomeCounts = results.reduce(
    (acc, item) => {
      acc[item.outcome] = (acc[item.outcome] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  return (
    <div className="space-y-3">
      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Filter scenario ID, name, or explanation..."
            className="pl-9 text-xs"
            aria-label="Search scenarios"
          />
        </div>

        {/* Outcome Filter Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0 text-xs">
          <Button
            size="sm"
            variant={outcomeFilter === 'ALL' ? 'secondary' : 'ghost'}
            onClick={() => setOutcomeFilter('ALL')}
            className="text-xs h-8 px-2.5"
          >
            All ({results.length})
          </Button>
          <Button
            size="sm"
            variant={outcomeFilter === 'PASS' ? 'secondary' : 'ghost'}
            onClick={() => setOutcomeFilter('PASS')}
            className="text-xs h-8 px-2.5 text-emerald-400 hover:text-emerald-300"
          >
            Pass ({outcomeCounts['PASS'] || 0})
          </Button>
          <Button
            size="sm"
            variant={outcomeFilter === 'FAIL' ? 'secondary' : 'ghost'}
            onClick={() => setOutcomeFilter('FAIL')}
            className="text-xs h-8 px-2.5 text-rose-400 hover:text-rose-300"
          >
            Fail ({outcomeCounts['FAIL'] || 0})
          </Button>
          {(outcomeCounts['ERROR'] || 0) > 0 && (
            <Button
              size="sm"
              variant={outcomeFilter === 'ERROR' ? 'secondary' : 'ghost'}
              onClick={() => setOutcomeFilter('ERROR')}
              className="text-xs h-8 px-2.5 text-amber-400 hover:text-amber-300"
            >
              Error ({outcomeCounts['ERROR'] || 0})
            </Button>
          )}
          {(outcomeCounts['NOT_RUN'] || 0) > 0 && (
            <Button
              size="sm"
              variant={outcomeFilter === 'NOT_RUN' ? 'secondary' : 'ghost'}
              onClick={() => setOutcomeFilter('NOT_RUN')}
              className="text-xs h-8 px-2.5 text-slate-400 hover:text-slate-300"
            >
              Not Run ({outcomeCounts['NOT_RUN'] || 0})
            </Button>
          )}
        </div>
      </div>

      {/* Results Table */}
      <div className="overflow-hidden rounded-xl border border-surface-border bg-surface">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm" role="table" aria-label="Scenario evaluation results table">
            <thead className="bg-surface-elevated/80 border-b border-surface-border text-xs uppercase tracking-wider text-slate-400 select-none">
              <tr>
                <th scope="col" className="w-8 py-3.5 pl-4 pr-1"></th>
                <th scope="col" className="py-3.5 px-4 font-semibold">Scenario</th>
                <th scope="col" className="py-3.5 px-4 font-semibold">Security Verdict</th>
                <th scope="col" className="py-3.5 px-4 font-semibold">Execution Status</th>
                <th scope="col" className="py-3.5 px-4 font-semibold">Security Assertions</th>
                <th scope="col" className="py-3.5 px-4 font-semibold text-center">Findings</th>
                <th scope="col" className="py-3.5 pr-4 text-right">Trace</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-surface-border/50 text-slate-300">
              {filteredResults.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-slate-400 text-xs">
                    No scenarios match the current filters.
                  </td>
                </tr>
              ) : (
                filteredResults.map((res) => {
                  const isExpanded = !!expandedRows[res.scenario_id];
                  return (
                    <React.Fragment key={res.scenario_id}>
                      <tr
                        className={`hover:bg-surface-elevated/40 transition-colors cursor-pointer select-none ${
                          isExpanded ? 'bg-surface-elevated/30' : ''
                        }`}
                        onClick={() => toggleRow(res.scenario_id)}
                      >
                        {/* Expand toggle */}
                        <td className="py-3.5 pl-4 pr-1 text-slate-500">
                          {isExpanded ? (
                            <ChevronDown className="w-4 h-4 text-slate-300" />
                          ) : (
                            <ChevronRight className="w-4 h-4 text-slate-500" />
                          )}
                        </td>

                        {/* Scenario ID & Name */}
                        <td className="py-3.5 px-4">
                          <div className="font-medium text-slate-100 flex items-center gap-2">
                            <span>{res.scenario_name || res.scenario_id}</span>
                          </div>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="font-mono text-[11px] text-slate-400">
                              {res.scenario_id}
                            </span>
                            <CategoryBadge category={res.category} size="sm" />
                            <SeverityBadge severity={res.risk_level} size="sm" />
                          </div>
                        </td>

                        {/* Security Verdict */}
                        <td className="py-3.5 px-4">
                          <OutcomeBadge outcome={res.outcome} size="sm" />
                        </td>

                        {/* Execution Status: actual vs expected */}
                        <td className="py-3.5 px-4 text-xs font-mono">
                          <div className="flex items-center gap-1.5">
                            <span className="text-slate-400">actual:</span>
                            <ExecutionStatusBadge status={res.actual_status} size="sm" />
                          </div>
                          <div className="flex items-center gap-1.5 mt-0.5 text-slate-500">
                            <span>expected:</span>
                            <span>{res.expected_status}</span>
                          </div>
                        </td>

                        {/* Security Assertions Indicators */}
                        <td className="py-3.5 px-4 text-xs">
                          <div className="flex flex-wrap gap-1.5">
                            {res.attempt_detected && (
                              <Badge variant="warning" size="sm" title="Attack attempt was detected">
                                Attempt Detected
                              </Badge>
                            )}
                            {res.violation_prevented ? (
                              <Badge variant="pass" size="sm" title="Policy violation successfully prevented">
                                Violation Prevented
                              </Badge>
                            ) : (
                              <Badge variant="fail" size="sm" title="Violation was NOT prevented">
                                Violation Unprevented
                              </Badge>
                            )}
                            {res.data_exposed ? (
                              <Badge variant="fail" size="sm" title="Sensitive data was exposed">
                                Data Exposed
                              </Badge>
                            ) : (
                              <Badge variant="outline" size="sm" title="No sensitive data leaked">
                                Data Protected
                              </Badge>
                            )}
                          </div>
                        </td>

                        {/* Findings Count */}
                        <td className="py-3.5 px-4 text-center">
                          {res.finding_count > 0 ? (
                            <Badge variant="fail" size="sm" className="font-semibold">
                              {res.finding_count} {res.finding_count === 1 ? 'finding' : 'findings'}
                            </Badge>
                          ) : (
                            <span className="text-xs text-slate-500">0</span>
                          )}
                        </td>

                        {/* Actions */}
                        <td className="py-3.5 pr-4 text-right">
                          {onSelectScenarioForTrace && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-xs h-7 px-2 text-slate-300 hover:text-white"
                              onClick={(e) => {
                                e.stopPropagation();
                                onSelectScenarioForTrace(res.scenario_id);
                              }}
                              title="Filter execution trace to this scenario"
                            >
                              Trace
                            </Button>
                          )}
                        </td>
                      </tr>

                      {/* Expandable Explanation & Findings Detail */}
                      {isExpanded && (
                        <tr className="bg-surface-elevated/20">
                          <td colSpan={7} className="p-4 pl-12 pr-6 border-t border-surface-border/40">
                            <div className="space-y-3">
                              {/* Evaluator Explanation */}
                              <div>
                                <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1 flex items-center gap-1.5">
                                  <Info className="w-3.5 h-3.5 text-primary" />
                                  Evaluator Explanation
                                </h4>
                                <div className="text-xs text-slate-300 bg-surface-elevated/50 p-3 rounded-lg border border-surface-border font-mono leading-relaxed whitespace-pre-wrap">
                                  {res.explanation || 'No detailed explanation provided.'}
                                </div>
                              </div>

                              {/* Findings in this scenario */}
                              {res.findings && res.findings.length > 0 && (
                                <div>
                                  <h4 className="text-xs font-semibold text-rose-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                                    <ShieldAlert className="w-3.5 h-3.5" />
                                    Security Findings ({res.findings.length})
                                  </h4>
                                  <div className="space-y-2">
                                    {res.findings.map((f) => (
                                      <div
                                        key={f.finding_id}
                                        className="p-3 rounded-lg border border-rose-500/20 bg-rose-950/10 text-xs flex flex-col gap-1.5"
                                      >
                                        <div className="flex items-center justify-between gap-2">
                                          <div className="flex items-center gap-2">
                                            <span className="font-semibold text-slate-200">
                                              {f.rule_name || f.rule_id}
                                            </span>
                                            <span className="font-mono text-[10px] text-slate-400">
                                              [{f.rule_id}]
                                            </span>
                                          </div>
                                          <div className="flex items-center gap-1.5">
                                            <SeverityBadge severity={f.severity} size="sm" />
                                            <OutcomeBadge outcome={f.outcome} size="sm" />
                                          </div>
                                        </div>
                                        <p className="text-slate-300 text-xs">
                                          {f.message}
                                        </p>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
