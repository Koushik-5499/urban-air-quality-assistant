import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ThemeProvider } from '../context/ThemeContext';
import { LocationProvider } from '../context/LocationContext';
import { HealthRecommendation } from '../components/dashboard/HealthRecommendation';
import { AQIOverviewCard } from '../components/dashboard/AQIOverviewCard';
import { PollutantCard } from '../components/dashboard/PollutantCard';
import { WeatherCard } from '../components/dashboard/WeatherCard';
import { AssistantContextPanel } from '../components/assistant/AssistantContextPanel';
import { AssistantProfileHeader } from '../components/assistant/AssistantProfileHeader';
import { ChatMessageBubble } from '../components/assistant/ChatMessageBubble';
import { ChatInput } from '../components/assistant/ChatInput';
import { ChatSuggestedQuestions } from '../components/assistant/ChatSuggestedQuestions';
import { ClearChatModal } from '../components/assistant/ClearChatModal';
import { TypingIndicator } from '../components/assistant/TypingIndicator';
import { AlertCard } from '../components/alerts/AlertCard';
import { AlertSeverityBadge } from '../components/alerts/AlertSeverityBadge';
import { AlertSummaryCards } from '../components/alerts/AlertSummaryCards';
import { AlertEmptyState } from '../components/alerts/AlertEmptyState';
import { LocationCard } from '../components/locations/LocationCard';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { DataProvenanceBadge } from '../components/common/DataProvenanceBadge';
import { Navbar } from '../components/layout/Navbar';
import { Footer } from '../components/layout/Footer';
import { NotFoundPage } from '../pages/NotFoundPage';
import { DASHBOARD_DATA } from '../data/dashboardData';
import { SUGGESTED_QUESTIONS } from '../services/assistantEngine';
import type { AirAlert } from '../types/alerts';
import type { ChatMessage } from '../types/assistant';

