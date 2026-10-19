import React, { useState, useMemo } from 'react';
import {
  ChevronRight,
  ChevronDown,
  Copy,
  Check,
  Download,
  Search,
  Maximize2,
  Minimize2,
  FileCode,
  Layers,
  Calendar,
  AlertCircle,
  FileCheck,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { downloadBlob } from '@/utils/csvExport';
import type { EvaluationReportExportResponse, EvaluationReport } from '@/api/types';

interface JsonReportVisualizerProps {
  runId: string;
  exportResponse?: EvaluationReportExportResponse | null;
  report?: EvaluationReport | null;
  rawJson?: Record<string, unknown> | null;
  isLoading?: boolean;
  error?: string | null;
  className?: string;
}

type ViewMode = 'tree' | 'raw';

interface JsonTreeNodeProps {
  keyName?: string;
  value: unknown;
  depth?: number;
  expandedKeys: Set<string>;
  toggleKey: (path: string) => void;
  path: string;
  searchFilter: string;
}

const JsonTreeNode: React.FC<JsonTreeNodeProps> = ({
  keyName,
  value,
  depth = 0,
  expandedKeys,
  toggleKey,
  path,
  searchFilter,
}) => {
  const isObject = value !== null && typeof value === 'object';
  const isArray = Array.isArray(value);
  const isExpanded = expandedKeys.has(path);

  // Search match check
  const matchesSearch = useMemo(() => {
    if (!searchFilter) return true;
    const filter = searchFilter.toLowerCase();
    if (keyName && keyName.toLowerCase().includes(filter)) return true;
    if (!isObject && value !== undefined && value !== null) {
      return String(value).toLowerCase().includes(filter);
    }
    return false;
  }, [keyName, value, isObject, searchFilter]);

  if (isObject) {
    const entries = isArray
      ? (value as unknown[]).map((v, i) => [`[${i}]`, v] as [string, unknown])
      : Object.entries(value as Record<string, unknown>);

    const childCount = entries.length;

    return (
      <div className="text-xs font-mono select-text" style={{ paddingLeft: depth > 0 ? '1rem' : 0 }}>
        <div
          onClick={() => toggleKey(path)}
          className={`flex items-center gap-1.5 py-0.5 px-1 rounded cursor-pointer hover:bg-surface-elevated/70 transition-colors group ${
            matchesSearch && searchFilter ? 'bg-primary/20 ring-1 ring-primary/40' : ''
          }`}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              toggleKey(path);
            }
          }}
          aria-expanded={isExpanded}
          aria-label={`Toggle ${keyName || (isArray ? 'array' : 'object')}`}
        >
          {childCount > 0 ? (
            isExpanded ? (
              <ChevronDown className="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-200" />
            ) : (
              <ChevronRight className="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-200" />
            )
          ) : (
            <span className="w-3.5 h-3.5 inline-block" />
          )}

          {keyName && (
            <span className="text-cyan-400 font-semibold group-hover:text-cyan-300">
              "{keyName}":
            </span>
          )}

          <span className="text-slate-400">
            {isArray ? '[' : '{'}
            {!isExpanded && (
              <span className="text-slate-500 italic ml-1">
                ... {childCount} {isArray ? 'items' : 'keys'} {isArray ? ']' : '}'}
              </span>
            )}
          </span>
        </div>

        {isExpanded && (
          <div className="border-l border-surface-border/40 ml-2 pl-1 space-y-0.5">
            {entries.map(([childKey, childValue]) => (
              <JsonTreeNode
                key={childKey}
                keyName={childKey}
                value={childValue}
                depth={depth + 1}
                expandedKeys={expandedKeys}
                toggleKey={toggleKey}
                path={`${path}.${childKey}`}
                searchFilter={searchFilter}
              />
            ))}
            <div className="text-slate-400 py-0.5 pl-3">
              {isArray ? ']' : '}'}
            </div>
          </div>
        )}
      </div>
    );
  }

  // Primitive Values
  const renderPrimitiveValue = () => {
    if (value === null) {
      return <span className="text-rose-400 font-semibold">null</span>;
    }
    if (value === undefined) {
      return <span className="text-slate-500">undefined</span>;
    }
    if (typeof value === 'boolean') {
      return <span className="text-amber-400 font-semibold">{value ? 'true' : 'false'}</span>;
    }
    if (typeof value === 'number') {
      return <span className="text-purple-400 font-semibold">{value}</span>;
    }
    // String value - ensure safe text rendering without innerHTML
    return (
      <span className="text-emerald-400 break-all">
        "{String(value)}"
      </span>
    );
  };

  return (
    <div
      className={`flex items-baseline gap-1.5 py-0.5 px-1 rounded hover:bg-surface-elevated/40 text-xs font-mono select-text ${
        matchesSearch && searchFilter ? 'bg-primary/20 ring-1 ring-primary/40' : ''
      }`}
      style={{ paddingLeft: depth > 0 ? '1rem' : 0 }}
    >
      <span className="w-3.5 h-3.5 inline-block shrink-0" />
      {keyName && (
        <span className="text-cyan-400 font-medium shrink-0">
          "{keyName}":
        </span>
      )}
      {renderPrimitiveValue()}
    </div>
  );
};

