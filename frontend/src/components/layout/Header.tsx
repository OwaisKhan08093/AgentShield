import React, { useEffect, useState, useCallback } from 'react';
import { Menu, RefreshCw, CheckCircle2, AlertCircle } from 'lucide-react';
import { apiClient } from '@/api/client';
import { API_CONFIG } from '@/api/config';
import { cn } from '@/utils/cn';

interface HeaderProps {
  title: string;
  description?: string;
  onToggleMobileMenu: () => void;
}

type BackendStatus = 'checking' | 'online' | 'offline';

export const Header: React.FC<HeaderProps> = ({ title, description, onToggleMobileMenu }) => {
  const [status, setStatus] = useState<BackendStatus>('checking');
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  const checkConnection = useCallback(async () => {
    setStatus('checking');
    try {
      const res = await apiClient.checkHealth();
      if (res && res.status === 'ok') {
        setStatus('online');
      } else {
        setStatus('offline');
      }
    } catch {
      setStatus('offline');
    } finally {
      setLastChecked(new Date());
    }
  }, []);

  useEffect(() => {
    let mounted = true;
    const runCheck = async () => {
      try {
        const res = await apiClient.checkHealth();
        if (mounted) {
          setStatus(res && res.status === 'ok' ? 'online' : 'offline');
          setLastChecked(new Date());
        }
      } catch {
        if (mounted) {
          setStatus('offline');
          setLastChecked(new Date());
        }
      }
    };

    runCheck();
    const interval = setInterval(runCheck, 30000);
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <header className="h-16 border-b border-surface-border bg-surface/80 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-20">
      <div className="flex items-center gap-4">
        <button
          type="button"
          onClick={onToggleMobileMenu}
          className="md:hidden p-2 rounded-lg text-slate-400 hover:text-white hover:bg-surface-elevated focus:outline-none focus:ring-2 focus:ring-brand-blue"
          aria-label="Toggle navigation menu"
        >
          <Menu className="w-5 h-5" aria-hidden="true" />
        </button>

        <div>
          <h1 className="text-base font-semibold text-slate-100 tracking-tight leading-tight">{title}</h1>
          {description && <p className="text-xs text-slate-400 hidden sm:block">{description}</p>}
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* Real Backend Connection Indicator */}
        <button
          type="button"
          onClick={checkConnection}
          title={`Click to re-test connection to ${API_CONFIG.baseUrl}${lastChecked ? ` (Last checked: ${lastChecked.toLocaleTimeString()})` : ''}`}
          className={cn(
            'inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium border transition-all duration-150',
            status === 'online' && 'bg-emerald-500/10 text-emerald-400 border-emerald-500/25 hover:bg-emerald-500/15',
            status === 'offline' && 'bg-rose-500/10 text-rose-400 border-rose-500/25 hover:bg-rose-500/15',
            status === 'checking' && 'bg-amber-500/10 text-amber-400 border-amber-500/25'
          )}
        >
          {status === 'online' && (
            <>
              <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-sm shadow-emerald-500/50" />
              <span>Backend Connected</span>
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" aria-hidden="true" />
            </>
          )}
          {status === 'offline' && (
            <>
              <span className="w-2 h-2 rounded-full bg-rose-500 shadow-sm shadow-rose-500/50" />
              <span>Backend Offline</span>
              <AlertCircle className="w-3.5 h-3.5 text-rose-400 shrink-0" aria-hidden="true" />
            </>
          )}
          {status === 'checking' && (
            <>
              <RefreshCw className="w-3 h-3 text-amber-400 animate-spin shrink-0" aria-hidden="true" />
              <span>Connecting...</span>
            </>
          )}
        </button>
      </div>
    </header>
  );
};
