import React, { useEffect, useState, useMemo, useCallback } from 'react';
import { ShieldCheck, RefreshCw, Layers, ShieldAlert, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { ErrorAlert } from '@/components/ui/ErrorAlert';
import { ScenarioCard } from '@/components/scenarios/ScenarioCard';
import { ScenarioFilters } from '@/components/scenarios/ScenarioFilters';
import { apiClient } from '@/api/client';
import type { ScenarioSummaryResponse } from '@/api/types';

export const Scenarios: React.FC = () => {
  const [scenarios, setScenarios] = useState<ScenarioSummaryResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filter States
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedRisk, setSelectedRisk] = useState('');

  const fetchScenarios = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiClient.listScenarios();
      setScenarios(Array.isArray(data) ? data : []);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to connect to backend';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    let mounted = true;

    const load = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const data = await apiClient.listScenarios();
        if (mounted) {
          setScenarios(Array.isArray(data) ? data : []);
        }
      } catch (err) {
        if (mounted) {
          const message = err instanceof Error ? err.message : 'Failed to connect to backend';
          setError(message);
        }
      } finally {
        if (mounted) {
          setIsLoading(false);
        }
      }
    };

    load();

    return () => {
      mounted = false;
    };
  }, []);

  // Dynamically derive available categories and risk levels from actual data
  const availableCategories = useMemo(() => {
    const set = new Set<string>();
    scenarios.forEach((s) => {
      if (s.category) set.add(s.category);
    });
    return Array.from(set).sort();
  }, [scenarios]);

  const availableRisks = useMemo(() => {
    const priority = ['critical', 'high', 'medium', 'low', 'informational'];
    const present = new Set<string>();
    scenarios.forEach((s) => {
      if (s.risk_level) present.add(s.risk_level.toLowerCase());
    });
    return priority.filter((r) => present.has(r));
  }, [scenarios]);

  // Compute counts by severity
  const riskCounts = useMemo(() => {
    const counts = { critical: 0, high: 0, medium: 0, low: 0, informational: 0 };
    scenarios.forEach((s) => {
      const norm = s.risk_level?.toLowerCase() as keyof typeof counts;
      if (norm && norm in counts) {
        counts[norm]++;
      }
    });
    return counts;
  }, [scenarios]);

  // Composed search and filter logic
  const filteredScenarios = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();

    return scenarios.filter((scenario) => {
      // Category filter match
      if (selectedCategory && scenario.category.toLowerCase() !== selectedCategory.toLowerCase()) {
        return false;
      }

      // Risk filter match
      if (selectedRisk && scenario.risk_level.toLowerCase() !== selectedRisk.toLowerCase()) {
        return false;
      }

      // Text query match across identifier, name, description, objective, tags, and category
      if (q) {
        const idMatch = scenario.scenario_id.toLowerCase().includes(q);
        const nameMatch = scenario.name.toLowerCase().includes(q);
        const descMatch = scenario.description.toLowerCase().includes(q);
        const objMatch = scenario.security_objective.toLowerCase().includes(q);
        const catMatch = scenario.category.toLowerCase().includes(q);
        const tagsMatch = scenario.tags?.some((t) => t.toLowerCase().includes(q)) ?? false;

        if (!idMatch && !nameMatch && !descMatch && !objMatch && !catMatch && !tagsMatch) {
          return false;
        }
      }

      return true;
    });
  }, [scenarios, searchQuery, selectedCategory, selectedRisk]);

  const handleResetFilters = useCallback(() => {
    setSearchQuery('');
    setSelectedCategory('');
    setSelectedRisk('');
  }, []);

  return (
    <div className="space-y-6 pb-12">
      {/* Page Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2.5">
            <ShieldCheck className="w-6 h-6 text-cyan-400" aria-hidden="true" />
            <span>Scenario Catalog & Explorer</span>
          </h1>
          <p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed">
            Deterministic security benchmark suite for evaluating customer-support agents against OWASP LLM vulnerabilities,
            privilege boundaries, and injection attacks.
          </p>
        </div>

        <Button
          variant="secondary"
          size="sm"
          onClick={fetchScenarios}
          isLoading={isLoading}
          leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
          className="self-start sm:self-auto"
        >
          Refresh Catalog
        </Button>
      </div>

      {/* Summary Metrics Bar */}
      {!isLoading && !error && scenarios.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-5 gap-3">
          <div className="p-3 rounded-xl bg-surface border border-surface-border space-y-1">
            <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider block">
              Total Scenarios
            </span>
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-brand-blue" aria-hidden="true" />
              <span className="text-xl font-bold text-slate-100">{scenarios.length}</span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-surface border border-surface-border space-y-1">
            <span className="text-[11px] font-medium text-rose-400 uppercase tracking-wider block">
              Critical Risk
            </span>
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-rose-400" aria-hidden="true" />
              <span className="text-xl font-bold text-rose-300">{riskCounts.critical}</span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-surface border border-surface-border space-y-1">
            <span className="text-[11px] font-medium text-amber-400 uppercase tracking-wider block">
              High Risk
            </span>
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400" aria-hidden="true" />
              <span className="text-xl font-bold text-amber-300">{riskCounts.high}</span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-surface border border-surface-border space-y-1">
            <span className="text-[11px] font-medium text-yellow-400 uppercase tracking-wider block">
              Medium Risk
            </span>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-yellow-400/80" aria-hidden="true" />
              <span className="text-xl font-bold text-yellow-300">{riskCounts.medium}</span>
            </div>
          </div>

          <div className="p-3 rounded-xl bg-surface border border-surface-border space-y-1 col-span-2 sm:col-span-1">
            <span className="text-[11px] font-medium text-blue-400 uppercase tracking-wider block">
              Low / Info
            </span>
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-blue-400/80" aria-hidden="true" />
              <span className="text-xl font-bold text-blue-300">
                {riskCounts.low + riskCounts.informational}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="min-h-[40vh] flex flex-col items-center justify-center space-y-3">
          <LoadingSpinner size="lg" text="Loading canonical security scenarios from backend..." />
        </div>
      )}

      {/* Error State */}
      {!isLoading && error && (
        <ErrorAlert
          title="Failed to Load Scenarios"
          message={error}
          onRetry={fetchScenarios}
        />
      )}

      {/* Empty State when backend returns 0 scenarios */}
      {!isLoading && !error && scenarios.length === 0 && (
        <EmptyState
          title="No Scenarios Available"
          description="The AgentShield scenario registry currently has no scenarios registered."
          action={
            <Button variant="secondary" onClick={fetchScenarios}>
              Retry Connection
            </Button>
          }
        />
      )}

      {/* Loaded State with Search and Cards */}
      {!isLoading && !error && scenarios.length > 0 && (
        <div className="space-y-4">
          {/* Search & Filter Toolbar */}
          <ScenarioFilters
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
            selectedCategory={selectedCategory}
            onCategoryChange={setSelectedCategory}
            selectedRisk={selectedRisk}
            onRiskChange={setSelectedRisk}
            onResetFilters={handleResetFilters}
            totalCount={scenarios.length}
            filteredCount={filteredScenarios.length}
            availableCategories={availableCategories}
            availableRisks={availableRisks}
          />

          {/* Empty Filtered Results State */}
          {filteredScenarios.length === 0 ? (
            <EmptyState
              title="No Matching Scenarios Found"
              description="No scenarios match your active search terms or filter selections. Try clearing your filters or broadening your search query."
              action={
                <Button variant="secondary" onClick={handleResetFilters}>
                  Clear All Filters
                </Button>
              }
            />
          ) : (
            /* Scenario Cards Grid */
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredScenarios.map((scenario) => (
                <ScenarioCard key={scenario.scenario_id} scenario={scenario} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Scenarios;
