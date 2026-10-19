import React from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '@/utils/cn';

export interface LoadingSpinnerProps {
  message?: string;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  message = 'Loading...',
  className,
  size = 'md',
}) => {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  };

  return (
    <div className={cn('flex flex-col items-center justify-center py-10 gap-3 text-slate-400', className)} role="status">
      <Loader2 className={cn('animate-spin text-brand-blue', sizes[size])} aria-hidden="true" />
      {message && <p className="text-xs font-medium text-slate-400 animate-pulse">{message}</p>}
      <span className="sr-only">{message}</span>
    </div>
  );
};