export const JsonReportVisualizer: React.FC<JsonReportVisualizerProps> = ({
  runId,
  exportResponse,
  report,
  rawJson,
  isLoading = false,
  error = null,
  className = '',
}) => {
  const [viewMode, setViewMode] = useState<ViewMode>('tree');
  const [searchFilter, setSearchFilter] = useState('');
  const [copyStatus, setCopyStatus] = useState<'idle' | 'copied' | 'error'>('idle');
  const [expandedKeys, setExpandedKeys] = useState<Set<string>>(() => {
    // Expand root level nodes by default
    return new Set(['root', 'root.report', 'root.metrics', 'root.summary_counts']);
  });

  // Consolidate full export data object
  const reportData = useMemo(() => {
    if (exportResponse) return exportResponse;
    if (rawJson) return rawJson;
    if (report) {
      return {
        schema_version: '1.0.0',
        exported_at: report.completed_at || new Date().toISOString(),
        report,
      };
    }
    return null;
  }, [exportResponse, report, rawJson]);

  const rawJsonString = useMemo(() => {
    if (!reportData) return '';
    return JSON.stringify(reportData, null, 2);
  }, [reportData]);

  // Recursively collect all object keys for Expand All
  const allPaths = useMemo(() => {
    const paths = new Set<string>();
    const collect = (obj: unknown, currentPath: string) => {
      if (obj !== null && typeof obj === 'object') {
        paths.add(currentPath);
        if (Array.isArray(obj)) {
          obj.forEach((v, i) => collect(v, `${currentPath}.[${i}]`));
        } else {
          Object.entries(obj as Record<string, unknown>).forEach(([k, v]) => {
            collect(v, `${currentPath}.${k}`);
          });
        }
      }
    };
    if (reportData) {
      collect(reportData, 'root');
    }
    return paths;
  }, [reportData]);

  const toggleKey = (path: string) => {
    setExpandedKeys((prev) => {
      const next = new Set(prev);
      if (next.has(path)) {
        next.delete(path);
      } else {
        next.add(path);
      }
      return next;
    });
  };

  const handleExpandAll = () => {
    setExpandedKeys(new Set(allPaths));
  };

  const handleCollapseAll = () => {
    setExpandedKeys(new Set(['root']));
  };

  const handleCopy = async () => {
    try {
      if (!rawJsonString) throw new Error('No JSON data available to copy');
      await navigator.clipboard.writeText(rawJsonString);
      setCopyStatus('copied');
      setTimeout(() => setCopyStatus('idle'), 2500);
    } catch {
      setCopyStatus('error');
      setTimeout(() => setCopyStatus('idle'), 3000);
    }
  };

  const handleDownload = () => {
    if (!rawJsonString) return;
    downloadBlob(
      `agentshield-report-${runId}.json`,
      rawJsonString,
      'application/json;charset=utf-8;'
    );
  };

  // Format dates safely
  const formatIso = (iso?: string) => {
    if (!iso) return '—';
    try {
      return new Date(iso).toLocaleString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      });
    } catch {
      return iso;
    }
  };

  // Extract metadata fields
  const schemaVersion =
    (reportData as Record<string, unknown>)?.schema_version || '1.0.0';
  const exportedAt =
    (reportData as Record<string, unknown>)?.exported_at ||
    (reportData as Record<string, unknown>)?.completed_at;
  const reportObj = (reportData as Record<string, unknown>)?.report as
    | EvaluationReport
    | undefined;
  const reportId = reportObj?.report_id || (reportData as Record<string, unknown>)?.report_id;
  const evaluatorVersion = reportObj?.evaluator_version || '1.0.0';
  const suiteVersion = reportObj?.suite_version ?? 1;

  if (isLoading) {
    return (
      <div className={`p-8 rounded-xl bg-surface border border-surface-border flex flex-col items-center justify-center space-y-3 ${className}`}>
        <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        <span className="text-xs text-slate-400">Loading machine-readable evaluation report...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`p-5 rounded-xl bg-rose-950/20 border border-rose-500/30 text-rose-300 space-y-3 ${className}`}>
        <div className="flex items-center gap-2 font-medium text-sm">
          <AlertCircle className="w-4 h-4 text-rose-400" />
          <span>Evaluation Report Retrieval Error</span>
        </div>
        <p className="text-xs text-rose-300/80 leading-relaxed">{error}</p>
      </div>
    );
  }

  if (!reportData) {
    return (
      <div className={`p-8 rounded-xl bg-surface border border-surface-border text-center space-y-2 ${className}`}>
        <FileCode className="w-8 h-8 text-slate-500 mx-auto" />
        <h4 className="text-sm font-medium text-slate-300">No Report Data Available</h4>
        <p className="text-xs text-slate-500 max-w-md mx-auto">
          The evaluation report for run <span className="font-mono text-slate-400">{runId}</span> is not available or has not been generated yet.
        </p>
      </div>
    );
  }

  return (
    <div className={`bg-surface rounded-xl border border-surface-border overflow-hidden space-y-0 ${className}`}>
      {/* 1. Report Metadata Header Bar */}
      <div className="p-4 bg-surface-elevated/40 border-b border-surface-border/60 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="space-y-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-semibold text-slate-200">
              Evaluation Report Object
            </span>
            <Badge variant="outline" size="sm">
              Schema v{String(schemaVersion)}
            </Badge>
            {Boolean(reportId) && (
              <Badge variant="default" size="sm" className="font-mono text-[10px]">
                Report ID: {String(reportId)}
              </Badge>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-2.5 text-xs text-slate-400">
            <span className="flex items-center gap-1">
              <Calendar className="w-3.5 h-3.5 text-slate-500" />
              Exported: {formatIso(String(exportedAt))}
            </span>
            <span className="text-slate-600">•</span>
            <span>Evaluator v{String(evaluatorVersion)}</span>
            <span className="text-slate-600">•</span>
            <span>Suite v{String(suiteVersion)}</span>
            <span className="text-slate-600">•</span>
            <span className="font-mono text-[11px] text-slate-500">
              {(new TextEncoder().encode(rawJsonString).length / 1024).toFixed(1)} KB
            </span>
          </div>
        </div>

        {/* View mode toggle & primary actions */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Tree / Raw Toggle */}
          <div className="p-0.5 rounded-lg bg-surface border border-surface-border flex items-center">
            <button
              type="button"
              onClick={() => setViewMode('tree')}
              className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                viewMode === 'tree'
                  ? 'bg-primary text-white font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              aria-label="Interactive Tree View"
            >
              <div className="flex items-center gap-1.5">
                <Layers className="w-3 h-3" />
                <span>Tree View</span>
              </div>
            </button>
            <button
              type="button"
              onClick={() => setViewMode('raw')}
              className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                viewMode === 'raw'
                  ? 'bg-primary text-white font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              aria-label="Raw Formatted JSON View"
            >
              <div className="flex items-center gap-1.5">
                <FileCode className="w-3 h-3" />
                <span>Raw JSON</span>
              </div>
            </button>
          </div>

          {/* Copy Button */}
          <Button
            variant="ghost"
            size="sm"
            onClick={handleCopy}
            leftIcon={
              copyStatus === 'copied' ? (
                <Check className="w-3.5 h-3.5 text-emerald-400" />
              ) : (
                <Copy className="w-3.5 h-3.5" />
              )
            }
            className={`h-8 px-2 text-xs ${
              copyStatus === 'copied' ? 'text-emerald-400' : 'text-slate-300'
            }`}
            aria-label="Copy report JSON"
          >
            {copyStatus === 'copied' ? 'Copied' : 'Copy'}
          </Button>

          {/* Download Button */}
          <Button
            variant="secondary"
            size="sm"
            onClick={handleDownload}
            leftIcon={<Download className="w-3.5 h-3.5 text-primary" />}
            className="h-8 px-2.5 text-xs text-slate-200"
            aria-label="Download JSON file"
          >
            Download JSON
          </Button>
        </div>
      </div>

      {/* 2. Visualizer Toolbar (Tree view only) */}
      {viewMode === 'tree' && (
        <div className="p-2.5 bg-surface-elevated/20 border-b border-surface-border/50 flex flex-wrap items-center justify-between gap-2 text-xs">
          {/* Search/Filter Bar */}
          <div className="relative min-w-[200px] max-w-xs flex-1">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchFilter}
              onChange={(e) => setSearchFilter(e.target.value)}
              placeholder="Search keys or values..."
              className="w-full pl-8 pr-3 py-1 bg-surface border border-surface-border rounded-md text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-primary focus:border-primary"
              aria-label="Filter JSON keys and values"
            />
            {searchFilter && (
              <button
                type="button"
                onClick={() => setSearchFilter('')}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 text-[10px]"
                aria-label="Clear search"
              >
                ✕
              </button>
            )}
          </div>

          {/* Expand / Collapse Controls */}
          <div className="flex items-center gap-1.5">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleExpandAll}
              leftIcon={<Maximize2 className="w-3 h-3 text-slate-400" />}
              className="h-7 px-2 text-[11px] text-slate-300"
              aria-label="Expand all JSON nodes"
            >
              Expand All
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleCollapseAll}
              leftIcon={<Minimize2 className="w-3 h-3 text-slate-400" />}
              className="h-7 px-2 text-[11px] text-slate-300"
              aria-label="Collapse all JSON nodes"
            >
              Collapse All
            </Button>
          </div>
        </div>
      )}

      {/* 3. Main Display Area */}
      <div className="p-4 max-h-[650px] overflow-auto bg-surface-elevated/40">
        {viewMode === 'tree' ? (
          <div className="space-y-0.5">
            <JsonTreeNode
              key="root"
              value={reportData}
              depth={0}
              expandedKeys={expandedKeys}
              toggleKey={toggleKey}
              path="root"
              searchFilter={searchFilter}
            />
          </div>
        ) : (
          <pre className="p-3 bg-surface-elevated/70 border border-surface-border rounded-lg text-xs font-mono text-slate-300 overflow-x-auto select-text leading-relaxed">
            {rawJsonString}
          </pre>
        )}
      </div>

      {/* 4. Footer info */}
      <div className="p-2.5 bg-surface-elevated/30 border-t border-surface-border/50 flex items-center justify-between text-[11px] text-slate-500 font-mono">
        <span className="flex items-center gap-1.5">
          <FileCheck className="w-3.5 h-3.5 text-emerald-400" />
          Endpoint: GET /api/v1/runs/{runId}/report.json
        </span>
        <span>RFC-8259 JSON</span>
      </div>
    </div>
  );
};
