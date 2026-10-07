import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Navbar } from '../components/Navbar';
import { AuthProvider } from '../context/AuthContext';

describe('Navbar Component', () => {
  it('renders application title, subtitle, and tabs', () => {
    const handleSelectTab = vi.fn();
    render(
      <AuthProvider>
        <Navbar activeTab="dashboard" setActiveTab={handleSelectTab} pendingReviewCount={3} />
      </AuthProvider>
    );

    expect(screen.getByText('Citation & Faithfulness Auditor')).toBeInTheDocument();
    expect(screen.getByText('Alan Vo | AI & Machine Learning')).toBeInTheDocument();
    expect(screen.getByText('Audit Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Ingest & Audit')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument(); // Counter badge
  });

  it('triggers tab selection when tab button is clicked', () => {
    const handleSelectTab = vi.fn();
    render(
      <AuthProvider>
        <Navbar activeTab="dashboard" setActiveTab={handleSelectTab} />
      </AuthProvider>
    );

    const ingestBtn = screen.getByText('Ingest & Audit');
    fireEvent.click(ingestBtn);
    expect(handleSelectTab).toHaveBeenCalledWith('import');
  });
});
