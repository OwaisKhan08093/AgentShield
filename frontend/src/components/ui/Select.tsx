import React, { forwardRef } from 'react';
import { ChevronDown } from 'lucide-react';
import { cn } from '@/utils/cn';

export interface SelectOption {
  value: string;
  label: string;
}

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  helperText?: string;
  options: SelectOption[];
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, label, error, helperText, options, id, disabled, children, ...props }, ref) => {
    const selectId = id || (label ? `select-${label.toLowerCase().replace(/\s+/g, '-')}` : undefined);

    return (
      <div className="w-full space-y-1.5">
        {label && (
          <label htmlFor={selectId} className="block text-xs font-medium text-slate-300">
            {label}
          </label>
        )}
        <div className="relative flex items-center">
          <select
            ref={ref}
            id={selectId}
            disabled={disabled}
            className={cn(
              'w-full bg-surface-elevated/70 border border-surface-border rounded-lg text-sm text-slate-100',
              'py-2 pl-3 pr-8 transition-colors duration-150 appearance-none cursor-pointer',
              'focus:outline-none focus:ring-2 focus:ring-brand-blue/50 focus:border-brand-blue',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              error && 'border-rose-500 focus:ring-rose-500/50 focus:border-rose-500',
              className
            )}
            {...props}
          >
            {children ||
              options.map((opt) => (
                <option key={opt.value} value={opt.value} className="bg-surface text-slate-100">
                  {opt.label}
                </option>
              ))}
          </select>
          <div className="absolute right-2.5 text-slate-400 pointer-events-none flex items-center justify-center">
            <ChevronDown className="w-4 h-4" aria-hidden="true" />
          </div>
        </div>
        {error && <p className="text-xs text-rose-400">{error}</p>}
        {helperText && !error && <p className="text-xs text-slate-500">{helperText}</p>}
      </div>
    );
  }
);

Select.displayName = 'Select';
