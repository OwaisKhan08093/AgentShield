import React, { useState, useEffect, useCallback } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  RefreshCw,
  Download,
  Calendar,
  Layers,
  Terminal,
  ShieldAlert,
  FileCode,
  Copy,
  Check,
  AlertTriangle,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { OutcomeBadge } from '@/components/ui/StatusBadge';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorAlert } from '@/components/ui/ErrorAlert';
import { EmptyState } from '@/components/ui/EmptyState';
import { RunMetricsOverview } from '@/components/runs/RunMetricsOverview';
import { ScenarioResultsTable } from '@/components/runs/ScenarioResultsTable';
import { TraceInspector } from '@/components/runs/TraceInspector';
import { FindingsList } from '@/components/runs/FindingsList';
import { apiClient, ApiClientError } from '@/api/client';
import type {
  EvaluationRunRecord,
  ScenarioResultResponse,
  TraceEvent,
} from '@/api/types';

type ActiveTab = 'results' | 'trace' | 'findings' | 'raw';

export const RunDetail: React.FC = () => {
  const { runId } = useParams<{ runId: string }>();
  const navigate = useNavigate();

  const [activeTab, setActiveTab] = useState<ActiveTab>('results');
  const [selectedScenarioForTrace, setSelectedScenarioForTrace] = useState<string | undefined>(undefined);

  // Data states
  const [run, setRun] = useState<EvaluationRunRecord | null>(null);
  const [results, setResults] = useState<ScenarioResultResponse[]>([]);
  const [traceEvents, setTraceEvents] = useState<TraceEvent[]>([]);
  const [rawReport, setRawReport] = useState<Record<string, unknown> | null>(null);

  // Loading & error states
  const [isLoading, setIsLoading] = useState(true);
  const [isTraceLoading, setIsTraceLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isNotFound, setIsNotFound] = useState(false);
  const [copiedReport, setCopiedReport] = useState(false);

  // Fetch Run and Results
  const fetchRunData = useCallback(async (id: string) => {
    setIsLoading(true);
    setError(null);
    setIsNotFound(false);
    // Clear old data immediately to prevent stale views during navigation
    setRun(null);
    setResults([]);
    setTraceEvents([]);
    setRawReport(null);

    try {
      const [runRecord, runResults] = await Promise.all([
        apiClient.getRun(id),
        apiClient.getRunResults(id),
      ]);
      setRun(runRecord);
      setResults(Array.isArray(runResults) ? runResults : []);
    } catch (err) {
      if (err instanceof ApiClientError && err.status === 404) {
        setIsNotFound(true);
      } else {
        setError(err instanceof Error ? err.message : 'Failed to load evaluation run details');
      }
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Fetch Trace Events (optionally filtered by scenario)
  const fetchTraceData = useCallback(async (id: string, scenarioId?: string) => {
    setIsTraceLoading(true);
    try {
      const events = await apiClient.getRunTrace(id, scenarioId);
      setTraceEvents(Array.isArray(events) ? events : []);
    } catch {
      // Trace may be empty or not recorded; retain empty array
      setTraceEvents([]);
    } finally {
      setIsTraceLoading(false);
    }
  }, []);

  // Primary load effect
  useEffect(() => {
    if (!runId) return;
    fetchRunData(runId);
  }, [runId, fetchRunData]);

  // Load trace when user switches to Trace tab or changes selectedScenarioForTrace
  useEffect(() => {
    if (!runId || isNotFound || error) return;
    if (activeTab === 'trace' || activeTab === 'results') {
      fetchTraceData(runId, selectedScenarioForTrace);
    }
  }, [runId, activeTab, selectedScenarioForTrace, isNotFound, error, fetchTraceData]);

  const handleDownloadReport = async () => {
    if (!runId) return;
    try {
      const exportData = await apiClient.exportRunReport(runId);
      const jsonStr = JSON.stringify(exportData.report || exportData, null, 2);
      const blob = new Blob([jsonStr], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `agentshield-report-${runId}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err) {
      alert(`Failed to export report: ${err instanceof Error ? err.message : 'Unknown error'}`);
    }
  };

  const handleLoadRawReport = async () => {
    if (!runId || rawReport) return;
    try {
      const exportData = await apiClient.exportRunReport(runId);
      setRawReport((exportData.report as Record<string, unknown>) || exportData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to retrieve raw report');
    }
  };

  const handleTabChange = (tab: ActiveTab) => {
    setActiveTab(tab);
    if (tab === 'raw' && !rawReport) {
      handleLoadRawReport();
    }
  };

  const handleSelectScenarioForTrace = (scenarioId: string) => {
    setSelectedScenarioForTrace(scenarioId);
    setActiveTab('trace');
  };

  const copyRawReport = () => {
    if (!rawReport) return;
    navigator.clipboard.writeText(JSON.stringify(rawReport, null, 2));
    setCopiedReport(true);
    setTimeout(() => setCopiedReport(false), 2000);
  };

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
        second: '2-digit',
      });
    } catch {
      return isoString;
    }
  };

  if (isNotFound) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-2">
          <Link to="/runs">
            <Button variant="ghost" size="sm" leftIcon={<ArrowLeft className="w-4 h-4" />}>
              Back to Runs
            </Button>
          </Link>
        </div>
        <EmptyState
          icon={<AlertTriangle className="w-6 h-6 text-amber-400" />}
          title={`Evaluation Run Not Found`}
          description={`The evaluation run "${runId}" does not exist in SQLite database or has been deleted.`}
          action={
            <Button variant="secondary" onClick={() => navigate('/runs')}>
              View All Runs
            </Button>
          }
        />
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-2">
          <Link to="/runs">
            <Button variant="ghost" size="sm" leftIcon={<ArrowLeft className="w-4 h-4" />}>
              Back to Runs
            </Button>
          </Link>
        </div>
        <div className="py-20 flex justify-center">
          <LoadingSpinner message={`Loading evaluation run ${runId}...`} />
        </div>
      </div>
    );
  }

  if (error || !run) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-2">
          <Link to="/runs">
            <Button variant="ghost" size="sm" leftIcon={<ArrowLeft className="w-4 h-4" />}>
              Back to Runs
            </Button>
          </Link>
        </div>
        <ErrorAlert
          message={error || 'Failed to load evaluation run'}
          onRetry={() => runId && fetchRunData(runId)}
        />
      </div>
    );
  }

  // Count total findings across scenarios
  const totalFindingsCount = results.reduce(
    (acc, res) => acc + (res.finding_count || (res.findings ? res.findings.length : 0)),
    0
  );

  return (
    <div className="space-y-6">
      {/* Back link & actions */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <Link to="/runs">
            <Button
              variant="ghost"
              size="sm"
              leftIcon={<ArrowLeft className="w-4 h-4" />}
              aria-label="Back to run history"
            >
              Runs
            </Button>
          </Link>
          <span className="text-slate-600">/</span>
          <span className="font-mono text-xs text-slate-400 font-semibold truncate max-w-xs sm:max-w-md">
            {run.run_id}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => fetchRunData(run.run_id)}
            leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
            aria-label="Refresh run details"
          >
            Refresh
          </Button>

          <Button
            variant="secondary"
            size="sm"
            onClick={handleDownloadReport}
            leftIcon={<Download className="w-3.5 h-3.5" />}
            aria-label="Download JSON Report"
          >
            Export JSON Report
          </Button>
        </div>
      </div>

      {/* Run Header Banner */}
      <div className="bg-surface rounded-xl border border-surface-border p-5 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-surface-border/50">
          <div className="space-y-1">
            <div className="flex flex-wrap items-center gap-2.5">
              <h1 className="text-xl font-bold font-mono text-slate-100">
                {run.run_id}
              </h1>
              <OutcomeBadge outcome={run.overall_outcome} size="md" />
              <Badge variant="outline" size="sm">
                Status: {run.status}
              </Badge>
            </div>
            <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 pt-1">
              <span className="flex items-center gap-1.5">
                <Calendar className="w-3.5 h-3.5 text-slate-500" />
                Started: {formatDate(run.started_at || run.created_at)}
              </span>
              {run.completed_at && (
                <>
                  <span className="text-slate-600">•</span>
                  <span>Completed: {formatDate(run.completed_at)}</span>
                </>
              )}
              <span className="text-slate-600">•</span>
              <span>Suite v{run.suite_version}</span>
              <span className="text-slate-600">•</span>
              <span>Evaluator v{run.evaluator_version}</span>
            </div>
          </div>
        </div>

        {/* Metrics Overview Strip */}
        <RunMetricsOverview run={run} />
      </div>

      {/* Tabs Navigation */}
      <div className="border-b border-surface-border flex items-center gap-2 text-xs font-medium">
        <button
          type="button"
          onClick={() => handleTabChange('results')}
          className={`pb-3 px-3.5 border-b-2 flex items-center gap-2 transition-colors focus:outline-none ${
            activeTab === 'results'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
          aria-selected={activeTab === 'results'}
          role="tab"
        >
          <Layers className="w-4 h-4" />
          <span>Scenario Results ({results.length})</span>
        </button>

        <button
          type="button"
          onClick={() => handleTabChange('trace')}
          className={`pb-3 px-3.5 border-b-2 flex items-center gap-2 transition-colors focus:outline-none ${
            activeTab === 'trace'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
          aria-selected={activeTab === 'trace'}
          role="tab"
        >
          <Terminal className="w-4 h-4" />
          <span>Execution Trace</span>
          {traceEvents.length > 0 && (
            <span className="text-[10px] bg-surface-elevated px-1.5 py-0.5 rounded text-slate-400">
              {traceEvents.length}
            </span>
          )}
        </button>

        <button
          type="button"
          onClick={() => handleTabChange('findings')}
          className={`pb-3 px-3.5 border-b-2 flex items-center gap-2 transition-colors focus:outline-none ${
            activeTab === 'findings'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
          aria-selected={activeTab === 'findings'}
          role="tab"
        >
          <ShieldAlert className="w-4 h-4" />
          <span>Security Findings</span>
          {totalFindingsCount > 0 && (
            <span className="text-[10px] bg-rose-500/20 text-rose-400 px-1.5 py-0.5 rounded font-semibold">
              {totalFindingsCount}
            </span>
          )}
        </button>

        <button
          type="button"
          onClick={() => handleTabChange('raw')}
          className={`pb-3 px-3.5 border-b-2 flex items-center gap-2 transition-colors focus:outline-none ${
            activeTab === 'raw'
              ? 'border-primary text-primary font-semibold'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
          aria-selected={activeTab === 'raw'}
          role="tab"
        >
          <FileCode className="w-4 h-4" />
          <span>Report JSON</span>
        </button>
      </div>

      {/* Tab Contents */}
      <div>
        {activeTab === 'results' && (
          <ScenarioResultsTable
            results={results}
            onSelectScenarioForTrace={handleSelectScenarioForTrace}
          />
        )}

        {activeTab === 'trace' && (
          <div>
            {isTraceLoading ? (
              <div className="py-12 flex justify-center">
                <LoadingSpinner message="Loading chronological execution trace..." />
              </div>
            ) : (
              <TraceInspector
                events={traceEvents}
                scenarioResults={results}
                selectedScenarioId={selectedScenarioForTrace}
                onScenarioChange={(id) => setSelectedScenarioForTrace(id)}
              />
            )}
          </div>
        )}

        {activeTab === 'findings' && (
          <FindingsList
            results={results}
            onSelectScenario={(id) => {
              setSelectedScenarioForTrace(id);
              setActiveTab('results');
            }}
          />
        )}

        {activeTab === 'raw' && (
          <div className="bg-surface rounded-xl border border-surface-border p-4 space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-surface-border/50">
              <span className="text-xs font-semibold text-slate-300">
                Evaluation Report Export Schema (GET /api/v1/runs/{run.run_id}/report.json)
              </span>
              <Button
                variant="ghost"
                size="sm"
                className="h-7 px-2.5 text-xs text-slate-300 hover:text-white gap-1.5"
                onClick={copyRawReport}
                disabled={!rawReport}
              >
                {copiedReport ? (
                  <>
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                    <span className="text-emerald-400">Copied</span>
                  </>
                ) : (
                  <>
                    <Copy className="w-3.5 h-3.5" />
                    <span>Copy JSON</span>
                  </>
                )}
              </Button>
            </div>

            {rawReport ? (
              <pre className="p-4 rounded-lg bg-surface-elevated/70 border border-surface-border text-xs font-mono text-slate-300 overflow-x-auto max-h-[600px] leading-relaxed select-text">
                {JSON.stringify(rawReport, null, 2)}
              </pre>
            ) : (
              <div className="py-8 flex justify-center">
                <LoadingSpinner message="Fetching raw report JSON..." />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
