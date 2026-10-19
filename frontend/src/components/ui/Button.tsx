import React, { forwardRef } from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '@/utils/cn';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  icon?: React.ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = 'primary',
      size = 'md',
      isLoading = false,
      disabled,
      leftIcon,
      rightIcon,
      icon,
      children,
      ...props
    },
    ref
  ) => {
    const baseStyles =
      'inline-flex items-center justify-center font-medium transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-blue/50 focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:pointer-events-none disabled:opacity-50 select-none';

    const variants = {
      primary:
        'bg-brand-blue text-white hover:bg-blue-600 active:bg-blue-700 shadow-sm shadow-blue-900/20 rounded-lg',
      secondary:
        'bg-surface-elevated text-slate-200 hover:bg-surface-hover hover:text-white border border-surface-border active:bg-surface-border rounded-lg',
      outline:
        'bg-transparent border border-surface-border-subtle text-slate-300 hover:bg-surface-elevated hover:text-white hover:border-slate-400 active:bg-surface-hover rounded-lg',
      ghost:
        'bg-transparent text-slate-400 hover:text-slate-100 hover:bg-surface-elevated active:bg-surface-hover rounded-lg',
      danger:
        'bg-rose-600 text-white hover:bg-rose-700 active:bg-rose-800 shadow-sm shadow-rose-950/20 rounded-lg',
    };

    const sizes = {
      sm: 'text-xs px-2.5 py-1.5 gap-1.5',
      md: 'text-sm px-4 py-2 gap-2',
      lg: 'text-base px-5 py-2.5 gap-2.5',
    };

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(baseStyles, variants[variant], sizes[size], className)}
        {...props}
      >
        {isLoading && <span className="sr-only">Loading</span>}
        {isLoading ? (
          <Loader2 className="w-4 h-4 animate-spin shrink-0 text-current" aria-hidden="true" />
        ) : (
          icon || leftIcon
        )}
        <span>{children}</span>
        {!isLoading && rightIcon}
      </button>
    );
  }
);

Button.displayName = 'Button';
