import { describe, it, expect } from 'vitest';
import { render, screen, act } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { Button } from '../components/ui/Button';
import { OutcomeBadge, SeverityBadge } from '../components/ui/StatusBadge';
import { EmptyState } from '../components/ui/EmptyState';
import { ErrorAlert } from '../components/ui/ErrorAlert';
import App from '../App';

describe('Design System Primitives', () => {
  it('renders Button with variants and handles loading state', () => {
    const { rerender } = render(<Button variant="primary">Click Me</Button>);
    const button = screen.getByRole('button', { name: /click me/i });
    expect(button).toBeInTheDocument();
    expect(button).not.toBeDisabled();

    rerender(<Button variant="primary" isLoading>Click Me</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('renders OutcomeBadge for PASS, FAIL, ERROR, and NOT_RUN with both text and color semantics', () => {
    const { rerender } = render(<OutcomeBadge outcome="PASS" />);
    expect(screen.getByText('PASS')).toBeInTheDocument();

    rerender(<OutcomeBadge outcome="FAIL" />);
    expect(screen.getByText('FAIL')).toBeInTheDocument();

    rerender(<OutcomeBadge outcome="ERROR" />);
    expect(screen.getByText('ERROR')).toBeInTheDocument();

    rerender(<OutcomeBadge outcome="NOT_RUN" />);
    expect(screen.getByText('NOT RUN')).toBeInTheDocument();
  });

  it('renders SeverityBadge for all severity levels', () => {
    const { rerender } = render(<SeverityBadge severity="CRITICAL" />);
    expect(screen.getByText('CRITICAL')).toBeInTheDocument();

    rerender(<SeverityBadge severity="HIGH" />);
    expect(screen.getByText('HIGH')).toBeInTheDocument();

    rerender(<SeverityBadge severity="MEDIUM" />);
    expect(screen.getByText('MEDIUM')).toBeInTheDocument();

    rerender(<SeverityBadge severity="LOW" />);
    expect(screen.getByText('LOW')).toBeInTheDocument();

    rerender(<SeverityBadge severity="INFO" />);
    expect(screen.getByText('INFO')).toBeInTheDocument();
  });

  it('renders EmptyState with icon, title, description, and action button', () => {
    render(
      <EmptyState
        title="No Scenarios Found"
        description="Try adjusting your filter criteria."
        action={<Button size="sm">Reset Filter</Button>}
      />
    );
    expect(screen.getByText('No Scenarios Found')).toBeInTheDocument();
    expect(screen.getByText('Try adjusting your filter criteria.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /reset filter/i })).toBeInTheDocument();
  });

  it('renders ErrorAlert with title, message, and retry button', () => {
    render(
      <ErrorAlert
        title="Failed to Load Data"
        message="Backend server did not respond in time."
        onRetry={() => {}}
      />
    );
    expect(screen.getByText('Failed to Load Data')).toBeInTheDocument();
    expect(screen.getByText('Backend server did not respond in time.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });
});

describe('Application Shell and Navigation', () => {
  it('renders Overview page on root path', async () => {
    await act(async () => {
      render(
        <MemoryRouter initialEntries={['/']}>
          <App />
        </MemoryRouter>
      );
    });
    expect(screen.getAllByText(/AI Agent Security Evaluation Platform/i).length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText(/Security evaluation platform for tool-using AI agents/i)).toBeInTheDocument();
  });

  it('renders Scenarios catalog page on /scenarios', async () => {
    await act(async () => {
      render(
        <MemoryRouter initialEntries={['/scenarios']}>
          <App />
        </MemoryRouter>
      );
    });
    expect(screen.getByText(/Scenario Catalog & Explorer/i)).toBeInTheDocument();
  });

  it('renders Runs placeholder page on /runs', async () => {
    await act(async () => {
      render(
        <MemoryRouter initialEntries={['/runs']}>
          <App />
        </MemoryRouter>
      );
    });
    expect(screen.getByText(/Evaluation Runs & Trace Inspector/i)).toBeInTheDocument();
    expect(screen.getByText(/PRD Days 21–22 Milestone/i)).toBeInTheDocument();
  });

  it('renders Documentation placeholder page on /docs', async () => {
    await act(async () => {
      render(
        <MemoryRouter initialEntries={['/docs']}>
          <App />
        </MemoryRouter>
      );
    });
    expect(screen.getByText(/API & Documentation Reference/i)).toBeInTheDocument();
  });

  it('renders 404 page for unknown routes', async () => {
    await act(async () => {
      render(
        <MemoryRouter initialEntries={['/non-existent-route']}>
          <App />
        </MemoryRouter>
      );
    });
    expect(screen.getByText('Page Not Found')).toBeInTheDocument();
    expect(screen.getByText('HTTP 404')).toBeInTheDocument();
  });
});
