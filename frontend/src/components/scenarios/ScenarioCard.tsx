import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, Shield, CheckCircle } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { SeverityBadge, CategoryBadge } from '@/components/ui/StatusBadge';
import { Badge } from '@/components/ui/Badge';
import type { ScenarioSummaryResponse } from '@/api/types';

interface ScenarioCardProps {
  scenario: ScenarioSummaryResponse;
}

export const ScenarioCard: React.FC<ScenarioCardProps> = ({ scenario }) => {
  return (
    <Card className="flex flex-col justify-between hover:border-slate-600 transition-all duration-200 group relative">
      <CardHeader className="space-y-3 pb-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded font-mono text-[11px] font-semibold bg-surface-tertiary text-cyan-400 border border-slate-700/60">
              {scenario.scenario_id}
            </span>
            {scenario.enabled && (
              <span className="inline-flex items-center gap-1 text-[10px] text-slate-400" title="Enabled for evaluation">
                <CheckCircle className="w-3 h-3 text-emerald-400" aria-hidden="true" />
                <span>Enabled</span>
              </span>
            )}
          </div>
          <div className="flex items-center gap-1.5 flex-wrap">
            <CategoryBadge category={scenario.category} size="sm" />
            <SeverityBadge severity={scenario.risk_level} size="sm" />
          </div>
        </div>

        <div>
          <CardTitle className="text-base text-slate-100 group-hover:text-cyan-300 transition-colors">
            <Link to={`/scenarios/${encodeURIComponent(scenario.scenario_id)}`} className="focus:outline-none">
              {scenario.name}
            </Link>
          </CardTitle>
          <p className="text-xs text-slate-400 mt-1 line-clamp-2 leading-relaxed">
            {scenario.description}
          </p>
        </div>
      </CardHeader>

      <CardContent className="space-y-3 pt-0 flex-1">
        <div className="p-2.5 rounded-lg bg-surface-tertiary/70 border border-surface-border text-xs">
          <div className="flex items-start gap-2">
            <Shield className="w-3.5 h-3.5 text-brand-blue shrink-0 mt-0.5" aria-hidden="true" />
            <div>
              <span className="font-semibold text-slate-300 block mb-0.5 text-[11px] uppercase tracking-wider">
                Security Objective
              </span>
              <p className="text-slate-300 line-clamp-2 leading-normal">
                {scenario.security_objective}
              </p>
            </div>
          </div>
        </div>

        {scenario.tags && scenario.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 items-center pt-1">
            {scenario.tags.map((tag) => (
              <Badge key={tag} variant="default" size="sm" className="text-[10px] py-0 px-1.5 text-slate-400">
                #{tag}
              </Badge>
            ))}
          </div>
        )}
      </CardContent>

      <CardFooter className="pt-3 border-t border-surface-border/60 flex items-center justify-between">
        <span className="text-[11px] text-slate-500 font-mono">
          v{scenario.version}
        </span>
        <Link to={`/scenarios/${encodeURIComponent(scenario.scenario_id)}`}>
          <Button
            variant="ghost"
            size="sm"
            rightIcon={<ArrowRight className="w-3.5 h-3.5 transition-transform group-hover:translate-x-0.5" />}
            className="text-xs text-slate-300 hover:text-white"
          >
            Inspect Scenario
          </Button>
        </Link>
      </CardFooter>
    </Card>
  );
};
