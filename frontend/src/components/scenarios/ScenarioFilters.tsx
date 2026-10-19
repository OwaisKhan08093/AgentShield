import React from 'react';
import { Search, X, Filter, RotateCcw } from 'lucide-react';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { formatCategory } from '@/components/ui/StatusBadge';

interface ScenarioFiltersProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
  selectedCategory: string;
  onCategoryChange: (category: string) => void;
  selectedRisk: string;
  onRiskChange: (risk: string) => void;
  onResetFilters: () => void;
  totalCount: number;
  filteredCount: number;
  availableCategories: string[];
  availableRisks: string[];
}

export const ScenarioFilters: React.FC<ScenarioFiltersProps> = ({
  searchQuery,
  onSearchChange,
  selectedCategory,
  onCategoryChange,
  selectedRisk,
  onRiskChange,
  onResetFilters,
  totalCount,
  filteredCount,
  availableCategories,
  availableRisks,
}) => {
  const isFiltered = searchQuery.trim() !== '' || selectedCategory !== '' || selectedRisk !== '';

  const categoryOptions = [
    { value: '', label: 'All Categories' },
    ...availableCategories.map((cat) => ({
      value: cat,
      label: formatCategory(cat),
    })),
  ];

  const riskOptions = [
    { value: '', label: 'All Risk Levels' },
    ...availableRisks.map((risk) => ({
      value: risk,
      label: risk.toUpperCase(),
    })),
  ];

  return (
    <div className="space-y-3 p-4 rounded-xl bg-surface border border-surface-border">
      <div className="flex flex-col md:flex-row items-stretch md:items-center gap-3">
        {/* Text Search Field */}
        <div className="flex-1 relative">
          <Input
            id="scenario-search-input"
            aria-label="Search scenarios"
            placeholder="Search scenarios by ID, name, description, category, or objective..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            leftIcon={<Search className="w-4 h-4" aria-hidden="true" />}
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => onSearchChange('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200 transition-colors"
              aria-label="Clear search input"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        {/* Category Select Filter */}
        <div className="w-full md:w-56">
          <Select
            id="scenario-category-filter"
            aria-label="Filter by scenario category"
            value={selectedCategory}
            onChange={(e) => onCategoryChange(e.target.value)}
            options={categoryOptions}
          />
        </div>

        {/* Risk Level Select Filter */}
        <div className="w-full md:w-48">
          <Select
            id="scenario-risk-filter"
            aria-label="Filter by risk level"
            value={selectedRisk}
            onChange={(e) => onRiskChange(e.target.value)}
            options={riskOptions}
          />
        </div>

        {/* Reset Action Button */}
        {isFiltered && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onResetFilters}
            leftIcon={<RotateCcw className="w-3.5 h-3.5" />}
            className="text-xs shrink-0 text-slate-300 hover:text-white"
          >
            Clear Filters
          </Button>
        )}
      </div>

      {/* Filter Status Summary & Active Badges */}
      <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-surface-border/50 text-xs">
        <div className="flex items-center gap-2 text-slate-400">
          <Filter className="w-3.5 h-3.5 text-slate-500" aria-hidden="true" />
          <span>
            Showing <strong className="text-slate-200">{filteredCount}</strong> of{' '}
            <strong className="text-slate-200">{totalCount}</strong> scenarios
          </span>
        </div>

        {isFiltered && (
          <div className="flex flex-wrap items-center gap-1.5">
            {searchQuery && (
              <Badge variant="info" size="sm" className="gap-1 text-[11px]">
                <span>Query: &ldquo;{searchQuery}&rdquo;</span>
                <button
                  type="button"
                  onClick={() => onSearchChange('')}
                  aria-label="Remove search query filter"
                  className="hover:text-white ml-0.5"
                >
                  <X className="w-3 h-3" />
                </button>
              </Badge>
            )}
            {selectedCategory && (
              <Badge variant="purple" size="sm" className="gap-1 text-[11px]">
                <span>Category: {formatCategory(selectedCategory)}</span>
                <button
                  type="button"
                  onClick={() => onCategoryChange('')}
                  aria-label="Remove category filter"
                  className="hover:text-white ml-0.5"
                >
                  <X className="w-3 h-3" />
                </button>
              </Badge>
            )}
            {selectedRisk && (
              <Badge variant="warning" size="sm" className="gap-1 text-[11px]">
                <span>Risk: {selectedRisk.toUpperCase()}</span>
                <button
                  type="button"
                  onClick={() => onRiskChange('')}
                  aria-label="Remove risk level filter"
                  className="hover:text-white ml-0.5"
                >
                  <X className="w-3 h-3" />
                </button>
              </Badge>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
