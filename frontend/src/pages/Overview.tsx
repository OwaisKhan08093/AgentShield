import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldCheck,
  FileCode,
  PlayCircle,
  Database,
  ExternalLink,
  Lock,
  ArrowRight,
  Terminal,
  Activity,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { OutcomeBadge } from '@/components/ui/StatusBadge';
import { apiClient } from '@/api/client';
import { API_CONFIG } from '@/api/config';
import type { RootResponse } from '@/api/types';

export const Overview: React.FC = () => {
  const [backendMeta, setBackendMeta] = useState<RootResponse | null>(null);
  const [backendError, setBackendError] = useState<string | null>(null);
  const [isConnecting, setIsConnecting] = useState(true);

  useEffect(() => {
    let mounted = true;
    async function fetchBackendInfo() {
      setIsConnecting(true);
      try {
        const data = await apiClient.getRoot();
        if (mounted) {
          setBackendMeta(data);
          setBackendError(null);
        }
      } catch (err) {
        if (mounted) {
          setBackendError(err instanceof Error ? err.message : 'Connection failed');
        }
      } finally {
        if (mounted) {
          setIsConnecting(false);
        }
      }
    }
    fetchBackendInfo();
    return () => {
      mounted = false;
    };
  }, []);

  const pipelineSteps = [
    {
      num: '01',
      title: 'Scenario Catalog',
      desc: '16 canonical benchmarks covering OWASP LLM vulnerabilities & benign positive controls.',
      icon: FileCode,
      color: 'text-blue-400',
    },
    {
      num: '02',
      title: 'Scenario Runner',
      desc: 'Deterministic orchestration with thread-level timeout protection and error containment.',
      icon: PlayCircle,
      color: 'text-indigo-400',
    },
    {
      num: '03',
      title: 'Authorization Guard',
      desc: 'Defense-in-depth policy enforcement on data tools, parameter ranges, and tenant isolation.',
      icon: Lock,
      color: 'text-cyan-400',
    },
    {
      num: '04',
      title: 'Trace Recording',
      desc: 'Chronological event recording with automated scrubbing of credentials, API tokens, and PII.',
      icon: Terminal,
      color: 'text-emerald-400',
    },
    {
      num: '05',
      title: 'Security Evaluator',
      desc: 'Rule-based assertions computing Attack Success Rate (ASR) and Protection Success Rate (PSR).',
      icon: ShieldCheck,
      color: 'text-amber-400',
    },
    {
      num: '06',
      title: 'Relational Storage',
      desc: 'Atomic SQLite persistence storing runs, findings, traces, and machine-readable JSON reports.',
      icon: Database,
      color: 'text-purple-400',
    },
  ];

  return (
    <div className="space-y-8 pb-10">
      {/* Hero Banner */}
      <section className="relative overflow-hidden rounded-2xl border border-surface-border bg-gradient-to-br from-surface to-surface-elevated/40 p-6 md:p-8">
        <div className="max-w-3xl space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium bg-brand-blue/10 text-brand-blue border border-brand-blue/20">
            <ShieldCheck className="w-3.5 h-3.5" aria-hidden="true" />
            <span>AI Agent Security Benchmark Engine</span>
          </div>

          <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-white leading-tight">
            Security evaluation platform for tool-using AI agents
          </h2>

          <p className="text-sm text-slate-300 leading-relaxed max-w-2xl">
            AgentShield systematically executes, audits, and scores customer-support agents against authorization
            violations, horizontal privilege escalations (IDOR), refund threshold bypasses, and adversarial prompt
            injections.
          </p>

          <div className="flex flex-wrap items-center gap-3 pt-2">
            <Link to="/scenarios">
              <Button variant="primary" rightIcon={<ArrowRight className="w-4 h-4" />}>
                Explore 16 Scenarios
              </Button>
            </Link>

            <Link to="/runs">
              <Button variant="secondary" leftIcon={<PlayCircle className="w-4 h-4" />}>
                View Evaluation Runs
              </Button>
            </Link>

            <a
              href={`${API_CONFIG.baseUrl}/docs`}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 px-3 py-2 transition-colors"
            >
              <span>Swagger API Docs</span>
              <ExternalLink className="w-3 h-3 text-slate-500" aria-hidden="true" />
            </a>
          </div>
        </div>
      </section>

      {/* Core Security Principle & Backend Health Status */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <Card className="md:col-span-2">
          <CardHeader>
            <div className="flex items-center gap-2 text-brand-blue">
              <Lock className="w-4 h-4" aria-hidden="true" />
              <CardTitle>Core Design Principle</CardTitle>
            </div>
            <CardDescription>Foundational security architecture guiding AgentShield evaluations</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <blockquote className="border-l-2 border-brand-blue/60 pl-3.5 italic text-xs text-slate-300 leading-relaxed font-sans">
              &ldquo;The language model is not the security boundary. Authorization must be enforced by the tool or
              service that owns the data and action.&rdquo;
            </blockquote>
            <p className="text-xs text-slate-400 leading-relaxed">
              AgentShield evaluates whether external authorization guards and policy enforcement layers reliably
              prevent unauthorized operations even when an agent encounters adversarial or deceptive prompts.
            </p>
          </CardContent>
        </Card>

        {/* Live Backend Connection Card */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-slate-200">
                <Activity className="w-4 h-4 text-brand-blue" aria-hidden="true" />
                <CardTitle>Backend Status</CardTitle>
              </div>
              <Badge variant={backendMeta ? 'pass' : isConnecting ? 'warning' : 'fail'} size="sm">
                {isConnecting ? 'Checking' : backendMeta ? 'Online' : 'Offline'}
              </Badge>
            </div>
            <CardDescription>Connection to FastAPI evaluation service</CardDescription>
          </CardHeader>
          <CardContent className="space-y-2.5 text-xs">
            <div className="flex items-center justify-between py-1 border-b border-surface-border/50">
              <span className="text-slate-400">Endpoint</span>
              <span className="font-mono text-[11px] text-slate-300 truncate max-w-[150px]">{API_CONFIG.baseUrl}</span>
            </div>
            <div className="flex items-center justify-between py-1 border-b border-surface-border/50">
              <span className="text-slate-400">Service</span>
              <span className="text-slate-300">{backendMeta?.name || 'AgentShield API'}</span>
            </div>
            <div className="flex items-center justify-between py-1">
              <span className="text-slate-400">API Version</span>
              <span className="font-mono text-[11px] text-slate-300">{backendMeta?.version || 'v1.0.0'}</span>
            </div>

            {backendError && (
              <div className="mt-2 p-2 rounded bg-rose-500/10 border border-rose-500/20 text-rose-300 text-[11px] flex items-start gap-1.5">
                <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                <span>Backend unreachable. Start via: uvicorn app.main:app</span>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Evaluation Pipeline Overview */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-semibold text-slate-100 tracking-tight">Security Evaluation Pipeline</h3>
            <p className="text-xs text-slate-400">Deterministic six-stage benchmark lifecycle</p>
          </div>
          <span className="text-xs text-slate-500 hidden sm:inline-block">End-to-End Traceable</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {pipelineSteps.map((step) => {
            const Icon = step.icon;
            return (
              <Card key={step.num} className="hover:border-surface-border-subtle transition-colors group">
                <CardContent className="p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono font-bold text-slate-500 tracking-wider">
                      STEP {step.num}
                    </span>
                    <div className="w-7 h-7 rounded-lg bg-surface-elevated flex items-center justify-center border border-surface-border">
                      <Icon className={`w-3.5 h-3.5 ${step.color}`} aria-hidden="true" />
                    </div>
                  </div>
                  <h4 className="text-sm font-semibold text-slate-200 group-hover:text-white transition-colors">
                    {step.title}
                  </h4>
                  <p className="text-xs text-slate-400 leading-relaxed">{step.desc}</p>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </section>

      {/* Strict Outcome Semantics Showcase */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" aria-hidden="true" />
            <CardTitle>Transparent Uncertainty: Outcome Semantics</CardTitle>
          </div>
          <CardDescription>
            AgentShield enforces strict separation between security passes, assertion breaches, runner exceptions, and
            unexecuted scenarios.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-3 rounded-lg bg-surface-elevated border border-surface-border space-y-1.5">
              <OutcomeBadge outcome="pass" />
              <p className="text-xs text-slate-400 leading-relaxed pt-1">
                All expected security assertions and task criteria were completely satisfied.
              </p>
            </div>
            <div className="p-3 rounded-lg bg-surface-elevated border border-surface-border space-y-1.5">
              <OutcomeBadge outcome="fail" />
              <p className="text-xs text-slate-400 leading-relaxed pt-1">
                Security boundary breached, policy violated, or expected authorization denial was missing.
              </p>
            </div>
            <div className="p-3 rounded-lg bg-surface-elevated border border-surface-border space-y-1.5">
              <OutcomeBadge outcome="error" />
              <p className="text-xs text-slate-400 leading-relaxed pt-1">
                Execution timed out or runner caught unhandled exception. Never treated as a security pass.
              </p>
            </div>
            <div className="p-3 rounded-lg bg-surface-elevated border border-surface-border space-y-1.5">
              <OutcomeBadge outcome="not_run" />
              <p className="text-xs text-slate-400 leading-relaxed pt-1">
                Scenario was skipped or interrupted prior to execution. Does not receive success credit.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
