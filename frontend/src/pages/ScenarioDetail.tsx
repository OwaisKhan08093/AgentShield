import React, { useEffect, useState, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Shield,
  FileCode,
  Tag,
  CheckCircle,
  AlertCircle,
  Layers,
  Copy,
  Check,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { SeverityBadge, CategoryBadge } from '@/components/ui/StatusBadge';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorAlert } from '@/components/ui/ErrorAlert';
import { ExpectedBehaviorPanel } from '@/components/scenarios/ExpectedBehaviorPanel';
import { apiClient, ApiClientError } from '@/api/client';
import type { ScenarioDetailResponse } from '@/api/types';

export const ScenarioDetail: React.FC = () => {
  const { scenarioId } = useParams<{ scenarioId: string }>();
  const [scenario, setScenario] = useState<ScenarioDetailResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isNotFound, setIsNotFound] = useState(false);
  const [copiedId, setCopiedId] = useState(false);

  const fetchScenario = useCallback(async () => {
    if (!scenarioId) return;
    setIsLoading(true);
    setError(null);
    setIsNotFound(false);

    try {
      const data = await apiClient.getScenario(scenarioId);
      setScenario(data);
    } catch (err) {
      if (err instanceof ApiClientError && err.status === 404) {
        setIsNotFound(true);
      } else {
        const msg = err instanceof Error ? err.message : 'Failed to retrieve scenario details';
        setError(msg);
      }
    } finally {
      setIsLoading(false);
    }
  }, [scenarioId]);

  useEffect(() => {
    let currentId = scenarioId;
    let mounted = true;

    if (!scenarioId) {
      setIsLoading(false);
      setIsNotFound(true);
      return;
    }

    const load = async () => {
      setIsLoading(true);
      setError(null);
      setIsNotFound(false);

      try {
        const data = await apiClient.getScenario(scenarioId);
        // Guard against stale requests if user navigated to another scenario
        if (mounted && currentId === scenarioId) {
          setScenario(data);
        }
      } catch (err) {
        if (mounted && currentId === scenarioId) {
          if (err instanceof ApiClientError && err.status === 404) {
            setIsNotFound(true);
          } else {
            const msg = err instanceof Error ? err.message : 'Failed to retrieve scenario details';
            setError(msg);
          }
        }
      } finally {
        if (mounted && currentId === scenarioId) {
          setIsLoading(false);
        }
      }
    };

    load();

    return () => {
      mounted = false;
    };
  }, [scenarioId]);

  const handleCopyId = () => {
    if (scenario?.scenario_id) {
      navigator.clipboard?.writeText(scenario.scenario_id);
      setCopiedId(true);
      setTimeout(() => setCopiedId(false), 2000);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Top Navigation & Back Action */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Link to="/scenarios">
          <Button variant="secondary" size="sm" leftIcon={<ArrowLeft className="w-3.5 h-3.5" />}>
            Back to Scenarios
          </Button>
        </Link>

        {scenario && (
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleCopyId}
              leftIcon={copiedId ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              className="text-xs"
            >
              {copiedId ? 'Copied ID' : 'Copy ID'}
            </Button>
          </div>
        )}
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="min-h-[50vh] flex flex-col items-center justify-center space-y-3">
          <LoadingSpinner size="lg" text={`Loading scenario details for ${scenarioId}...`} />
        </div>
      )}

      {/* 404 Not Found State */}
      {!isLoading && isNotFound && (
        <div className="min-h-[50vh] flex flex-col items-center justify-center text-center px-4 space-y-4">
          <div className="w-16 h-16 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 shadow-inner">
            <AlertCircle className="w-8 h-8" />
          </div>
          <div className="space-y-1">
            <h2 className="text-xl font-bold text-slate-100">Scenario Not Found</h2>
            <p className="text-xs text-slate-400 max-w-md">
              No registered scenario was found matching ID: <code className="text-cyan-400 font-mono">{scenarioId}</code>.
            </p>
          </div>
          <Link to="/scenarios">
            <Button variant="primary">Return to Catalog</Button>
          </Link>
        </div>
      )}

      {/* API Error State */}
      {!isLoading && !isNotFound && error && (
        <ErrorAlert
          title="Failed to Load Scenario"
          message={error}
          onRetry={fetchScenario}
        />
      )}

      {/* Loaded Content */}
      {!isLoading && !isNotFound && scenario && (
        <div className="space-y-6">
          {/* Header Card */}
          <div className="p-6 rounded-2xl bg-surface border border-surface-border space-y-4 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2.5">
                <span className="px-2.5 py-1 rounded font-mono text-xs font-semibold bg-surface-tertiary text-cyan-300 border border-slate-700">
                  {scenario.scenario_id}
                </span>
                <span className="text-xs font-mono text-slate-500">v{scenario.version}</span>
                {scenario.enabled && (
                  <Badge variant="pass" size="sm" className="gap-1">
                    <CheckCircle className="w-3 h-3" />
                    <span>Enabled</span>
                  </Badge>
                )}
              </div>

              <div className="flex items-center gap-2">
                <CategoryBadge category={scenario.category} size="md" />
                <SeverityBadge severity={scenario.risk_level} size="md" />
              </div>
            </div>

            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">
                {scenario.name}
              </h1>
              <p className="text-sm text-slate-300 mt-2 leading-relaxed max-w-3xl">
                {scenario.description}
              </p>
            </div>

            {/* Tags */}
            {scenario.tags && scenario.tags.length > 0 && (
              <div className="flex flex-wrap items-center gap-1.5 pt-2 border-t border-surface-border/60">
                <Tag className="w-3.5 h-3.5 text-slate-500" />
                <span className="text-xs text-slate-400 mr-1">Tags:</span>
                {scenario.tags.map((tag) => (
                  <Badge key={tag} variant="default" size="sm" className="text-slate-300 font-mono text-[11px]">
                    #{tag}
                  </Badge>
                ))}
              </div>
            )}
          </div>

          {/* Security Objective Banner */}
          <div className="p-4 rounded-xl bg-cyan-950/20 border border-cyan-500/30 text-xs space-y-1.5">
            <div className="flex items-center gap-2 text-cyan-400 font-semibold text-sm">
              <Shield className="w-4 h-4 shrink-0" aria-hidden="true" />
              <span>Target Security Objective</span>
            </div>
            <p className="text-slate-200 leading-relaxed font-sans text-xs pl-6">
              {scenario.security_objective}
            </p>
          </div>

          {/* Expected Behavior and Assertions */}
          <ExpectedBehaviorPanel
            expectedBehavior={scenario.expected_behavior}
            successCondition={scenario.success_condition}
            failureCondition={scenario.failure_condition}
          />

          {/* Scenario Metadata Card */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center gap-2">
                <FileCode className="w-4 h-4 text-brand-blue" aria-hidden="true" />
                <CardTitle className="text-sm text-slate-200">Scenario Metadata & Specification</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="space-y-3 pt-0 text-xs">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="p-3 rounded-lg bg-surface-tertiary border border-surface-border space-y-1">
                  <span className="text-slate-500 text-[11px] uppercase tracking-wider block">Attack Vector</span>
                  <span className="text-slate-200 font-medium block">{scenario.category}</span>
                </div>
                <div className="p-3 rounded-lg bg-surface-tertiary border border-surface-border space-y-1">
                  <span className="text-slate-500 text-[11px] uppercase tracking-wider block">Risk Severity</span>
                  <span className="text-slate-200 font-medium uppercase block">{scenario.risk_level}</span>
                </div>
                <div className="p-3 rounded-lg bg-surface-tertiary border border-surface-border space-y-1">
                  <span className="text-slate-500 text-[11px] uppercase tracking-wider block">Registry Status</span>
                  <span className="text-emerald-400 font-medium block">Active & Deterministic</span>
                </div>
              </div>

              <div className="p-3 rounded-lg bg-surface-tertiary border border-surface-border flex items-center justify-between text-slate-400">
                <span className="flex items-center gap-2">
                  <Layers className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Evaluation Suite: <strong>support-agent-security-v1</strong></span>
                </span>
                <span className="text-[11px] font-mono">ReferenceAgent Baseline</span>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default ScenarioDetail;
