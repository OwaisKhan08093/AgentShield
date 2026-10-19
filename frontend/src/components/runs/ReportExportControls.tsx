import React, { useState } from 'react';
import {
  Download,
  Copy,
  Check,
  FileSpreadsheet,
  FileCode,
  ShieldAlert,
  BarChart3,
  AlertCircle,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import {
  downloadBlob,
  generateScenarioResultsCsv,
  generateFindingsCsv,
  generateMetricsCsv,
} from '@/utils/csvExport';
import type { EvaluationReport } from '@/api/types';

interface ReportExportControlsProps {
  runId: string;
  report?: EvaluationReport | null;
  exportData?: Record<string, unknown> | null;
  className?: string;
}

export const ReportExportControls: React.FC<ReportExportControlsProps> = ({
  runId,
  report,
  exportData,
  className = '',
}) => {
  const [copyStatus, setCopyStatus] = useState<'idle' | 'copied' | 'error'>('idle');
  const [copyErrorMsg, setCopyErrorMsg] = useState<string | null>(null);

  const findingsCount = report?.findings?.length ?? 0;
  const scenariosCount = report?.scenario_evaluations?.length ?? 0;
  const hasMetrics = Boolean(report?.metrics);

  const getJsonExportString = (): string => {
    if (exportData) {
      return JSON.stringify(exportData, null, 2);
    }
    if (report) {
      return JSON.stringify({ schema_version: '1.0.0', report }, null, 2);
    }
    return '';
  };

  const handleCopyJson = async () => {
    try {
      const jsonStr = getJsonExportString();
      if (!jsonStr) {
        throw new Error('No report JSON data available to copy');
      }
      await navigator.clipboard.writeText(jsonStr);
      setCopyStatus('copied');
      setCopyErrorMsg(null);
      setTimeout(() => setCopyStatus('idle'), 2500);
    } catch (err) {
      setCopyStatus('error');
      setCopyErrorMsg(err instanceof Error ? err.message : 'Clipboard copy failed');
      setTimeout(() => setCopyStatus('idle'), 3500);
    }
  };

  const handleDownloadJson = () => {
    const jsonStr = getJsonExportString();
    if (!jsonStr) return;
    downloadBlob(
      `agentshield-report-${runId}.json`,
      jsonStr,
      'application/json;charset=utf-8;'
    );
  };

  const handleDownloadScenariosCsv = () => {
    if (!report?.scenario_evaluations) return;
    const csvContent = generateScenarioResultsCsv(report.scenario_evaluations, runId);
    downloadBlob(`agentshield-scenarios-${runId}.csv`, csvContent);
  };

  const handleDownloadFindingsCsv = () => {
    if (!report?.findings || report.findings.length === 0) return;
    const csvContent = generateFindingsCsv(report.findings, runId);
    downloadBlob(`agentshield-findings-${runId}.csv`, csvContent);
  };

  const handleDownloadMetricsCsv = () => {
    if (!report) return;
    const csvContent = generateMetricsCsv(report);
    downloadBlob(`agentshield-metrics-${runId}.csv`, csvContent);
  };

  const isDataAvailable = Boolean(report || exportData);

  return (
    <div
      className={`flex flex-wrap items-center justify-between gap-3 p-3 bg-surface-elevated/40 border border-surface-border rounded-lg ${className}`}
      role="toolbar"
      aria-label="Report export and copy actions"
    >
      <div className="flex items-center gap-2 text-xs text-slate-400 font-medium">
        <Download className="w-4 h-4 text-primary" />
        <span>Export Report Data:</span>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {/* Copy JSON Action */}
        <Button
          variant="ghost"
          size="sm"
          onClick={handleCopyJson}
          disabled={!isDataAvailable}
          leftIcon={
            copyStatus === 'copied' ? (
              <Check className="w-3.5 h-3.5 text-emerald-400" />
            ) : copyStatus === 'error' ? (
              <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
            ) : (
              <Copy className="w-3.5 h-3.5" />
            )
          }
          className={`h-8 px-2.5 text-xs ${
            copyStatus === 'copied'
              ? 'text-emerald-400 hover:text-emerald-300'
              : copyStatus === 'error'
              ? 'text-rose-400 hover:text-rose-300'
              : 'text-slate-300 hover:text-white'
          }`}
          aria-label="Copy full report JSON to clipboard"
          title={copyErrorMsg || 'Copy JSON report to clipboard'}
        >
          {copyStatus === 'copied'
            ? 'Copied JSON!'
            : copyStatus === 'error'
            ? 'Copy Failed'
            : 'Copy JSON'}
        </Button>

        {/* Download Full JSON Report */}
        <Button
          variant="secondary"
          size="sm"
          onClick={handleDownloadJson}
          disabled={!isDataAvailable}
          leftIcon={<FileCode className="w-3.5 h-3.5 text-primary" />}
          className="h-8 px-2.5 text-xs text-slate-200"
          aria-label="Download raw JSON report"
          title="Download the full machine-readable evaluation report as JSON"
        >
          JSON Report
        </Button>

        {/* Download Scenario Results CSV */}
        <Button
          variant="secondary"
          size="sm"
          onClick={handleDownloadScenariosCsv}
          disabled={!isDataAvailable || scenariosCount === 0}
          leftIcon={<FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400" />}
          className="h-8 px-2.5 text-xs text-slate-200"
          aria-label="Download scenario evaluation results CSV"
          title={
            scenariosCount === 0
              ? 'No scenario evaluation results available'
              : `Download ${scenariosCount} scenario evaluation results as CSV`
          }
        >
          Scenarios CSV
        </Button>

        {/* Download Findings CSV */}
        <Button
          variant="secondary"
          size="sm"
          onClick={handleDownloadFindingsCsv}
          disabled={!isDataAvailable || findingsCount === 0}
          leftIcon={<ShieldAlert className="w-3.5 h-3.5 text-rose-400" />}
          className="h-8 px-2.5 text-xs text-slate-200 disabled:opacity-50"
          aria-label="Download security findings CSV"
          title={
            findingsCount === 0
              ? 'No security findings recorded in this report'
              : `Download ${findingsCount} security findings as CSV`
          }
        >
          Findings CSV ({findingsCount})
        </Button>

        {/* Download Metrics CSV */}
        <Button
          variant="secondary"
          size="sm"
          onClick={handleDownloadMetricsCsv}
          disabled={!isDataAvailable || !hasMetrics}
          leftIcon={<BarChart3 className="w-3.5 h-3.5 text-cyan-400" />}
          className="h-8 px-2.5 text-xs text-slate-200"
          aria-label="Download evaluation metrics CSV"
          title="Download metrics and categorical breakdowns as CSV"
        >
          Metrics CSV
        </Button>
      </div>
    </div>
  );
};
