import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  RefreshCw,
  Search,
  Activity,
  Layers,
  ChevronLeft,
  ChevronRight,
  Plus,
} from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { ErrorAlert } from '@/components/ui/ErrorAlert';
import { EmptyState } from '@/components/ui/EmptyState';
import { RunHistoryTable } from '@/components/runs/RunHistoryTable';
import { RunCreateModal } from '@/components/runs/RunCreateModal';
import { apiClient } from '@/api/client';
import type { EvaluationRunRecord } from '@/api/types';

export const Runs: React.FC = () => {
  const navigate = useNavigate();

  const [runs, setRuns] = useState<EvaluationRunRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Pagination state
  const [limit] = useState(20);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(false);

  // Search filter
  const [searchQuery, setSearchQuery] = useState('');

  // Modal state
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  const fetchRuns = useCallback(async (currentOffset: number) => {
    setIsLoading(true);
    setError(null);
    try {
      // Fetch current page + 1 extra item to check if next page exists
      const data = await apiClient.listRuns(limit + 1, currentOffset);
      const safeData = Array.isArray(data) ? data : [];
      if (safeData.length > limit) {
        setHasMore(true);
        setRuns(safeData.slice(0, limit));
      } else {
        setHasMore(false);
        setRuns(safeData);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load evaluation runs');
    } finally {
      setIsLoading(false);
    }
  }, [limit]);

  useEffect(() => {
    fetchRuns(offset);
  }, [fetchRuns, offset]);

  const handleRunCreated = (newRunId: string) => {
    setIsCreateModalOpen(false);
    navigate(`/runs/${newRunId}`);
  };

  const handleNextPage = () => {
    if (hasMore) {
      setOffset((prev) => prev + limit);
    }
  };

  const handlePrevPage = () => {
    if (offset > 0) {
      setOffset((prev) => Math.max(0, prev - limit));
    }
  };

  const filteredRuns = (Array.isArray(runs) ? runs : []).filter((r) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      r.run_id.toLowerCase().includes(q) ||
      r.status.toLowerCase().includes(q) ||
      r.overall_outcome.toLowerCase().includes(q)
    );
  });

  const currentPage = Math.floor(offset / limit) + 1;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2">
        <div>
          <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-100 flex items-center gap-2.5">
            <Layers className="w-6 h-6 text-primary" />
            Evaluation Runs & Trace Inspector
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-1">
            Execute security test suites, monitor execution progress, and inspect historical evaluation reports.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="secondary"
            size="sm"
            onClick={() => fetchRuns(offset)}
            disabled={isLoading}
            leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />}
            aria-label="Refresh run list"
          >
            Refresh
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={() => setIsCreateModalOpen(true)}
            leftIcon={<Plus className="w-3.5 h-3.5" />}
            aria-label="Launch new evaluation"
          >
            New Evaluation
          </Button>
        </div>
      </div>

      {/* Search & Status Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-surface p-3.5 rounded-xl border border-surface-border">
        <div className="relative flex-1 max-w-sm">
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search run ID, status, outcome..."
            className="pl-8 text-xs"
            aria-label="Search evaluation runs"
          />
        </div>

        <div className="text-xs text-slate-400 flex items-center gap-2">
          <span>Page {currentPage}</span>
          <span className="text-slate-600">•</span>
          <span>Showing {filteredRuns.length} run{filteredRuns.length === 1 ? '' : 's'}</span>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <ErrorAlert
          message={error}
          onRetry={() => fetchRuns(offset)}
        />
      )}

      {/* Loading Spinner */}
      {isLoading && (
        <div className="py-12 flex justify-center">
          <LoadingSpinner message="Loading evaluation runs from SQLite database..." />
        </div>
      )}

      {/* Run List or Empty State */}
      {!isLoading && !error && (
        <>
          {runs.length === 0 ? (
            <EmptyState
              icon={<Activity className="w-6 h-6 text-primary" />}
              title="No Evaluation Runs Yet"
              description="No security evaluations have been executed. Launch your first evaluation run against the ReferenceAgent to evaluate prompt injection defenses."
              action={
                <Button variant="primary" onClick={() => setIsCreateModalOpen(true)}>
                  Launch Evaluation Run
                </Button>
              }
            />
          ) : filteredRuns.length === 0 ? (
            <EmptyState
              icon={<Search className="w-6 h-6 text-slate-400" />}
              title="No Matching Runs"
              description="No evaluation runs matched your search query. Try clearing the search query."
              action={
                <Button variant="secondary" onClick={() => setSearchQuery('')}>
                  Clear Search
                </Button>
              }
            />
          ) : (
            <>
              <RunHistoryTable runs={filteredRuns} />

              {/* Pagination Controls */}
              <div className="flex items-center justify-between pt-2">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handlePrevPage}
                  disabled={offset === 0 || isLoading}
                  leftIcon={<ChevronLeft className="w-3.5 h-3.5" />}
                  aria-label="Previous page"
                >
                  Previous
                </Button>

                <span className="text-xs text-slate-400">
                  Page {currentPage}
                </span>

                <Button
                  variant="secondary"
                  size="sm"
                  onClick={handleNextPage}
                  disabled={!hasMore || isLoading}
                  rightIcon={<ChevronRight className="w-3.5 h-3.5" />}
                  aria-label="Next page"
                >
                  Next
                </Button>
              </div>
            </>
          )}
        </>
      )}

      {/* Run Creation Modal */}
      <RunCreateModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onRunCreated={handleRunCreated}
      />
    </div>
  );
};
