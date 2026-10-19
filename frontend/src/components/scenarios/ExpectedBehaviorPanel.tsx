import React from 'react';
import { CheckCircle2, XCircle, AlertTriangle, Shield, Lock, EyeOff, Wrench } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import type { ExpectedBehavior } from '@/api/types';

interface ExpectedBehaviorPanelProps {
  expectedBehavior: ExpectedBehavior;
  successCondition: string;
  failureCondition: string;
}

export const ExpectedBehaviorPanel: React.FC<ExpectedBehaviorPanelProps> = ({
  expectedBehavior,
  successCondition,
  failureCondition,
}) => {
  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case 'success':
        return (
          <Badge variant="pass" size="sm">
            <CheckCircle2 className="w-3 h-3" />
            <span>SUCCESS</span>
          </Badge>
        );
      case 'denied':
        return (
          <Badge variant="error" size="sm">
            <Lock className="w-3 h-3" />
            <span>DENIED (Blocked by Policy)</span>
          </Badge>
        );
      case 'error':
        return (
          <Badge variant="warning" size="sm">
            <AlertTriangle className="w-3 h-3" />
            <span>ERROR</span>
          </Badge>
        );
      default:
        return <Badge size="sm">{status.toUpperCase()}</Badge>;
    }
  };

  return (
    <div className="space-y-4">
      {/* Formal Behavior Assertions Card */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-cyan-400" aria-hidden="true" />
            <CardTitle className="text-base text-slate-100">
              Expected Security Behavior & Assertions
            </CardTitle>
          </div>
          {expectedBehavior.description && (
            <p className="text-xs text-slate-300 mt-1 leading-relaxed">
              {expectedBehavior.description}
            </p>
          )}
        </CardHeader>
        <CardContent className="space-y-4 pt-0">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
            {/* Expected Status */}
            <div className="p-3 rounded-lg bg-surface-tertiary border border-surface-border space-y-1.5">
              <span className="text-slate-400 font-medium block text-[11px] uppercase tracking-wider">
                Expected Execution Status
              </span>
              <div className="flex items-center gap-2">
                {getStatusBadge(expectedBehavior.expected_status)}
              </div>
            </div>

            {/* AuthZ Denial Required */}
            <div className="p-3 rounded-lg bg-surface-tertiary border border-surface-border space-y-1.5">
              <span className="text-slate-400 font-medium block text-[11px] uppercase tracking-wider">
                Authorization Denial Required
              </span>
              <div className="flex items-center gap-2">
                {expectedBehavior.must_have_authorization_denial ? (
                  <Badge variant="fail" size="sm">
                    <Lock className="w-3 h-3" />
                    <span>Yes — Tool Must Deny Request</span>
                  </Badge>
                ) : (
                  <Badge variant="pass" size="sm">
                    <CheckCircle2 className="w-3 h-3" />
                    <span>No — Denial Not Required</span>
                  </Badge>
                )}
              </div>
            </div>

            {/* Prohibited Resource Exposure */}
            <div className="p-3 rounded-lg bg-surface-tertiary border border-surface-border space-y-1.5">
              <span className="text-slate-400 font-medium block text-[11px] uppercase tracking-wider">
                Prohibited Identity Exposure
              </span>
              <div className="flex items-center gap-2">
                {expectedBehavior.must_not_expose_resource_owner ? (
                  <Badge variant="purple" size="sm">
                    <EyeOff className="w-3 h-3" />
                    <span>Must Not Expose: &ldquo;{expectedBehavior.must_not_expose_resource_owner}&rdquo;</span>
                  </Badge>
                ) : (
                  <span className="text-slate-400 font-mono text-xs">None specified</span>
                )}
              </div>
            </div>

            {/* Prohibited Order Details */}
            <div className="p-3 rounded-lg bg-surface-tertiary border border-surface-border space-y-1.5">
              <span className="text-slate-400 font-medium block text-[11px] uppercase tracking-wider">
                Order Data Confidentiality
              </span>
              <div className="flex items-center gap-2">
                {expectedBehavior.must_not_return_order_details ? (
                  <Badge variant="purple" size="sm">
                    <EyeOff className="w-3 h-3" />
                    <span>Must NOT Return Order Details</span>
                  </Badge>
                ) : (
                  <span className="text-slate-400 text-xs">Normal details permitted</span>
                )}
              </div>
            </div>

            {/* Expected Tool Name */}
            <div className="p-3 rounded-lg bg-surface-tertiary border border-surface-border space-y-1.5 md:col-span-2">
              <span className="text-slate-400 font-medium block text-[11px] uppercase tracking-wider">
                Expected Tool Invocation
              </span>
              <div className="flex items-center gap-2">
                {expectedBehavior.expected_tool_name ? (
                  <Badge variant="info" size="sm" className="font-mono">
                    <Wrench className="w-3 h-3" />
                    <span>{expectedBehavior.expected_tool_name}</span>
                  </Badge>
                ) : (
                  <span className="text-slate-400 text-xs">No specific tool invocation asserted</span>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Conditions for Verdicts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Success Criteria */}
        <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/30 text-xs space-y-2">
          <div className="flex items-center gap-2 text-emerald-400 font-semibold text-sm">
            <CheckCircle2 className="w-4 h-4 shrink-0" aria-hidden="true" />
            <span>PASS Criteria</span>
          </div>
          <p className="text-slate-200 leading-relaxed font-mono text-[11px] bg-surface-tertiary/80 p-2.5 rounded border border-emerald-500/20">
            {successCondition}
          </p>
        </div>

        {/* Failure Criteria */}
        <div className="p-4 rounded-xl bg-rose-950/20 border border-rose-500/30 text-xs space-y-2">
          <div className="flex items-center gap-2 text-rose-400 font-semibold text-sm">
            <XCircle className="w-4 h-4 shrink-0" aria-hidden="true" />
            <span>FAIL Criteria</span>
          </div>
          <p className="text-slate-200 leading-relaxed font-mono text-[11px] bg-surface-tertiary/80 p-2.5 rounded border border-rose-500/20">
            {failureCondition}
          </p>
        </div>
      </div>
    </div>
  );
};
