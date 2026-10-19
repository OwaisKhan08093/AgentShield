import React from 'react';
import { CheckCircle2, XCircle, AlertTriangle, MinusCircle, ShieldAlert, ShieldCheck, Shield } from 'lucide-react';
import { Badge } from './Badge';
import type { EvaluationOutcome, RiskLevel } from '@/api/types';

interface OutcomeBadgeProps {
  outcome: EvaluationOutcome;
  size?: 'sm' | 'md';
  className?: string;
}

export const OutcomeBadge: React.FC<OutcomeBadgeProps> = ({ outcome, size = 'md', className }) => {
  switch (outcome.toLowerCase()) {
    case 'pass':
      return (
        <Badge variant="pass" size={size} className={className} aria-label="Outcome: PASS (Security assertions satisfied)">
          <CheckCircle2 className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
          <span>PASS</span>
        </Badge>
      );
    case 'fail':
      return (
        <Badge variant="fail" size={size} className={className} aria-label="Outcome: FAIL (Security assertion failed)">
          <XCircle className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
          <span>FAIL</span>
        </Badge>
      );
    case 'error':
      return (
        <Badge variant="error" size={size} className={className} aria-label="Outcome: ERROR (Execution or unhandled exception)">
          <AlertTriangle className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
          <span>ERROR</span>
        </Badge>
      );
    case 'not_run':
    default:
      return (
        <Badge variant="notrun" size={size} className={className} aria-label="Outcome: NOT RUN (Scenario was not executed)">
          <MinusCircle className="w-3.5 h-3.5 shrink-0" aria-hidden="true" />
          <span>NOT RUN</span>
        </Badge>
      );
  }
};

interface SeverityBadgeProps {
  severity: RiskLevel | string;
  size?: 'sm' | 'md';
  className?: string;
}

export const SeverityBadge: React.FC<SeverityBadgeProps> = ({ severity, size = 'sm', className }) => {
  const norm = severity.toLowerCase();
  switch (norm) {
    case 'critical':
      return (
        <Badge variant="fail" size={size} className={className} aria-label="Risk Level: Critical">
          <ShieldAlert className="w-3 h-3 shrink-0" aria-hidden="true" />
          <span>CRITICAL</span>
        </Badge>
      );
    case 'high':
      return (
        <Badge variant="error" size={size} className={className} aria-label="Risk Level: High">
          <ShieldAlert className="w-3 h-3 shrink-0" aria-hidden="true" />
          <span>HIGH</span>
        </Badge>
      );
    case 'medium':
      return (
        <Badge variant="warning" size={size} className={className} aria-label="Risk Level: Medium">
          <Shield className="w-3 h-3 shrink-0" aria-hidden="true" />
          <span>MEDIUM</span>
        </Badge>
      );
    case 'low':
      return (
        <Badge variant="info" size={size} className={className} aria-label="Risk Level: Low">
          <ShieldCheck className="w-3 h-3 shrink-0" aria-hidden="true" />
          <span>LOW</span>
        </Badge>
      );
    case 'informational':
    default:
      return (
        <Badge variant="default" size={size} className={className} aria-label="Risk Level: Informational">
          <Shield className="w-3 h-3 shrink-0" aria-hidden="true" />
          <span>INFO</span>
        </Badge>
      );
  }
};
