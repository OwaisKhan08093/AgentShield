import React from 'react';
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  MinusCircle,
  ShieldAlert,
  ShieldCheck,
  Shield,
  Tag,
} from 'lucide-react';
import { Badge } from './Badge';
import type { EvaluationOutcome, RiskLevel, ScenarioCategory } from '@/api/types';

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

export const formatCategory = (category: string): string => {
  switch (category.toLowerCase()) {
    case 'benign_task':
      return 'Benign Task';
    case 'unauthorized_access':
      return 'Unauthorized Access';
    case 'approval_bypass':
      return 'Approval Bypass';
    case 'data_exposure':
      return 'Data Exposure';
    case 'malformed_input':
      return 'Malformed Input';
    case 'direct_injection':
      return 'Direct Injection';
    case 'indirect_injection':
      return 'Indirect Injection';
    default:
      return category.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
  }
};

interface CategoryBadgeProps {
  category: ScenarioCategory | string;
  size?: 'sm' | 'md';
  className?: string;
}

export const CategoryBadge: React.FC<CategoryBadgeProps> = ({ category, size = 'sm', className }) => {
  const norm = category.toLowerCase();
  let variant: 'default' | 'info' | 'purple' | 'warning' | 'fail' = 'default';

  if (norm === 'benign_task') {
    variant = 'info';
  } else if (norm === 'unauthorized_access' || norm === 'data_exposure') {
    variant = 'purple';
  } else if (norm === 'approval_bypass' || norm === 'malformed_input') {
    variant = 'warning';
  } else if (norm.includes('injection')) {
    variant = 'fail';
  }

  return (
    <Badge variant={variant} size={size} className={className} aria-label={`Category: ${formatCategory(category)}`}>
      <Tag className="w-3 h-3 shrink-0" aria-hidden="true" />
      <span>{formatCategory(category)}</span>
    </Badge>
  );
};