describe('UI Components Render & Accessibility Verification', () => {
  const delhi = DASHBOARD_DATA['delhi'];
  const coimbatore = DASHBOARD_DATA['coimbatore'];

  it('renders Dashboard cards (AQIOverviewCard, PollutantCard, WeatherCard, HealthRecommendation)', () => {
    render(
      <div>
        <AQIOverviewCard data={delhi} />
        {delhi.pollutants.map((p) => (
          <PollutantCard key={p.id} pollutant={p} />
        ))}
        <WeatherCard weather={delhi.weather} locationName={delhi.location.city} />
        <HealthRecommendation category={delhi.category} aqi={delhi.aqi} />
      </div>
    );

    expect(screen.getByText(/Atmospheric Weather/i)).toBeTruthy();
    expect(screen.getByText(/Health Guidance & Precautions/i)).toBeTruthy();
    expect(screen.getByText(/Winter Smog & Family Inversion Protocol/i)).toBeTruthy();

    // Exercise household profile controls (children/asthma/outdoor worker checkboxes + commute/heating selects)
    fireEvent.click(screen.getByLabelText(/Asthma/i));
    fireEvent.click(screen.getByLabelText(/Outdoor Worker/i));
    fireEvent.change(screen.getByLabelText(/Commute/i), { target: { value: 'public_transit' } });
    fireEvent.change(screen.getByLabelText(/Heating/i), { target: { value: 'biomass' } });
    expect(screen.getByText(/3\.6 kg CO₂\/evening avoided/i)).toBeTruthy();
  });

  it('renders Assistant components (ContextPanel, Header, Bubbles, Input, SuggestedQuestions, ClearModal, Typing)', () => {
    const onSend = vi.fn();
    const onSelect = vi.fn();
    const onClear = vi.fn();
    const onClose = vi.fn();
    const onConfirm = vi.fn();

    const msgAssistant: ChatMessage = {
      id: 'm1',
      sender: 'assistant',
      text: 'Avoid dawn smog between **6 AM and 9 AM**.\n• Use **N95**\n• Run HEPA',
      timestamp: '08:00 AM',
      provenance: 'gemini',
      cityContext: { city: 'Delhi', aqi: delhi.aqi, category: delhi.category },
      explainability: {
        priority: 'Critical Health Alert',
        targetGroup: 'Families & sensitive groups',
        reason: 'Thermal inversion peaks',
        supportingSource: 'CPCB & WHO',
      },
    };
    const msgUser: ChatMessage = {
      id: 'm2',
      sender: 'user',
      text: 'Is it safe outside?',
      timestamp: '08:01 AM',
    };
    const msgSys: ChatMessage = {
      id: 'm3',
      sender: 'system',
      text: 'City switched',
      timestamp: '08:02 AM',
    };

    render(
      <div>
        <AssistantContextPanel cityData={delhi} />
        <AssistantProfileHeader cityData={delhi} messageCount={3} onClearChat={onClear} />
        <ChatMessageBubble message={msgAssistant} />
        <ChatMessageBubble message={msgUser} />
        <ChatMessageBubble message={msgSys} />
        <ChatSuggestedQuestions questions={SUGGESTED_QUESTIONS} onSelectQuestion={onSelect} />
        <ChatInput onSendMessage={onSend} />
        <TypingIndicator />
        <ClearChatModal isOpen={true} onClose={onClose} onConfirm={onConfirm} />
      </div>
    );

    const textarea = screen.getByLabelText(/Message input for AI Health Assistant/i);
    fireEvent.change(textarea, { target: { value: 'Winter smog advice' } });
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false });
    expect(onSend).toHaveBeenCalledWith('Winter smog advice');

    const suggestedBtn = screen.getByText(SUGGESTED_QUESTIONS[0].question);
    fireEvent.click(suggestedBtn);
    expect(onSelect).toHaveBeenCalled();

    const whyBtn = screen.getByRole('button', { name: /Why this advice/i });
    fireEvent.click(whyBtn);
    expect(screen.getByText(/Thermal inversion peaks/i)).toBeTruthy();

    fireEvent.keyDown(window, { key: 'Escape' });
    expect(onClose).toHaveBeenCalled();
  });

  it('renders Alerts, Locations, Common, Layout, and NotFoundPage components', () => {
    const sampleAlert: AirAlert = {
      id: 'alert-1',
      cityId: 'delhi',
      city: 'Delhi',
      state: 'Delhi',
      country: 'India',
      station: 'Anand Vihar',
      aqi: 320,
      category: 'Hazardous',
      severity: 'severe',
      title: 'Severe Smog Warning',
      description: 'Thermal inversion detected',
      recommendedAction: 'Stay indoors with HEPA filter',
      dominantPollutant: 'PM2.5',
      timestamp: new Date().toISOString(),
      dateFormatted: 'Today, 07:00 AM',
      isRead: false,
      isDismissed: false,
      isSimulated: true,
    };

    render(
      <MemoryRouter>
        <ThemeProvider>
          <LocationProvider>
            <Navbar
              isSidebarCollapsed={false}
              onToggleSidebarCollapse={vi.fn()}
              onOpenMobileSidebar={vi.fn()}
            />
            <AlertSummaryCards
              totalAlerts={4}
              unreadAlerts={2}
              criticalAlerts={1}
              monitoredCitiesCount={5}
              totalCitiesCount={10}
            />
            <AlertSeverityBadge severity="severe" />
            <AlertSeverityBadge severity="warning" />
            <AlertSeverityBadge severity="info" />
            <AlertCard
              alert={sampleAlert}
              onViewDetails={vi.fn()}
              onToggleRead={vi.fn()}
              onDismiss={vi.fn()}
            />
            <AlertEmptyState onResetFilters={vi.fn()} />
            <LocationCard
              cityData={coimbatore}
              isSelectedForDashboard={false}
              isCompared={false}
              canCompare={true}
              onViewDetails={vi.fn()}
              onSelectForDashboard={vi.fn()}
              onToggleCompare={vi.fn()}
            />
            <LoadingSpinner label="Loading telemetry" />
            <DataProvenanceBadge forceProvenance="demo" />
            <DataProvenanceBadge forceProvenance="live" />
            <NotFoundPage />
            <Footer />
          </LocationProvider>
        </ThemeProvider>
      </MemoryRouter>
    );

    expect(screen.getByText(/Severe Smog Warning/i)).toBeTruthy();
    expect(screen.getByText(/Page Not Found/i)).toBeTruthy();
  });
});
