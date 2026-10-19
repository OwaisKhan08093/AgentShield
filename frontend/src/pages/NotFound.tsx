import React from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle, Home, ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/Button';

export const NotFound: React.FC = () => {
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center text-center px-4">
      <div className="w-16 h-16 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 mb-6 shadow-inner">
        <AlertTriangle className="w-8 h-8" />
      </div>

      <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-medium bg-surface-tertiary border border-border-default text-text-muted mb-4">
        <span>HTTP 404</span>
        <span>•</span>
        <span>Route Not Found</span>
      </div>

      <h1 className="text-3xl font-bold text-text-primary tracking-tight mb-2">
        Page Not Found
      </h1>
      <p className="text-text-muted max-w-md text-sm mb-8 leading-relaxed">
        The route you requested does not exist in the AgentShield console or may have been moved.
      </p>

      <div className="flex flex-wrap items-center justify-center gap-3">
        <Button variant="secondary" onClick={() => window.history.back()} icon={<ArrowLeft className="w-4 h-4" />}>
          Go Back
        </Button>
        <Link to="/">
          <Button variant="primary" icon={<Home className="w-4 h-4" />}>
            Return to Overview
          </Button>
        </Link>
      </div>
    </div>
  );
};

export default NotFound;
