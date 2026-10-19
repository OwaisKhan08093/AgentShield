import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { cn } from '@/utils/cn';
import { Button } from './Button';

export interface ErrorAlertProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  className?: string;
}

export const ErrorAlert: React.FC<ErrorAlertProps> = ({
  title = 'Connection or Evaluation Error',
  message,
  onRetry,
  className,
}) => {
  return (
    <div
      role="alert"
      className={cn(
        'rounded-xl border border-rose-500/25 bg-rose-500/10 p-4 text-rose-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3',
        className
      )}
    >
      <div className="flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" aria-hidden="true" />
        <div>
          <h4 className="text-sm font-semibold text-rose-300">{title}</h4>
          <p className="text-xs text-rose-300/80 mt-0.5 leading-relaxed">{message}</p>
        </div>
      </div>
      {onRetry && (
        <Button
          variant="outline"
          size="sm"
          onClick={onRetry}
          leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
          className="border-rose-500/30 text-rose-200 hover:bg-rose-500/20 shrink-0"
        >
          Retry
        </Button>
      )}
    </div>
  );
};
