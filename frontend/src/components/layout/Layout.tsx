import React, { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

export interface LayoutProps {
  children?: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();

  // Route-aware header titles
  const getHeaderMeta = () => {
    switch (location.pathname) {
      case '/':
        return {
          title: 'System Overview',
          description: 'AI Agent Security Evaluation Platform baseline and architecture',
        };
      case '/scenarios':
        return {
          title: 'Security Scenarios',
          description: 'Deterministic benchmark catalog covering OWASP LLM attack vectors',
        };
      case '/runs':
        return {
          title: 'Evaluation Runs',
          description: 'Execution history, scenario outcomes, and sanitized traces',
        };
      case '/docs':
        return {
          title: 'API & Documentation',
          description: 'Platform schemas, evaluation assertions, and integration specs',
        };
      default:
        return {
          title: 'AgentShield Platform',
          description: 'Security evaluation and benchmarking',
        };
    }
  };

  const { title, description } = getHeaderMeta();

  return (
    <div className="flex h-screen bg-background text-slate-100 overflow-hidden font-sans">
      {/* Desktop Sidebar */}
      <div className="hidden md:flex md:shrink-0">
        <Sidebar />
      </div>

      {/* Mobile Drawer Backdrop */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm md:hidden"
          onClick={() => setMobileMenuOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Mobile Drawer */}
      <div
        className={`fixed inset-y-0 left-0 z-50 w-64 transform transition-transform duration-200 ease-in-out md:hidden ${
          mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <Sidebar onCloseMobile={() => setMobileMenuOpen(false)} />
      </div>

      {/* Main Content Viewport */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Header
          title={title}
          description={description}
          onToggleMobileMenu={() => setMobileMenuOpen((prev) => !prev)}
        />

        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          <div className="max-w-6xl mx-auto">
            {children ?? <Outlet />}
          </div>
        </main>
      </div>
    </div>
  );
};
