import { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { Bot, MessageSquare, ShieldCheck, AlertTriangle } from 'lucide-react';
import { useLocation } from '../hooks/useLocation';
import { useDocumentTitle } from '../hooks/useDocumentTitle';
import { DataProvenanceBadge } from '../components/common/DataProvenanceBadge';
import { AssistantProfileHeader } from '../components/assistant/AssistantProfileHeader';
import { ChatMessageBubble } from '../components/assistant/ChatMessageBubble';
import { ChatInput } from '../components/assistant/ChatInput';
import { ChatSuggestedQuestions } from '../components/assistant/ChatSuggestedQuestions';
import { TypingIndicator } from '../components/assistant/TypingIndicator';
import { ClearChatModal } from '../components/assistant/ClearChatModal';
import { AssistantContextPanel } from '../components/assistant/AssistantContextPanel';
import {
  generateAssistantResponse,
  SUGGESTED_QUESTIONS,
} from '../services/assistantEngine';
import { healthApi } from '../services/api/healthApi';
import type { ChatMessage } from '../types/assistant';

const STORAGE_KEY_CHAT = 'uaqa_assistant_messages';

const LIFESTYLE_PERSONAS = [
  { id: 'family_with_children', label: '👨‍👩‍👧 Family with Children', desc: 'School commute, pediatric lung health, indoor hacks' },
  { id: 'daily_commuter', label: '🚴 Daily Commuter', desc: 'Off-peak transit shifts, N95 routing, traffic corridors' },
  { id: 'elderly_caregiver', label: '🧓 Elderly & Vulnerable', desc: 'Cardiopulmonary care, indoor air sealing, medication safety' },
  { id: 'outdoor_enthusiast', label: '🏃 Outdoor Athlete', desc: 'Diurnal workout windows (1-4 PM), PM2.5 tracking' },
  { id: 'remote_worker', label: '🏡 Work from Home', desc: 'Diurnal ventilation, DIY Corsi-Rosenthal filtration' },
  { id: 'community_leader', label: '🏘️ Community Action', desc: 'Neighborhood carpools, reporting waste burning, clean heating' },
];

function Assistant() {
  useDocumentTitle('AI Health Assistant — Urban Air Quality Assistant');

  const { selectedCityData, selectedCityId } = useLocation();
  const [selectedLifestyle, setSelectedLifestyle] = useState<string>('family_with_children');

  // Thermal inversion window: 05:00–08:30 IST = 23:30–03:00 UTC
  const isInversionWindow = useMemo(() => {
    const now = new Date();
    const utcH = now.getUTCHours();
    const utcM = now.getUTCMinutes();
    const mins = utcH * 60 + utcM;
    return mins >= 23 * 60 + 30 || mins <= 3 * 60; // 23:30–03:00 UTC
  }, []);
  const [isTyping, setIsTyping] = useState(false);
  const [isClearModalOpen, setIsClearModalOpen] = useState(false);
  const [activeMobileTab, setActiveMobileTab] = useState<'chat' | 'health'>('chat');

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const prevCityIdRef = useRef<string>(selectedCityId);

  // Helper to construct initial welcome message
  const createWelcomeMessage = useCallback(
    (): ChatMessage => ({
      id: 'welcome-msg',
      sender: 'assistant',
      text:
        `Hello! I am your **Urban Air Quality Health Assistant**.\n\n` +
        `I am currently monitoring atmospheric criteria pollutants for **${selectedCityData.location.city}, ${selectedCityData.location.state}** (AQI **${selectedCityData.aqi} — ${selectedCityData.category}**).\n\n` +
        `Ask me anything about today's air quality, outdoor exercise safety, particulate health risks, masks, or precautions for sensitive groups. You can also pick from the suggested questions below!`,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      cityContext: {
        city: selectedCityData.location.city,
        aqi: selectedCityData.aqi,
        category: selectedCityData.category,
      },
      provenance: 'offline_rules',
      explainability: {
        priority: 'Baseline Advisory',
        targetGroup: 'General public & sensitive cohorts',
        reason: 'Initial atmospheric baseline telemetry loaded for active metropolitan area.',
        supportingSource: 'CPCB National Air Quality Index (NAQI) Standards',
      },
    }),
    [selectedCityData]
  );

  // Messages state with localStorage persistence
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY_CHAT);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (Array.isArray(parsed) && parsed.length > 0) return parsed;
      }
    } catch {
      // storage unavailable
    }
    return [createWelcomeMessage()];
  });

  // Persist messages
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY_CHAT, JSON.stringify(messages));
    } catch {
      // storage error
    }
  }, [messages]);

  // Notice when the active city changes elsewhere in the application
  useEffect(() => {
    if (prevCityIdRef.current !== selectedCityId) {
      prevCityIdRef.current = selectedCityId;
      const systemNotice: ChatMessage = {
        id: `sys-${Date.now()}`,
        sender: 'system',
        text: `Active location context updated to ${selectedCityData.location.city} (AQI ${selectedCityData.aqi} • ${selectedCityData.category})`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, systemNotice]);
    }
  }, [selectedCityId, selectedCityData]);

  // Scroll to bottom when messages update or typing starts
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  // Handle sending a message with Backend Gemini API integration + graceful fallback
  const handleSendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || isTyping) return;

      const userMsg: ChatMessage = {
        id: `user-${Date.now()}`,
        sender: 'user',
        text: trimmed,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, userMsg]);
      setIsTyping(true);

      try {
        // Build conversation history for FastAPI Gemini endpoint
        const conversationHistory = messages
          .filter((m) => m.sender === 'user' || m.sender === 'assistant')
          .slice(-6)
          .map((m) => ({
            role: m.sender as 'user' | 'assistant',
            content: m.text,
          }));

        const currentPersona = LIFESTYLE_PERSONAS.find((p) => p.id === selectedLifestyle);

        const response = await healthApi.askAssistant({
          city: selectedCityData.location.city,
          question: trimmed,
          lifestyle: selectedLifestyle,
          family_context: currentPersona?.desc,
          conversation_history: conversationHistory,
        });

        let responseText = response.answer;
        if (response.recommendations && response.recommendations.length > 0) {
          responseText +=
            '\n\n**Actionable Recommendations:**\n' +
            response.recommendations.map((r) => `• **${r.title}**: ${r.description}`).join('\n');
        }
        if (response.direct_impact_metrics && response.direct_impact_metrics.length > 0) {
          responseText +=
            '\n\n**Quantified Direct Impacts:**\n' +
            response.direct_impact_metrics.slice(0, 3).map((m) => `• 📊 ${m}`).join('\n');
        }
        if (response.disclaimer) {
          responseText += `\n\n*${response.disclaimer}*`;
        }

        const assistantMsg: ChatMessage = {
          id: `asst-${Date.now()}`,
          sender: 'assistant',
          text: responseText,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          cityContext: {
            city: selectedCityData.location.city,
            aqi: selectedCityData.aqi,
            category: selectedCityData.category,
          },
          provenance: 'gemini',
          explainability: {
            priority:
              selectedCityData.aqi > 200
                ? 'Critical Health Alert'
                : selectedCityData.aqi > 100
                ? 'Elevated Precaution'
                : 'Standard Health Advisory',
            targetGroup:
              'Families, pediatric cohorts, elderly, asthmatics, and active outdoor commuters',
            reason:
              'Assessed using generative AI grounded in CPCB NAQI guidelines and real-time station metrics.',
            supportingSource: 'Google Gemini AI + CPCB National Standards + WHO Guidelines (2021)',
          },
        };

        setMessages((prev) => [...prev, assistantMsg]);
      } catch {
        // Graceful fallback to built-in rule engine if backend is offline or errors
        const responseText = generateAssistantResponse(trimmed, selectedCityData);
        const assistantMsg: ChatMessage = {
          id: `asst-${Date.now()}`,
          sender: 'assistant',
          text: responseText,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          cityContext: {
            city: selectedCityData.location.city,
            aqi: selectedCityData.aqi,
            category: selectedCityData.category,
          },
          provenance: 'offline_rules',
          explainability: {
            priority:
              selectedCityData.aqi > 150 ? 'High Priority Alert' : 'Standard Precaution',
            targetGroup:
              'Local residents, sensitive individuals (asthma/COPD), and children',
            reason:
              'Generated via local deterministic rule engine using simulated and local atmospheric telemetry.',
            supportingSource: 'CPCB National Air Quality Index Breakpoints & WHO Ambient Standards',
          },
        };

        setMessages((prev) => [...prev, assistantMsg]);
      } finally {
        setIsTyping(false);
      }
    },
    [isTyping, messages, selectedCityData, selectedLifestyle]
  );

  // Clear conversation history
  const handleConfirmClear = () => {
    const freshWelcome = createWelcomeMessage();
    setMessages([freshWelcome]);
    try {
      localStorage.removeItem(STORAGE_KEY_CHAT);
    } catch {
      // storage error
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-12 animate-in fade-in duration-300">
      {/* 1. Page Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-slate-200/80 dark:border-slate-800 pb-5">
        <div className="space-y-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="p-2 rounded-xl bg-teal-50 text-teal-700 dark:bg-teal-950/60 dark:text-teal-400 border border-teal-200/60 dark:border-teal-800/60">
              <Bot className="w-5 h-5" aria-hidden="true" />
            </span>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 dark:text-white tracking-tight">
              AI Environmental Health Assistant
            </h1>
            <DataProvenanceBadge />
          </div>
          <p className="text-sm text-slate-600 dark:text-slate-400 max-w-3xl">
            Context-aware environmental health consultation powered by Google Gemini and CPCB guidelines. Receive immediate guidance on outdoor exertion, particulate exposure thresholds, protective measures, and sensitive group precautions tailored to your active city.
          </p>
        </div>

        {/* Thermal Inversion Peak Window Banner — 05:00–08:30 IST */}
      {isInversionWindow && (
        <div
          role="alert"
          aria-live="polite"
          className="flex items-start gap-3 px-4 py-3 rounded-xl bg-amber-50 border border-amber-300 dark:bg-amber-950/40 dark:border-amber-700 text-amber-900 dark:text-amber-200 text-sm"
        >
          <AlertTriangle className="w-5 h-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" aria-hidden="true" />
          <div>
            <strong>Peak Thermal Inversion Window (05:00–08:30 IST)</strong>
            <span className="ml-1">— Cold air traps pollutants near ground level during these hours. Avoid outdoor exertion; keep windows closed.</span>
          </div>
        </div>
      )}

      {/* Mobile View Switcher (Chat vs Health Context) */}
        <div className="inline-flex lg:hidden p-1 rounded-xl bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs font-semibold self-start">
          <button
            type="button"
            onClick={() => setActiveMobileTab('chat')}
            className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer flex items-center gap-1.5 ${
              activeMobileTab === 'chat'
                ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-xs'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <MessageSquare className="w-3.5 h-3.5" />
            <span>Chat Session</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveMobileTab('health')}
            className={`px-3 py-1.5 rounded-lg transition-all cursor-pointer flex items-center gap-1.5 ${
              activeMobileTab === 'health'
                ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white shadow-xs'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Health Insights</span>
          </button>
        </div>
      </div>

      {/* 2. Main 2-Column Responsive Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Chat Conversation Window (8 cols) */}
        <div
          className={`lg:col-span-8 space-y-4 ${
            activeMobileTab === 'health' ? 'hidden lg:block' : 'block'
          }`}
        >
          {/* Assistant Profile Header */}
          <AssistantProfileHeader
            cityData={selectedCityData}
            messageCount={messages.length}
            onClearChat={() => setIsClearModalOpen(true)}
          />

          {/* Lifestyle & Household Context Selector (Challenge 6 Pillar) */}
          <div className="p-3 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                <span>🎯 Tailor Advisory to Your Lifestyle & Household:</span>
              </span>
              <span className="text-2xs text-teal-600 dark:text-teal-400 font-medium">
                Active: {LIFESTYLE_PERSONAS.find((p) => p.id === selectedLifestyle)?.label}
              </span>
            </div>
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 no-scrollbar">
              {LIFESTYLE_PERSONAS.map((persona) => {
                const isActive = selectedLifestyle === persona.id;
                return (
                  <button
                    key={persona.id}
                    type="button"
                    onClick={() => setSelectedLifestyle(persona.id)}
                    aria-pressed={isActive}
                    className={`px-2.5 py-1 rounded-xl text-xs font-semibold whitespace-nowrap transition-all cursor-pointer flex items-center gap-1 ${
                      isActive
                        ? 'bg-teal-600 text-white shadow-xs dark:bg-teal-500'
                        : 'bg-slate-100 hover:bg-slate-200 text-slate-700 dark:bg-slate-800 dark:hover:bg-slate-700 dark:text-slate-300'
                    }`}
                  >
                    <span>{persona.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Chat Messages Container */}
          <div
            tabIndex={0}
            role="log"
            aria-live="polite"
            aria-label="Conversation with Air Quality Assistant"
            aria-relevant="additions"
            className="p-4 sm:p-5 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200/80 dark:border-slate-800 shadow-xs min-h-[460px] max-h-[580px] overflow-y-auto space-y-4 focus:outline-hidden focus:ring-2 focus:ring-teal-500/20"
          >
            {messages.map((message) => (
              <ChatMessageBubble key={message.id} message={message} />
            ))}

            {isTyping && <TypingIndicator />}
            <div ref={messagesEndRef} />
          </div>

          {/* Suggested Quick Questions */}
          <ChatSuggestedQuestions
            questions={SUGGESTED_QUESTIONS}
            onSelectQuestion={handleSendMessage}
            disabled={isTyping}
          />

          {/* User Input Bar */}
          <ChatInput onSendMessage={handleSendMessage} disabled={isTyping} />
        </div>

        {/* Right Column: Health Context Panel (4 cols) */}
        <div
          className={`lg:col-span-4 ${
            activeMobileTab === 'chat' ? 'hidden lg:block' : 'block'
          }`}
        >
          <AssistantContextPanel cityData={selectedCityData} />
        </div>
      </div>

      {/* Clear Chat Confirmation Modal */}
      <ClearChatModal
        isOpen={isClearModalOpen}
        onClose={() => setIsClearModalOpen(false)}
        onConfirm={handleConfirmClear}
      />
    </div>
  );
}

export { Assistant, Assistant as AssistantPage };
export default Assistant;
