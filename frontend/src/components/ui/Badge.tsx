import React from 'react';
import { cn } from '@/utils/cn';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'outline' | 'pass' | 'fail' | 'error' | 'notrun' | 'info' | 'warning' | 'purple';
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({
  className,
  variant = 'default',
  size = 'md',
  children,
  ...props
}) => {
  const baseStyles = 'inline-flex items-center font-medium rounded-full tracking-wide transition-colors select-none';

  const variants = {
    default: 'bg-surface-elevated text-slate-300 border border-surface-border',
    outline: 'bg-transparent text-slate-300 border border-surface-border-subtle',
    pass: 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/25',
    fail: 'bg-rose-500/10 text-rose-400 border border-rose-500/25',
    error: 'bg-amber-500/10 text-amber-400 border border-amber-500/25',
    notrun: 'bg-slate-500/10 text-slate-400 border border-slate-500/25',
    info: 'bg-blue-500/10 text-blue-400 border border-blue-500/25',
    warning: 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/25',
    purple: 'bg-purple-500/10 text-purple-400 border border-purple-500/25',
  };

  const sizes = {
    sm: 'text-[11px] px-2 py-0.5 gap-1',
    md: 'text-xs px-2.5 py-1 gap-1.5',
  };

  return (
    <span className={cn(baseStyles, variants[variant], sizes[size], className)} {...props}>
      {children}
    </span>
  );
};
