import React from 'react';
import { BookOpen, ExternalLink, Code2, ShieldAlert, Cpu } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { API_CONFIG } from '@/api/config';

export const DocsPlaceholder: React.FC = () => {
  const resources = [
    {
      title: 'FastAPI Interactive Swagger Docs',
      desc: 'Interactive OpenAPI specification to test all scenario, run, results, trace, and export endpoints directly.',
      url: `${API_CONFIG.baseUrl}/docs`,
      icon: Code2,
    },
    {
      title: 'ReDoc API Specification',
      desc: 'Clean, structured three-panel API documentation with complete request/response schemas.',
      url: `${API_CONFIG.baseUrl}/redoc`,
      icon: BookOpen,
    },
    {
      title: 'OpenAPI JSON Schema',
      desc: 'Machine-readable OpenAPI 3.1 specification schema for code generation and CI/CD validation.',
      url: `${API_CONFIG.baseUrl}/openapi.json`,
      icon: Cpu,
    },
    {
      title: 'AgentShield GitHub Repository',
      desc: 'Full source code, implementation PRD, test suites, threat models, and architectural docs.',
      url: 'https://github.com/OwaisKhan08093/AgentShield',
      icon: ExternalLink,
    },
  ];

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-brand-blue" aria-hidden="true" />
              <CardTitle>API & Documentation Reference</CardTitle>
            </div>
            <Badge variant="info" size="sm">
              Live Documentation Links
            </Badge>
          </div>
          <CardDescription>
            Explore the live FastAPI backend contracts, schema definitions, and threat models.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {resources.map((res) => {
              const Icon = res.icon;
              return (
                <a
                  key={res.title}
                  href={res.url}
                  target="_blank"
                  rel="noreferrer"
                  className="p-4 rounded-xl bg-surface-elevated border border-surface-border hover:border-brand-blue/50 transition-colors flex items-start gap-3.5 group block"
                >
                  <div className="w-9 h-9 rounded-lg bg-surface flex items-center justify-center text-brand-blue shrink-0 border border-surface-border group-hover:bg-brand-blue/10 transition-colors">
                    <Icon className="w-4 h-4" />
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center gap-1.5">
                      <span className="text-sm font-semibold text-slate-100 group-hover:text-white transition-colors">
                        {res.title}
                      </span>
                      <ExternalLink className="w-3 h-3 text-slate-500 group-hover:text-slate-300" />
                    </div>
                    <p className="text-xs text-slate-400 leading-relaxed">{res.desc}</p>
                  </div>
                </a>
              );
            })}
          </div>

          <div className="p-4 rounded-xl bg-surface-elevated/50 border border-surface-border text-xs text-slate-400 space-y-2">
            <h4 className="font-semibold text-slate-200 flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-amber-400" />
              <span>Scope & Security Boundary Notice</span>
            </h4>
            <p className="leading-relaxed">
              AgentShield evaluates defense-in-depth posture using a deterministic Reference Agent against synthetic customer
              and order records. Passing synthetic benchmark scenarios does not certify that an AI agent is universally immune
              to unrestricted real-world attacks.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
