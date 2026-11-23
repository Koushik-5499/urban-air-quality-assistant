import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { axe } from 'vitest-axe';
import { DataProvenanceBadge } from '../components/common/DataProvenanceBadge';
import { HealthRecommendation } from '../components/dashboard/HealthRecommendation';
import { ChatMessageBubble } from '../components/assistant/ChatMessageBubble';
import { LocationProvider } from '../context/LocationContext';
import type { ChatMessage } from '../types/assistant';

describe('Component & Accessibility Tests (WCAG 2.1 AA)', () => {
  it('DataProvenanceBadge renders demo provenance and passes axe audit', async () => {
    const { container } = render(
      <LocationProvider>
        <DataProvenanceBadge forceProvenance="demo" />
      </LocationProvider>
    );

    expect(screen.getByText(/Demo data/i)).toBeInTheDocument();
    const results = await axe(container);
    expect(results.violations).toEqual([]);
  });

  it('DataProvenanceBadge renders live provenance and passes axe audit', async () => {
    const { container } = render(
      <LocationProvider>
        <DataProvenanceBadge forceProvenance="live" />
      </LocationProvider>
    );

    expect(screen.getByText(/Live CPCB data/i)).toBeInTheDocument();
    const results = await axe(container);
    expect(results.violations).toEqual([]);
  });

  it('HealthRecommendation renders explainability accordion and passes axe audit', async () => {
    const { container } = render(
      <HealthRecommendation aqi={225} category="Very Unhealthy" />
    );

    // Initial check
    expect(screen.getByText(/Health Guidance & Precautions/i)).toBeInTheDocument();
    const toggleButton = screen.getByRole('button', { name: /Why this advice\?/i });
    expect(toggleButton).toHaveAttribute('aria-expanded', 'false');

    // Toggle expand
    fireEvent.click(toggleButton);
    expect(toggleButton).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByText(/Supporting Standards:/i)).toBeInTheDocument();

    // Verify accessibility with axe
    const results = await axe(container);
    expect(results.violations).toEqual([]);
  });

  it('ChatMessageBubble renders assistant message with provenance and explainability', async () => {
    const testMessage: ChatMessage = {
      id: 'msg-test-1',
      sender: 'assistant',
      text: 'Ambient PM2.5 levels are elevated. Please reschedule intense outdoor exercise to midday.',
      timestamp: '10:30 AM',
      provenance: 'offline_rules',
      explainability: {
        priority: 'High Priority Alert',
        targetGroup: 'Pediatric and asthma cohorts',
        reason: 'Diurnal thermal inversion traps particulates near ground level.',
        supportingSource: 'CPCB Guidelines & WHO Standards',
      },
    };

    const { container } = render(<ChatMessageBubble message={testMessage} />);

    expect(screen.getByText(/Offline guidance \(built-in rules\)/i)).toBeInTheDocument();
    const explainButton = screen.getByRole('button', { name: /Why this advice\?/i });
    expect(explainButton).toHaveAttribute('aria-expanded', 'false');

    fireEvent.click(explainButton);
    expect(explainButton).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByText(/Diurnal thermal inversion/i)).toBeInTheDocument();

    const results = await axe(container);
    expect(results.violations).toEqual([]);
  });
});
