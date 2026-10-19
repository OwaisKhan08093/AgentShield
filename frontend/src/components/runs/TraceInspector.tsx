import React, { useState } from 'react';
import {
  Clock,
  Terminal,
  ShieldAlert,
  Copy,
  Check,
  ChevronDown,
  ChevronRight,
  Search,
} from 'lucide-react';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { EmptyState } from '@/components/ui/EmptyState';
import type { TraceEvent, ScenarioResultResponse } from '@/api/types';

interface TraceInspectorProps {
  events: TraceEvent[];
  scenarioResults?: ScenarioResultResponse[];
  selectedScenarioId?: string;
  onScenarioChange?: (scenarioId: string | undefined) => void;
  isLoading?: boolean;
}

export const TraceInspector: React.FC<TraceInspectorProps> = ({
  events,
  scenarioResults = [],
  selectedScenarioId,
  onScenarioChange,
}) => {
  const [copiedEventId, setCopiedEventId] = useState<string | null>(null);
  const [filterType, setFilterType] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [expandedPayloads, setExpandedPayloads] = useState<Record<string, boolean>>({});

  const togglePayload = (eventId: string) => {
    setExpandedPayloads((prev) => ({
      ...prev,
      [eventId]: !prev[eventId],
    }));
  };

  const copyPayload = (eventId: string, payload: unknown) => {
    try {
      navigator.clipboard.writeText(JSON.stringify(payload, null, 2));
      setCopiedEventId(eventId);
      setTimeout(() => setCopiedEventId(null), 2000);
    } catch {
      // ignore clipboard error
    }
  };

  const filteredEvents = events.filter((ev) => {
    // Type filter
    if (filterType === 'DENIED' && !ev.is_denied) return false;
    if (filterType !== 'ALL' && filterType !== 'DENIED' && ev.event_type !== filterType) {
      return false;
    }

    // Search query
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchTool = ev.tool_name?.toLowerCase().includes(q);
      const matchType = ev.event_type.toLowerCase().includes(q);
      const matchDecision = ev.decision?.toLowerCase().includes(q);
      const matchPayload = ev.sanitized_payload
        ? JSON.stringify(ev.sanitized_payload).toLowerCase().includes(q)
        : false;

      if (!matchTool && !matchType && !matchDecision && !matchPayload) {
        return false;
      }
    }

    return true;
  });

  const getEventTypeVariant = (type: string) => {
    switch (type.toLowerCase()) {
      case 'tool_call':
        return 'purple';
      case 'tool_result':
        return 'info';
      case 'response':
        return 'pass';
      case 'request':
        return 'default';
      case 'error':
        return 'fail';
      default:
        return 'default';
    }
  };

  const formatTimestamp = (isoString: string) => {
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
      {/* Filters Toolbar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-surface p-3.5 rounded-xl border border-surface-border">
        {/* Scenario Filter Dropdown if scenario results available */}
        <div className="flex flex-wrap items-center gap-2">
          {scenarioResults.length > 0 && onScenarioChange && (
            <div className="flex items-center gap-2">
              <label htmlFor="trace-scenario-select" className="text-xs text-slate-400 font-medium whitespace-nowrap">
                Scenario:
              </label>
              <select
                id="trace-scenario-select"
                value={selectedScenarioId || ''}
                onChange={(e) => onScenarioChange(e.target.value || undefined)}
                className="bg-surface-elevated border border-surface-border rounded-lg text-xs text-slate-200 py-1.5 px-3 focus:outline-none focus:ring-1 focus:ring-primary max-w-xs truncate"
                aria-label="Filter trace events by scenario"
              >
                <option value="">All Scenarios ({scenarioResults.length})</option>
                {scenarioResults.map((s) => (
                  <option key={s.scenario_id} value={s.scenario_id}>
                    {s.scenario_id} — {s.scenario_name || s.scenario_id}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Type filters */}
          <div className="flex items-center gap-1 overflow-x-auto text-xs">
            <Button
              size="sm"
              variant={filterType === 'ALL' ? 'secondary' : 'ghost'}
              onClick={() => setFilterType('ALL')}
              className="text-xs h-7 px-2.5"
            >
              All ({events.length})
            </Button>
            <Button
              size="sm"
              variant={filterType === 'tool_call' ? 'secondary' : 'ghost'}
              onClick={() => setFilterType('tool_call')}
              className="text-xs h-7 px-2.5 text-purple-400"
            >
              Tool Calls
            </Button>
            <Button
              size="sm"
              variant={filterType === 'tool_result' ? 'secondary' : 'ghost'}
              onClick={() => setFilterType('tool_result')}
              className="text-xs h-7 px-2.5 text-blue-400"
            >
              Tool Results
            </Button>
            <Button
              size="sm"
              variant={filterType === 'DENIED' ? 'secondary' : 'ghost'}
              onClick={() => setFilterType('DENIED')}
              className="text-xs h-7 px-2.5 text-rose-400"
            >
              Denied Only
            </Button>
          </div>
        </div>

        {/* Text Search */}
        <div className="relative w-full sm:w-64">
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search payload or tool..."
            className="pl-8 text-xs h-8"
            aria-label="Search trace payloads"
          />
        </div>
      </div>

      {/* Events Timeline */}
      {filteredEvents.length === 0 ? (
        <EmptyState
          icon={<Terminal className="w-6 h-6 text-slate-400" />}
          title="No Trace Events Found"
          description={
            events.length === 0
              ? 'No execution trace events were recorded for this run. Make sure "record_trace" was enabled in execution options.'
              : 'No trace events matched the selected filter or search query.'
          }
        />
      ) : (
        <div className="relative border-l border-surface-border ml-3 sm:ml-5 space-y-3 pb-4">
          {filteredEvents.map((ev) => {
            const hasPayload =
              ev.sanitized_payload && Object.keys(ev.sanitized_payload).length > 0;
            const isPayloadExpanded = expandedPayloads[ev.event_id] !== false; // expanded by default

            return (
              <div key={ev.event_id} className="relative pl-6 sm:pl-8 group">
                {/* Timeline node */}
                <div
                  className={`absolute -left-2.5 top-3.5 w-5 h-5 rounded-full border-2 flex items-center justify-center text-[10px] font-bold ${
                    ev.is_denied
                      ? 'bg-rose-950 border-rose-500 text-rose-400'
                      : ev.event_type === 'tool_call'
                      ? 'bg-purple-950 border-purple-500 text-purple-400'
                      : 'bg-surface-elevated border-slate-600 text-slate-300'
                  }`}
                  aria-hidden="true"
                >
                  {ev.sequence}
                </div>

                {/* Event Card */}
                <div
                  className={`rounded-xl border transition-colors ${
                    ev.is_denied
                      ? 'border-rose-500/30 bg-rose-950/10'
                      : 'border-surface-border bg-surface'
                  } p-4`}
                >
                  {/* Event Header */}
                  <div className="flex flex-wrap items-center justify-between gap-2 pb-2 border-b border-surface-border/50">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-mono text-xs font-semibold text-slate-400">
                        #{ev.sequence}
                      </span>

                      <Badge variant={getEventTypeVariant(ev.event_type)} size="sm">
                        {ev.event_type}
                      </Badge>

                      {ev.tool_name && (
                        <div className="flex items-center gap-1 font-mono text-xs text-slate-200 bg-surface-elevated px-2 py-0.5 rounded border border-surface-border">
                          <Terminal className="w-3 h-3 text-primary" />
                          <span>{ev.tool_name}</span>
                        </div>
                      )}

                      {/* Decision & Denial status */}
                      {ev.decision && (
                        <span
                          className={`text-xs font-mono font-medium px-2 py-0.5 rounded ${
                            ev.is_denied
                              ? 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                              : ev.decision.toLowerCase() === 'allowed'
                              ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                              : 'bg-slate-700/50 text-slate-300'
                          }`}
                        >
                          decision: {ev.decision}
                        </span>
                      )}

                      {ev.is_denied && (
                        <Badge variant="fail" size="sm" className="font-bold">
                          <ShieldAlert className="w-3 h-3" />
                          AUTHORIZATION DENIED
                        </Badge>
                      )}
                    </div>

                    {/* Timestamp & copy */}
                    <div className="flex items-center gap-2 text-[11px] text-slate-500 font-mono">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3 text-slate-500" />
                        {formatTimestamp(ev.timestamp)}
                      </span>
                    </div>
                  </div>

                  {/* Sanitized Payload Display */}
                  {hasPayload ? (
                    <div className="mt-3">
                      <div className="flex items-center justify-between pb-1.5">
                        <button
                          type="button"
                          onClick={() => togglePayload(ev.event_id)}
                          className="flex items-center gap-1 text-[11px] font-semibold text-slate-400 hover:text-slate-200 select-none focus:outline-none"
                          aria-expanded={isPayloadExpanded}
                        >
                          {isPayloadExpanded ? (
                            <ChevronDown className="w-3.5 h-3.5" />
                          ) : (
                            <ChevronRight className="w-3.5 h-3.5" />
                          )}
                          <span>Sanitized Payload</span>
                        </button>

                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 px-2 text-[11px] text-slate-400 hover:text-white gap-1"
                          onClick={() => copyPayload(ev.event_id, ev.sanitized_payload)}
                          title="Copy sanitized JSON payload"
                        >
                          {copiedEventId === ev.event_id ? (
                            <>
                              <Check className="w-3 h-3 text-emerald-400" />
                              <span className="text-emerald-400">Copied</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-3 h-3" />
                              <span>Copy JSON</span>
                            </>
                          )}
                        </Button>
                      </div>

                      {isPayloadExpanded && (
                        <pre className="p-3 rounded-lg bg-surface-elevated/70 border border-surface-border text-xs font-mono text-slate-300 overflow-x-auto leading-relaxed max-h-80 select-text">
                          {JSON.stringify(ev.sanitized_payload, null, 2)}
                        </pre>
                      )}
                    </div>
                  ) : (
                    <div className="mt-2 text-xs text-slate-500 italic">
                      No payload data associated with this event.
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
