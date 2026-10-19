import React from 'react';
import { NavLink } from 'react-router-dom';
import { Shield, LayoutDashboard, FileCode, PlayCircle, BookOpen, ExternalLink } from 'lucide-react';
import { cn } from '@/utils/cn';

interface SidebarProps {
  onCloseMobile?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ onCloseMobile }) => {
  const navItems = [
    {
      to: '/',
      label: 'Overview',
      icon: LayoutDashboard,
      description: 'System summary & evaluation pipeline',
    },
    {
      to: '/scenarios',
      label: 'Scenarios',
      icon: FileCode,
      description: '16 canonical security benchmarks',
    },
    {
      to: '/runs',
      label: 'Evaluation Runs',
      icon: PlayCircle,
      description: 'Execution history, results & traces',
    },
    {
      to: '/docs',
      label: 'API & Documentation',
      icon: BookOpen,
      description: 'FastAPI schemas & threat models',
    },
  ];

  return (
    <aside className="w-64 h-full bg-surface border-r border-surface-border flex flex-col justify-between shrink-0 select-none">
      <div>
        {/* Brand Header */}
        <div className="p-5 border-b border-surface-border/60">
          <NavLink to="/" className="flex items-center gap-3 group" onClick={onCloseMobile}>
            <div className="w-9 h-9 rounded-lg bg-brand-blue/10 border border-brand-blue/30 flex items-center justify-center text-brand-blue group-hover:bg-brand-blue/20 transition-colors">
              <Shield className="w-5 h-5 text-brand-blue" aria-hidden="true" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="font-bold text-sm tracking-tight text-slate-100">AgentShield</span>
                <span className="text-[10px] font-mono font-medium px-1.5 py-0.2 bg-brand-blue/10 text-brand-blue border border-brand-blue/20 rounded">
                  v1.0
                </span>
              </div>
              <p className="text-[11px] text-slate-400 font-normal">Security Evaluation Platform</p>
            </div>
          </NavLink>
        </div>

        {/* Navigation Items */}
        <nav className="p-3 space-y-1">
          <div className="px-3 py-2 text-[10px] font-semibold tracking-wider uppercase text-slate-500">
            Platform Navigation
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                onClick={onCloseMobile}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 px-3 py-2.5 rounded-lg text-xs font-medium transition-all group relative',
                    isActive
                      ? 'bg-surface-elevated text-brand-blue border border-surface-border font-semibold shadow-sm'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-surface-hover'
                  )
                }
              >
                {({ isActive }) => (
                  <>
                    <Icon
                      className={cn(
                        'w-4 h-4 shrink-0 transition-colors',
                        isActive ? 'text-brand-blue' : 'text-slate-400 group-hover:text-slate-200'
                      )}
                      aria-hidden="true"
                    />
                    <div className="flex-1 truncate">
                      <span className="block truncate">{item.label}</span>
                    </div>
                    {isActive && (
                      <span className="w-1.5 h-1.5 rounded-full bg-brand-blue shadow-sm shadow-blue-500/50" />
                    )}
                  </>
                )}
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Footer / Context Notice */}
      <div className="p-4 border-t border-surface-border/60 bg-surface/50 space-y-3">
        <div className="p-2.5 rounded-lg bg-surface-elevated border border-surface-border text-[11px] space-y-1">
          <div className="flex items-center gap-1.5 text-slate-300 font-medium">
            <span className="w-2 h-2 rounded-full bg-brand-blue animate-pulse" />
            <span>Target Agent</span>
          </div>
          <p className="text-[10px] text-slate-400 leading-snug">
            Deterministic Reference Agent with synthetic mock tools. No external LLM token costs.
          </p>
        </div>

        <a
          href="https://github.com/OwaisKhan08093/AgentShield"
          target="_blank"
          rel="noreferrer"
          className="flex items-center justify-between text-[11px] text-slate-400 hover:text-slate-200 px-2 py-1 rounded transition-colors group"
        >
          <span>Repository</span>
          <ExternalLink className="w-3 h-3 text-slate-500 group-hover:text-slate-300" aria-hidden="true" />
        </a>
      </div>
    </aside>
  );
};
