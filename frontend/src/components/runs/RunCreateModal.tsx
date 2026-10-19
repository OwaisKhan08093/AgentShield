import React, { useState, useEffect } from 'react';
import { Play, X, CheckSquare, Square, Shield, Settings } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { SeverityBadge } from '@/components/ui/StatusBadge';
import { ErrorAlert } from '@/components/ui/ErrorAlert';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { apiClient } from '@/api/client';
import type { ScenarioSummaryResponse, CreateRunRequest } from '@/api/types';

interface RunCreateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onRunCreated: (runId: string) => void;
  preselectedScenarioId?: string;
}

export const RunCreateModal: React.FC<RunCreateModalProps> = ({
  isOpen,
  onClose,
  onRunCreated,
  preselectedScenarioId,
}) => {
  const [scenarios, setScenarios] = useState<ScenarioSummaryResponse[]>([]);
  const [isLoadingScenarios, setIsLoadingScenarios] = useState(false);
  const [scenariosError, setScenariosError] = useState<string | null>(null);

  // Form State
  const [suiteId] = useState('support-agent-security-v1');
  const [agentId] = useState('reference-agent');
  const [runAll, setRunAll] = useState(!preselectedScenarioId);
  const [selectedScenarioIds, setSelectedScenarioIds] = useState<string[]>(
    preselectedScenarioId ? [preselectedScenarioId] : []
  );

  // Advanced Options
  const [continueOnError, setContinueOnError] = useState(true);
  const [recordTrace, setRecordTrace] = useState(true);
  const [timeoutSeconds, setTimeoutSeconds] = useState<string>('');
  const [showOptions, setShowOptions] = useState(false);

  // Submission State
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen) {
      setIsLoadingScenarios(true);
      setScenariosError(null);
      setSubmitError(null);

      apiClient
        .listScenarios()
        .then((data) => {
          setScenarios(Array.isArray(data) ? data : []);
          if (preselectedScenarioId) {
            setSelectedScenarioIds([preselectedScenarioId]);
            setRunAll(false);
          }
        })
        .catch((err) => {
          setScenariosError(err instanceof Error ? err.message : 'Failed to load scenario catalog');
        })
        .finally(() => {
          setIsLoadingScenarios(false);
        });
    }
  }, [isOpen, preselectedScenarioId]);

  if (!isOpen) return null;

  const toggleScenario = (id: string) => {
    setSelectedScenarioIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    );
  };

  const selectAllScenarios = () => {
    setSelectedScenarioIds(scenarios.map((s) => s.scenario_id));
  };

  const deselectAllScenarios = () => {
    setSelectedScenarioIds([]);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isSubmitting) return;

    if (!runAll && selectedScenarioIds.length === 0) {
      setSubmitError('Please select at least one scenario to execute, or choose "Run All Scenarios".');
      return;
    }

    let parsedTimeout: number | null = null;
    if (timeoutSeconds.trim()) {
      const num = parseFloat(timeoutSeconds);
      if (isNaN(num) || num < 0.01 || num > 300) {
        setSubmitError('Execution timeout must be a valid number between 0.01 and 300 seconds.');
        return;
      }
      parsedTimeout = num;
    }

    setIsSubmitting(true);
    setSubmitError(null);

    const payload: CreateRunRequest = {
      suite_id: suiteId,
      agent_id: agentId,
      scenario_ids: runAll ? null : selectedScenarioIds,
      options: {
        continue_on_error: continueOnError,
        record_trace: recordTrace,
        timeout_seconds: parsedTimeout,
      },
    };

    try {
      const res = await apiClient.createRun(payload);
      if (res && res.run_id) {
        onRunCreated(res.run_id);
      } else {
        setSubmitError('Backend did not return a valid run ID.');
      }
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : 'Evaluation run execution failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  const activeScenarioCount = runAll ? scenarios.length : selectedScenarioIds.length;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm overflow-y-auto"
      role="dialog"
      aria-modal="true"
      aria-labelledby="run-modal-title"
    >
      <div className="relative w-full max-w-2xl bg-surface border border-surface-border rounded-2xl shadow-2xl overflow-hidden my-8">
        {/* Modal Header */}
        <div className="flex items-center justify-between p-5 border-b border-surface-border/60 bg-surface-elevated/40">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-lg bg-brand-blue/10 border border-brand-blue/30 flex items-center justify-center text-brand-blue">
              <Play className="w-4 h-4 fill-current" />
            </div>
            <div>
              <h2 id="run-modal-title" className="text-base font-bold text-slate-100">
                Launch Evaluation Run
              </h2>
              <p className="text-xs text-slate-400">
                Execute scenarios against the deterministic ReferenceAgent and evaluate security policies
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            disabled={isSubmitting}
            className="text-slate-400 hover:text-slate-200 transition-colors p-1.5 rounded-lg hover:bg-surface-elevated"
            aria-label="Close dialog"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {submitError && (
            <ErrorAlert
              title="Failed to Launch Evaluation"
              message={submitError}
            />
          )}

          {/* Target Suite & Agent Metadata */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 p-3 rounded-xl bg-surface-tertiary border border-surface-border text-xs">
            <div>
              <span className="text-slate-400 block text-[11px] uppercase tracking-wider font-medium">
                Target Evaluation Suite
              </span>
              <span className="text-slate-200 font-mono font-semibold">{suiteId}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[11px] uppercase tracking-wider font-medium">
                Evaluated Target Agent
              </span>
              <span className="text-cyan-400 font-mono font-semibold">{agentId} (Synthetic)</span>
            </div>
          </div>

          {/* Scenario Selection Mode */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-slate-300 block">
                Target Scenarios Selection
              </label>
              <span className="text-xs font-medium text-cyan-400">
                {activeScenarioCount} scenario{activeScenarioCount !== 1 ? 's' : ''} selected
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <label
                className={`flex items-start gap-3 p-3.5 rounded-xl border cursor-pointer transition-all ${
                  runAll
                    ? 'bg-brand-blue/10 border-brand-blue/50 text-slate-100 ring-1 ring-brand-blue/30'
                    : 'bg-surface-tertiary border-surface-border text-slate-400 hover:bg-surface-elevated'
                }`}
              >
                <input
                  type="radio"
                  name="scenarioSelection"
                  checked={runAll}
                  onChange={() => setRunAll(true)}
                  className="mt-0.5 accent-brand-blue"
                  disabled={isSubmitting}
                />
                <div>
                  <span className="text-xs font-semibold text-slate-100 block">
                    Run All Scenarios (Full Suite)
                  </span>
                  <span className="text-[11px] text-slate-400 block mt-0.5">
                    Evaluates all {scenarios.length || 16} canonical benchmarks across all categories
                  </span>
                </div>
              </label>

              <label
                className={`flex items-start gap-3 p-3.5 rounded-xl border cursor-pointer transition-all ${
                  !runAll
                    ? 'bg-brand-blue/10 border-brand-blue/50 text-slate-100 ring-1 ring-brand-blue/30'
                    : 'bg-surface-tertiary border-surface-border text-slate-400 hover:bg-surface-elevated'
                }`}
              >
                <input
                  type="radio"
                  name="scenarioSelection"
                  checked={!runAll}
                  onChange={() => setRunAll(false)}
                  className="mt-0.5 accent-brand-blue"
                  disabled={isSubmitting}
                />
                <div>
                  <span className="text-xs font-semibold text-slate-100 block">
                    Select Specific Scenarios
                  </span>
                  <span className="text-[11px] text-slate-400 block mt-0.5">
                    Pick target vulnerability test cases to execute
                  </span>
                </div>
              </label>
            </div>

            {/* Custom Scenario Checklist */}
            {!runAll && (
              <div className="space-y-2 p-3 rounded-xl bg-surface-tertiary border border-surface-border">
                <div className="flex items-center justify-between pb-2 border-b border-surface-border/60 text-xs">
                  <span className="text-slate-400">Available Canonical Scenarios:</span>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={selectAllScenarios}
                      disabled={isSubmitting}
                      className="text-[11px] text-brand-blue hover:underline"
                    >
                      Select All
                    </button>
                    <span className="text-slate-600">|</span>
                    <button
                      type="button"
                      onClick={deselectAllScenarios}
                      disabled={isSubmitting}
                      className="text-[11px] text-slate-400 hover:underline"
                    >
                      Deselect All
                    </button>
                  </div>
                </div>

                {isLoadingScenarios && (
                  <div className="py-6 flex justify-center">
                    <LoadingSpinner size="sm" text="Loading scenarios catalog..." />
                  </div>
                )}

                {scenariosError && (
                  <p className="text-xs text-rose-400 py-2">{scenariosError}</p>
                )}

                {!isLoadingScenarios && !scenariosError && (
                  <div className="max-h-48 overflow-y-auto space-y-1.5 pr-1">
                    {scenarios.map((s) => {
                      const isSelected = selectedScenarioIds.includes(s.scenario_id);
                      return (
                        <div
                          key={s.scenario_id}
                          onClick={() => !isSubmitting && toggleScenario(s.scenario_id)}
                          className={`flex items-center justify-between p-2 rounded-lg cursor-pointer text-xs transition-colors ${
                            isSelected
                              ? 'bg-surface-elevated text-slate-100 border border-brand-blue/30'
                              : 'text-slate-400 hover:bg-surface-elevated/50'
                          }`}
                        >
                          <div className="flex items-center gap-2 truncate">
                            {isSelected ? (
                              <CheckSquare className="w-4 h-4 text-cyan-400 shrink-0" />
                            ) : (
                              <Square className="w-4 h-4 text-slate-500 shrink-0" />
                            )}
                            <span className="font-mono text-[11px] text-slate-300 shrink-0">
                              {s.scenario_id}
                            </span>
                            <span className="truncate text-slate-200">{s.name}</span>
                          </div>
                          <SeverityBadge severity={s.risk_level} size="sm" className="ml-2 shrink-0" />
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Collapsible Advanced Execution Options */}
          <div className="space-y-2 border-t border-surface-border/60 pt-3">
            <button
              type="button"
              onClick={() => setShowOptions((prev) => !prev)}
              className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors"
            >
              <Settings className="w-3.5 h-3.5" />
              <span>{showOptions ? 'Hide Advanced Options' : 'Show Advanced Execution Options'}</span>
            </button>

            {showOptions && (
              <div className="p-3.5 rounded-xl bg-surface-tertiary border border-surface-border space-y-3 text-xs animate-in fade-in duration-150">
                <label className="flex items-center gap-2 cursor-pointer text-slate-300">
                  <input
                    type="checkbox"
                    checked={continueOnError}
                    onChange={(e) => setContinueOnError(e.target.checked)}
                    className="rounded border-surface-border accent-brand-blue"
                    disabled={isSubmitting}
                  />
                  <span>Continue suite evaluation on individual scenario failure</span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer text-slate-300">
                  <input
                    type="checkbox"
                    checked={recordTrace}
                    onChange={(e) => setRecordTrace(e.target.checked)}
                    className="rounded border-surface-border accent-brand-blue"
                    disabled={isSubmitting}
                  />
                  <span>Record and persist chronological execution traces</span>
                </label>

                <div className="w-full sm:w-60 pt-1">
                  <Input
                    label="Per-Scenario Timeout (seconds)"
                    placeholder="e.g. 5.0 (default: none)"
                    value={timeoutSeconds}
                    onChange={(e) => setTimeoutSeconds(e.target.value)}
                    disabled={isSubmitting}
                    helperText="Limits scenario execution duration (0.01 - 300s)"
                  />
                </div>
              </div>
            )}
          </div>

          {/* Modal Footer Actions */}
          <div className="flex items-center justify-between pt-3 border-t border-surface-border/60">
            <div className="text-[11px] text-slate-500 flex items-center gap-1.5">
              <Shield className="w-3.5 h-3.5 text-slate-500" />
              <span>Deterministic mock evaluation — no external LLM tokens</span>
            </div>

            <div className="flex items-center gap-2.5">
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={onClose}
                disabled={isSubmitting}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="primary"
                size="sm"
                isLoading={isSubmitting}
                leftIcon={<Play className="w-3.5 h-3.5 fill-current" />}
              >
                {isSubmitting ? 'Evaluating Suite...' : `Start Evaluation (${activeScenarioCount})`}
              </Button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};
